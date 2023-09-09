from django.shortcuts import render

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from core.serializers import UserSerializer, CurrencySerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from core.models import Currency, UserBalance, TreasuryBalance, Exchange
from django.db import transaction
from django.conf import settings
import math


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows currencies to be viewed or edited.
    """

    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]


class Ok(APIView):
    def get(self, request):
        return Response("OK")


class Buy(APIView):
    def get(self, request):
        return Response("OK bye!")

    def post(self, request):
        print(request.user.email)
        # TODO: SERIALIZER? MAKE REWQUIRED?
        requested_symbol = request.data["symbol"]
        requested_amount = request.data["amount"]

        # DRF handles 404 errors
        requested_currency = Currency.objects.get(ticker_symbol=requested_symbol)
        base_currency = Currency.objects.get(
            ticker_symbol=settings.BASE_CURRENCY_SYMBOL
        )
        user_base_balance, _ = UserBalance.objects.get_or_create(
            user=request.user, currency=base_currency
        )

        required_funds = requested_currency.dollar_value * requested_amount

        if required_funds > user_base_balance.in_dollars():
            return Response(status=403, data="Insuficient Funds!")
        else:
            with transaction.atomic():
                order_total = required_funds / base_currency.dollar_value
                # charge user the dollar amount
                user_base_balance.amount -= order_total
                # give user usdt to the treasury
                treasury_base_currency, _ = TreasuryBalance.objects.get_or_create(
                    currency=base_currency
                )
                treasury_base_currency.amount += order_total
                # give user the required token amount
                requested_user_balance, created = UserBalance.objects.get_or_create(
                    currency=requested_currency, user=request.user
                )
                if created:
                    requested_user_balance.amount = requested_amount
                else:
                    requested_user_balance.amount += requested_amount

                (
                    treasury_purchased_token,
                    created,
                ) = TreasuryBalance.objects.get_or_create(currency=requested_currency)

                treasury_purchased_token.amount -= requested_amount

                requested_user_balance.save()
                user_base_balance.save()
                treasury_base_currency.save()
                treasury_purchased_token.save()
            if (
                treasury_purchased_token.in_dollars()
                <= -1 * settings.TREASURY_DEBT_THRESHOLD
            ):
                e = Exchange.objects.get()
                amount_to_buy = math.ceil(
                    abs(treasury_purchased_token.in_dollars())
                    / requested_currency.dollar_value
                )
                e.buy_from_exchange(amount=amount_to_buy, symbol=requested_symbol)

        return Response(f"OK POST! {request.data}", status=200)

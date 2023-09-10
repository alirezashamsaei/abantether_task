from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Currency, Exchange, UserBalance
from core.serializers import (
    CurrencyExchangeSerializer,
    CurrencySerializer,
    UserSerializer,
)
from core.utils import PurchaceHandler


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


class Buy(viewsets.ViewSet):
    serializer_class = CurrencyExchangeSerializer

    def list(self, request):
        data = {"message": "Buy a currency using USD."}
        return Response(data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            requested_symbol = validated_data.get("symbol")
            requested_amount = validated_data.get("amount")
            # DRF handles 404 errors
            requested_currency = Currency.objects.get(ticker_symbol=requested_symbol)
            base_currency = Currency.objects.get(
                ticker_symbol=settings.BASE_CURRENCY_SYMBOL
            )
            user_base_balance, _ = UserBalance.objects.get_or_create(
                user=request.user, currency=base_currency
            )

            required_funds = requested_currency.dollar_value * requested_amount

            if required_funds > user_base_balance.in_dollars:
                return Response(
                    {"error": "Insufficient Funds!"}, status=status.HTTP_403_FORBIDDEN
                )

            else:
                try:
                    exchange = Exchange.objects.get()
                    handler = PurchaceHandler(
                        request.user, requested_symbol, requested_amount, exchange
                    )
                    handler.execute()
                except Exception as e:
                    print(e)
                    return Response(
                        "Error!", status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            return Response("OK.", status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

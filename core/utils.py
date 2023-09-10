from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
from core.models import Currency, UserBalance, TreasuryBalance, Exchange
from rest_framework import status
from django.conf import settings
import math

User = get_user_model()


class PurchaceHandler:
    """makes purchases for users"""

    def __init__(self, user: User, symbol: str, amount: Decimal, exchange: Exchange):
        self.user = user
        self.symbol = symbol
        self.amount = amount
        self.exchange = exchange

    def execute(self) -> None:
        try:
            with transaction.atomic():
                requested_currency = Currency.objects.get(ticker_symbol=self.symbol)
                base_currency = Currency.objects.get(
                    ticker_symbol=settings.BASE_CURRENCY_SYMBOL
                )
                user_base_balance, _ = UserBalance.objects.get_or_create(
                    user=self.user, currency=base_currency
                )

                required_funds = Decimal(requested_currency.dollar_value) * Decimal(
                    self.amount
                )

                if required_funds > user_base_balance.in_dollars:
                    return {"error": "Insufficient Funds!"}, status.HTTP_403_FORBIDDEN

                total_amount = required_funds / base_currency.dollar_value

                requested_currency_handler = TransferHandler(
                    user=self.user, currency=requested_currency
                )
                base_currency_handler = TransferHandler(
                    user=self.user, currency=base_currency
                )

                base_currency_handler.transfer_from_user_to_treasury(total_amount)
                requested_currency_handler.transfer_from_treasury_to_user(self.amount)

            treasury_handler = TreasuryPurchaceHandler(currency=requested_currency)
            treasury_handler.purchase_if_necessary(exchange=self.exchange)

            return {"message": "Purchase successful."}, status.HTTP_201_CREATED

        except Currency.DoesNotExist:
            return {"error": "Currency not found."}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log the exception for debugging purposes
            print(f"Error: {str(e)}")
            return {
                "error": "An error occurred."
            }, status.HTTP_500_INTERNAL_SERVER_ERROR


class TreasuryPurchaceHandler:
    """Purchases a currency if balance is below threshold."""
    def __init__(self, currency: Currency) -> None:
        self.currency = currency
        self.treasury_balance, _ = TreasuryBalance.objects.get_or_create(
            currency=self.currency
        )

    def purchase_if_necessary(self, exchange: Exchange):
        if self.treasury_balance.in_dollars <= -1 * settings.TREASURY_DEBT_THRESHOLD:
            amount_to_buy = math.ceil(
                abs(self.treasury_balance.in_dollars)
                / self.treasury_balance.currency.dollar_value
            )
            exchange.buy_from_exchange(
                amount=amount_to_buy, symbol=self.currency.ticker_symbol
            )

class TransferHandler:
    """Responsible for transfering a currency between treasury and user balance"""

    def __init__(self, user: User, currency: Currency) -> None:
        self.user = user
        self.treasury_balance, _ = TreasuryBalance.objects.get_or_create(
            currency=currency
        )
        self.user_balance, _ = UserBalance.objects.get_or_create(
            currency=currency, user=self.user
        )

    def transfer_from_treasury_to_user(self, amount: Decimal):
        try:
            with transaction.atomic():
                self.treasury_balance.decrease_amount(amount=amount)
                self.user_balance.increase_amount(amount=amount)
        except Exception as e:
            print(e)  # Not so clean...

    def transfer_from_user_to_treasury(self, amount: Decimal):
        if self.user_balance.amount < amount:
            raise ValueError("Insufficient funds in user balance.")

        try:
            with transaction.atomic():
                self.treasury_balance.increase_amount(amount=amount)
                self.user_balance.decrease_amount(amount=amount)
        except Exception as e:
            print(e)  # Not so clean...

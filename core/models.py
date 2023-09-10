from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal

User = get_user_model()


class Currency(models.Model):
    """A tradable currency, eg. USDT"""

    display_name = models.CharField(max_length=50)
    ticker_symbol = models.CharField(max_length=6, unique=True)
    dollar_value = models.DecimalField("Dollar Value", decimal_places=4, max_digits=12)

    class Meta:
        verbose_name_plural = "currencies"

    def __str__(self) -> str:
        return self.ticker_symbol


class Balance(models.Model):
    currency = models.ForeignKey(to=Currency, on_delete=models.PROTECT)
    amount = models.DecimalField(
        "Currency Amount", default=0, decimal_places=4, max_digits=12
    )

    class Meta:
        abstract = True

    @property
    def in_dollars(self):
        return self.currency.dollar_value * self.amount

    def increase_amount(self, amount):
        self.amount += amount
        self.save()

    def decrease_amount(self, amount):
        self.amount -= amount
        self.save()

    def update_amount(self, amount):
        self.amount = amount
        self.save()


class UserBalance(Balance):
    """Each User Can have some amount of each currency."""

    user = models.ForeignKey(to=User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.username} | {self.currency.ticker_symbol} | ({self.amount})"


class TreasuryBalance(Balance):
    """How much of each currency do we have in the treasury."""

    def __str__(self) -> str:
        return f"{self.currency.ticker_symbol} | {self.amount}"


class Exchange(models.Model):
    "Foreign exchange we can call to exchange currencies."
    title = models.CharField("Exchange Name", max_length=50)

    def __str__(self) -> str:
        return self.title

    def buy_from_exchange(self, amount: Decimal, symbol: str) -> bool:
        """Adds the requested amount of currency to the treasury."""

        # Throws an error if currency does notz
        currency = Currency.objects.get(ticker_symbol=symbol)

        if Decimal(currency.dollar_value * amount) < Decimal(
            settings.MINIMUM_ORDER_USD_VALUE
        ):
            raise ValueError(
                f"Dollar amount should be at least {settings.MINIMUM_ORDER_USD_VALUE}"
            )
        else:
            treasury_balance, created = TreasuryBalance.objects.get_or_create(
                currency=currency
            )
            if created:
                treasury_balance.amount = amount
            else:
                treasury_balance.amount += amount
            treasury_balance.save()

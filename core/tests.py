from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status

from core.utils import PurchaceHandler

from .models import Currency, Exchange, TreasuryBalance, UserBalance

User = get_user_model()


class CurrencyModelTestCase(TestCase):
    def setUp(self):
        # Create a sample currency with ticker symbol "BTC"
        self.currency = Currency.objects.create(
            display_name="Bitcoin",
            ticker_symbol="BTC",  # Updated ticker symbol to "BTC"
            dollar_value=50000.0,
        )

    def test_currency_creation(self):
        """Test if a currency instance is created correctly."""
        self.assertEqual(self.currency.display_name, "Bitcoin")
        self.assertEqual(self.currency.ticker_symbol, "BTC")
        self.assertEqual(self.currency.dollar_value, 50000.0)

    def test_currency_unique_ticker_symbol(self):
        """Test that ticker symbols are unique."""
        # Attempt to create another currency with the same ticker symbol
        with self.assertRaises(Exception):
            Currency.objects.create(
                display_name="Bitcoin 2",
                ticker_symbol="BTC",  # Duplicate ticker symbol
                dollar_value=50000.10,
            )


class ExchangeModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")

        # Create a test currency
        self.currency = Currency.objects.create(
            display_name="Test Currency",
            ticker_symbol="TEST",
            dollar_value=Decimal("2.0"),  # Set a dollar value for the currency
        )

    def test_buy_from_exchange_success(self):
        # Create an exchange
        exchange = Exchange.objects.create(title="Test Exchange")

        # Call the buy_from_exchange method
        amount = Decimal("100.0")
        symbol = "TEST"
        exchange.buy_from_exchange(amount, symbol)

        # Check if the TreasuryBalance for the currency was created and updated correctly
        treasury_balance = TreasuryBalance.objects.get(currency=self.currency)
        self.assertEqual(treasury_balance.amount, amount)

    def test_buy_from_exchange_insufficient_funds(self):
        # Create an exchange
        exchange = Exchange.objects.create(title="Test Exchange")

        # Call the buy_from_exchange method with an insufficient amount
        amount = Decimal("4.5")  # Dollar Value for TEST curency is 2
        symbol = "TEST"

        # Check if a ValueError is raised with the appropriate message
        with self.assertRaises(ValueError) as context:
            exchange.buy_from_exchange(amount, symbol)

        self.assertEqual(
            str(context.exception),
            f"Dollar amount should be at least {settings.MINIMUM_ORDER_USD_VALUE}",
        )

    def test_buy_from_exchange_existing_treasury_balance(self):
        # Create an exchange
        exchange = Exchange.objects.create(title="Test Exchange")

        # Create an existing TreasuryBalance for the currency
        TreasuryBalance.objects.create(currency=self.currency, amount=Decimal("50.0"))

        # Call the buy_from_exchange method to update the existing balance
        amount = Decimal("100.0")
        symbol = "TEST"
        exchange.buy_from_exchange(amount, symbol)

        # Check if the existing TreasuryBalance was updated correctly
        updated_balance = TreasuryBalance.objects.get(currency=self.currency)
        self.assertEqual(updated_balance.amount, Decimal("150.0"))

    def test_buy_from_exchange_currency_not_existing(self):
        # Define the parameters for a new currency
        amount = Decimal("100.0")
        symbol = "NEWCUR"
        exchange = Exchange.objects.create(title="Test Exchange")

        with self.assertRaises(Currency.DoesNotExist):
            exchange.buy_from_exchange(amount, symbol)


class TreasuryBalanceTestCase(TestCase):
    def setUp(self):
        # Create a sample currency for testing
        self.currency = Currency.objects.create(
            display_name="Test Currency",
            ticker_symbol="TEST",
            dollar_value=Decimal("1.0"),
        )

    def test_treasury_balance_creation(self):
        """
        Test that a TreasuryBalance object can be created.
        """
        treasury_balance = TreasuryBalance.objects.create(
            currency=self.currency, amount=Decimal("1000.0")
        )
        self.assertIsInstance(treasury_balance, TreasuryBalance)
        self.assertEqual(treasury_balance.currency, self.currency)
        self.assertEqual(treasury_balance.amount, Decimal("1000.0"))

    def test_treasury_balance_update(self):
        """
        Test updating the amount in a TreasuryBalance object.
        """
        initial_amount = Decimal("100.0")
        treasury_balance = TreasuryBalance.objects.create(
            currency=self.currency, amount=initial_amount
        )

        # Update the amount
        new_amount = Decimal("200.0")
        treasury_balance.amount = new_amount
        treasury_balance.save()

        updated_treasury_balance = TreasuryBalance.objects.get(currency=self.currency)
        self.assertEqual(updated_treasury_balance.amount, new_amount)


class UserBalanceTestCase(TestCase):
    def setUp(self):
        # Create a sample user for testing
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create a sample currency for testing
        self.currency = Currency.objects.create(
            display_name="Test Currency",
            ticker_symbol="TEST",
            dollar_value=Decimal("1.0"),
        )

    def test_user_balance_creation(self):
        """
        Test that a UserBalance object can be created.
        """
        user_balance = UserBalance.objects.create(
            user=self.user, currency=self.currency, amount=Decimal("100.0")
        )
        self.assertIsInstance(user_balance, UserBalance)
        self.assertEqual(user_balance.user, self.user)
        self.assertEqual(user_balance.currency, self.currency)
        self.assertEqual(user_balance.amount, Decimal("100.0"))

    def test_user_balance_update(self):
        """
        Test updating the amount in a UserBalance object.
        """
        initial_amount = Decimal("100.0")
        user_balance = UserBalance.objects.create(
            user=self.user, currency=self.currency, amount=initial_amount
        )

        # Update the amount
        new_amount = Decimal("200.0")
        user_balance.amount = new_amount
        user_balance.save()

        updated_user_balance = UserBalance.objects.get(
            user=self.user, currency=self.currency
        )
        self.assertEqual(updated_user_balance.amount, new_amount)


class PurchaseHandlerTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Create a base currency (e.g., USD)
        self.base_currency = Currency.objects.create(
            display_name="US Dollar",
            ticker_symbol="USD",
            dollar_value=1.0,  # Assume 1 USD = 1 USD
        )

        # Create a currency to be purchased (e.g., BTC)
        self.currency_to_purchase = Currency.objects.create(
            display_name="Bitcoin",
            ticker_symbol="BTC",
            dollar_value=25000.0,  # Assume 1 BTC = 25000 USD
        )

        # Set the user's initial balance in USD
        self.user_base_balance = UserBalance.objects.create(
            user=self.user,
            currency=self.base_currency,
            amount=100000.0,  # Start with 100,000 USD
        )
        self.exchange = Exchange.objects.create(title="Binance")

    def test_successful_purchase_big_amount(self):
        # Simulate a valid purchase request
        handler = PurchaceHandler(self.user, "BTC", 2, self.exchange)
        response, response_status = handler.execute()
        self.assertEqual(response_status, status.HTTP_201_CREATED)
        self.assertEqual(response, {"message": "Purchase successful."})

        # Check if the user's balance in BTC has increased
        user_balance_in_btc = UserBalance.objects.get(
            user=self.user, currency=self.currency_to_purchase
        )
        self.assertAlmostEqual(user_balance_in_btc.amount, Decimal(2), places=4)

        # Check if the user's balance in USD has decreased
        user_balance_in_usd = UserBalance.objects.get(
            user=self.user, currency=self.base_currency
        )
        self.assertAlmostEqual(user_balance_in_usd.amount, Decimal(50000.0), places=4)

        # Check if the treasury balance for USD has increased
        treasury_balance_in_usd = TreasuryBalance.objects.get(
            currency=self.base_currency
        )
        self.assertAlmostEqual(
            treasury_balance_in_usd.amount,
            Decimal(
                50000.0,
            ),
            places=4,
        )

        # Check if the treasury balance for BTC has decreased
        treasury_balance_in_btc = TreasuryBalance.objects.get(
            currency=self.currency_to_purchase
        )
        self.assertAlmostEqual(treasury_balance_in_btc.amount, Decimal(0), places=4)

    def test_successful_purchase_small_amount(self):
        initial_user_base_balance, _ = UserBalance.objects.get_or_create(
            user=self.user, currency=self.base_currency
        )
        initial_user_btc_balance, _ = UserBalance.objects.get_or_create(
            user=self.user, currency=self.currency_to_purchase
        )
        initial_treasury_balance_in_usd, _ = TreasuryBalance.objects.get_or_create(
            currency=self.base_currency
        )
        initial_treasury_balance_in_btc, _ = TreasuryBalance.objects.get_or_create(
            currency=self.currency_to_purchase
        )
        initial_treasury_balance_in_btc.amount = Decimal(0)
        initial_treasury_balance_in_btc.save()

        # Simulate a valid purchase request
        handler = PurchaceHandler(self.user, "BTC", Decimal(0.0001), self.exchange)
        response, response_status = handler.execute()
        
        self.assertEqual(response_status, status.HTTP_201_CREATED)
        self.assertEqual(response, {"message": "Purchase successful."})

        # Check if the user's balance in BTC has increased
        user_balance_in_btc = UserBalance.objects.get(
            user=self.user, currency=self.currency_to_purchase
        )
        self.assertAlmostEqual(
            user_balance_in_btc.amount,
            Decimal(initial_user_btc_balance.amount) + Decimal(0.0001),
            places=4,
        )

        # Check if the user's balance in USD has decreased
        user_balance_in_usd = UserBalance.objects.get(
            user=self.user, currency=self.base_currency
        )
        self.assertAlmostEqual(
            user_balance_in_usd.amount,
            Decimal(initial_user_base_balance.amount) - Decimal(2.5),
            places=4,
        )

        # Check if the treasury balance for USD has increased
        treasury_balance_in_usd = TreasuryBalance.objects.get(
            currency=self.base_currency
        )
        self.assertAlmostEqual(
            treasury_balance_in_usd.amount,
            Decimal(initial_treasury_balance_in_usd.amount) + Decimal(2.5),
            places=4,
        )

        # Check if the treasury balance for BTC has decreased
        treasury_balance_in_btc = TreasuryBalance.objects.get(
            currency=self.currency_to_purchase
        )
        self.assertAlmostEqual(
            treasury_balance_in_btc.amount,
            Decimal(initial_treasury_balance_in_btc.amount) - Decimal(0.0001),
            places=4,
        )

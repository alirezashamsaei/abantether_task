from django.contrib import admin
from core.models import UserBalance, TreasuryBalance, Currency, Exchange

admin.site.register(Exchange)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("ticker_symbol", "display_name", "dollar_value")


@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "currency", "amount")


@admin.register(TreasuryBalance)
class TreasuryBalanceAdmin(admin.ModelAdmin):
    list_display = ("currency", "amount")

from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import Currency
User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]

class CurrencySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Currency
        fields = ["url", "display_name", "ticker_symbol", "dollar_value"]

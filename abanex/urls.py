from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from core import views

router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"currencies", views.CurrencyViewSet)
router.register(r"buy", views.Buy, basename="buy")

urlpatterns = [
    path("admin/", admin.site.urls),
] + [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

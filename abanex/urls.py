from django.contrib import admin
from django.urls import path
from django.urls import include, path
from rest_framework import routers
from core import views

router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"currencies", views.CurrencyViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
] + [
    path("", include(router.urls)),
    path("ok", views.Ok.as_view()),
    path("buy/", views.Buy.as_view()),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

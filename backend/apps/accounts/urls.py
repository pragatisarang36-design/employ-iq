"""
URL patterns for accounts, authentication, and identity.
Conforming to API_SPECIFICATION.md.
"""

from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    RegisterView,
    UserMeView,
)

urlpatterns = [
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("me/", UserMeView.as_view(), name="user_me"),
]

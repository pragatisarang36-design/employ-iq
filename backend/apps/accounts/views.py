"""
Views for authentication, session management, and user identity.
Conforming to API_SPECIFICATION.md.
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserMeSerializer,
)
from .services import record_audit_event


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /auth/token/
    Obtains access and refresh JWT tokens. Public access.
    """

    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /auth/token/refresh/
    Rotates access token. Public access.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            record_audit_event(
                action="auth.token_refresh",
                actor=request.user if request.user.is_authenticated else None,
                object_type="Token",
                metadata={"status": "success"},
            )
        return response


class LogoutView(APIView):
    """
    POST /auth/logout/
    Blacklists the provided refresh token. Requires Bearer authentication.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(actor=request.user)
        return Response(
            {"status": "ok", "message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


class UserMeView(APIView):
    """
    GET /me/
    Returns the authenticated user's profile and institution scope.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """
    POST /auth/register/
    Registers a new account under a specified institution.
    """

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output_serializer = UserMeSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

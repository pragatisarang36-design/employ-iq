"""
Serializers for accounts, authentication, and tenancy.
Conforming to API_SPECIFICATION.md.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Institution, User, UserRole
from .services import record_audit_event


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ["id", "name", "slug", "is_active"]
        read_only_fields = ["id"]


class UserMeSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "institution",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "role", "institution", "created_at"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Enhanced TokenObtainPairSerializer that supports multi-tenant resolution
    via optional institution_slug and embeds role & institution_id claims.
    """

    institution_slug = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        email = attrs.get(self.username_field, "").strip().lower()
        password = attrs.get("password")
        institution_slug = attrs.get("institution_slug")

        user_query = User.objects.filter(email=email, is_active=True)

        if institution_slug:
            institution = Institution.objects.filter(slug=institution_slug.strip().lower(), is_active=True).first()
            if not institution:
                raise serializers.ValidationError({"institution_slug": "Institution not found or inactive."})
            user_query = user_query.filter(institution=institution)

        matching_users = list(user_query)
        if not matching_users:
            raise serializers.ValidationError({"detail": "No active account found with the given credentials."})

        # If multiple users exist with the same email across different institutions and no slug was supplied
        if len(matching_users) > 1 and not institution_slug:
            raise serializers.ValidationError(
                {"institution_slug": "Multiple accounts found with this email. Please specify your institution_slug."}
            )

        user = None
        for candidate in matching_users:
            if candidate.check_password(password):
                user = candidate
                break

        if user is None:
            raise serializers.ValidationError({"detail": "Invalid email or password."})

        self.user = user
        refresh = self.get_token(user)

        # Audit event on successful authentication
        record_audit_event(
            action="auth.login",
            actor=user,
            institution=user.institution,
            object_type="User",
            object_id=str(user.id),
            metadata={"email": user.email, "role": user.role},
        )

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims for rapid client & downstream service evaluation
        token["role"] = user.role
        token["email"] = user.email
        token["institution_id"] = str(user.institution_id) if user.institution_id else None
        return token


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        return value

    def save(self, **kwargs):
        actor = kwargs.get("actor")
        self.token.blacklist()
        record_audit_event(
            action="auth.logout",
            actor=actor,
            institution=actor.institution if actor else None,
            object_type="User",
            object_id=str(actor.id) if actor else "",
            metadata={"status": "blacklisted"},
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    institution_slug = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "institution_slug",
            "first_name",
            "last_name",
            "role",
        ]
        read_only_fields = ["id"]

    def validate_role(self, value):
        if value not in (UserRole.STUDENT, UserRole.TPO, UserRole.ADMIN):
            raise serializers.ValidationError("Invalid role choice.")
        return value

    def validate(self, attrs):
        institution_slug = attrs.get("institution_slug", "").strip().lower()
        institution = Institution.objects.filter(slug=institution_slug, is_active=True).first()
        if not institution:
            raise serializers.ValidationError({"institution_slug": "Institution not found or inactive."})

        email = attrs.get("email", "").strip().lower()
        if User.objects.filter(institution=institution, email=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists in this institution."})

        attrs["institution"] = institution
        attrs["email"] = email
        return attrs

    def create(self, validated_data):
        validated_data.pop("institution_slug", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user

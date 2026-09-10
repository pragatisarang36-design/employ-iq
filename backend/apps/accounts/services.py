"""
Business services for accounts and audit logging.
Views remain thin; writes and state transformations execute here.
"""

from typing import Any, Dict, Optional
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AuditEvent, Institution, User, UserRole


SENSITIVE_KEYS = {
    "password",
    "token",
    "refresh",
    "access",
    "secret",
    "authorization",
    "api_key",
}


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redacts sensitive keys from audit log metadata."""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                cleaned[key] = "[REDACTED]"
            else:
                cleaned[key] = redact_sensitive_data(value)
        return cleaned
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data


def record_audit_event(
    *,
    action: str,
    actor: Optional[User] = None,
    institution: Optional[Institution] = None,
    object_type: str = "",
    object_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """
    Persists an immutable audit log entry.
    Ensures institution boundary is maintained and sensitive payload data is redacted.
    """
    target_institution = institution
    if target_institution is None and actor and actor.institution:
        target_institution = actor.institution

    safe_metadata = redact_sensitive_data(metadata or {})

    return AuditEvent.objects.create(
        action=action,
        actor=actor,
        institution=target_institution,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        metadata=safe_metadata,
    )


def create_institution(
    *,
    name: str,
    slug: str,
    is_active: bool = True,
    actor: Optional[User] = None,
) -> Institution:
    institution = Institution.objects.create(
        name=name.strip(),
        slug=slug.strip().lower(),
        is_active=is_active,
    )
    record_audit_event(
        action="institution.created",
        actor=actor,
        institution=institution,
        object_type="Institution",
        object_id=str(institution.id),
        metadata={"name": institution.name, "slug": institution.slug},
    )
    return institution


def create_user(
    *,
    email: str,
    password: Optional[str] = None,
    institution: Optional[Institution] = None,
    role: str = UserRole.STUDENT,
    first_name: str = "",
    last_name: str = "",
    actor: Optional[User] = None,
) -> User:
    user = User.objects.create_user(
        email=email,
        password=password,
        institution=institution,
        role=role,
        first_name=first_name,
        last_name=last_name,
    )
    record_audit_event(
        action="user.created",
        actor=actor or user,
        institution=institution,
        object_type="User",
        object_id=str(user.id),
        metadata={"email": user.email, "role": user.role},
    )
    return user


def blacklist_refresh_token(
    *,
    refresh_token: str,
    actor: Optional[User] = None,
) -> None:
    token = RefreshToken(refresh_token)
    token.blacklist()

    record_audit_event(
        action="auth.logout",
        actor=actor,
        institution=actor.institution if actor else None,
        object_type="User",
        object_id=str(actor.id) if actor else "",
        metadata={"detail": "Refresh token blacklisted"},
    )

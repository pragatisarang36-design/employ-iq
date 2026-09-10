"""
Read selectors for accounts and tenancy.
Views and external apps use selectors for structured data access.
"""

from typing import Optional
from django.db.models import QuerySet

from .models import AuditEvent, Institution, User


def get_institution_by_slug(slug: str) -> Optional[Institution]:
    return Institution.objects.filter(slug=slug.strip().lower(), is_active=True).first()


def get_user_by_id(user_id) -> Optional[User]:
    return User.objects.filter(id=user_id).select_related("institution").first()


def get_user_by_email_and_institution(
    email: str, institution: Optional[Institution] = None
) -> Optional[User]:
    qs = User.objects.filter(email=email.strip().lower())
    if institution is not None:
        qs = qs.filter(institution=institution)
    return qs.select_related("institution").first()


def list_users_for_institution(
    institution: Institution, role: Optional[str] = None
) -> QuerySet[User]:
    qs = User.objects.filter(institution=institution, is_active=True)
    if role:
        qs = qs.filter(role=role)
    return qs.order_by("email")


def get_audit_events_for_institution(
    institution: Institution, action: Optional[str] = None
) -> QuerySet[AuditEvent]:
    qs = AuditEvent.objects.filter(institution=institution)
    if action:
        qs = qs.filter(action=action)
    return qs.select_related("actor").order_by("-created_at")

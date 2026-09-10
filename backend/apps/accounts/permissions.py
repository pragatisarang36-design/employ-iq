"""
Role-Based Access Control (RBAC) and Tenancy isolation permissions.
Conforming to SYSTEM_ARCHITECTURE.md and API_SPECIFICATION.md.
"""

from rest_framework.permissions import BasePermission
from .models import UserRole


class IsStudent(BasePermission):
    """Allows access only to authenticated students."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role == UserRole.STUDENT
        )


class IsTPO(BasePermission):
    """Allows access only to authenticated Training and Placement Officers."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role == UserRole.TPO
        )


class IsAdmin(BasePermission):
    """Allows access to institution administrators or superusers."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (request.user.role == UserRole.ADMIN or request.user.is_superuser)
        )


class IsTPOOrAdmin(BasePermission):
    """Allows access to TPO or Institution Admin."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (
                request.user.role in (UserRole.TPO, UserRole.ADMIN)
                or request.user.is_superuser
            )
        )


class IsSameInstitution(BasePermission):
    """
    Object-level permission ensuring multi-tenant isolation.
    An actor can only inspect or modify records belonging to their own institution.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if not request.user.institution_id:
            return False

        # If the object itself is an Institution
        if hasattr(obj, "slug") and hasattr(obj, "is_active") and str(obj.__class__.__name__) == "Institution":
            return obj.id == request.user.institution_id

        # If object has institution_id
        if hasattr(obj, "institution_id"):
            return obj.institution_id == request.user.institution_id

        # If object has user relation with institution_id
        if hasattr(obj, "user") and hasattr(obj.user, "institution_id"):
            return obj.user.institution_id == request.user.institution_id

        return False


class IsSelfOrAuthorizedStaff(BasePermission):
    """
    Allows the student owner to access/modify their own object,
    or TPO/Admin of the same institution to inspect it.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Check self-ownership
        if hasattr(obj, "id") and obj.id == request.user.id:
            return True
        if hasattr(obj, "user_id") and obj.user_id == request.user.id:
            return True

        # If not self, check if actor is TPO or Admin in the same institution
        if request.user.role in (UserRole.TPO, UserRole.ADMIN):
            obj_inst_id = getattr(obj, "institution_id", None)
            if not obj_inst_id and hasattr(obj, "user"):
                obj_inst_id = getattr(obj.user, "institution_id", None)
            return bool(obj_inst_id and obj_inst_id == request.user.institution_id)

        return False

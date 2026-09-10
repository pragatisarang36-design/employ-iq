"""
Views for student profile and feature snapshot extraction.
Conforming to API_SPECIFICATION.md.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsSameInstitution, IsStudent, IsTPOOrAdmin
from apps.accounts.services import record_audit_event
from .selectors import get_student_profile_by_id, get_student_profile_by_user
from .serializers import (
    FeatureSnapshotSerializer,
    StudentProfileDetailSerializer,
    StudentProfileUpdateSerializer,
)
from .services import (
    build_feature_snapshot,
    get_or_create_student_profile,
    update_student_profile,
)


class StudentMeProfileView(APIView):
    """
    GET, PATCH /students/me/profile/
    Student only. Retrieve or update own academic and profile facts.
    """

    permission_classes = [IsStudent]

    def get(self, request, *args, **kwargs):
        profile = get_or_create_student_profile(request.user)
        # Re-fetch with prefetching
        profile = get_student_profile_by_user(request.user) or profile
        serializer = StudentProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        profile = get_or_create_student_profile(request.user)
        serializer = StudentProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_profile = update_student_profile(
            profile=profile,
            data=serializer.validated_data,
            actor=request.user,
        )
        output_serializer = StudentProfileDetailSerializer(updated_profile)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class StudentFeatureSnapshotView(APIView):
    """
    GET /students/me/feature-snapshot/
    Student only. Validated model-ready features with schema version.
    """

    permission_classes = [IsStudent]

    def get(self, request, *args, **kwargs):
        profile = get_or_create_student_profile(request.user)
        snapshot_data = build_feature_snapshot(profile)
        serializer = FeatureSnapshotSerializer(snapshot_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentDetailForStaffView(APIView):
    """
    GET /students/{student_id}/profile/
    TPO/Admin only, scoped to own institution.
    """

    permission_classes = [IsTPOOrAdmin, IsSameInstitution]

    def get(self, request, student_id, *args, **kwargs):
        # Filter by institution if not platform superuser
        institution_scope = None if request.user.is_superuser else request.user.institution
        profile = get_student_profile_by_id(student_id, institution=institution_scope)

        if not profile:
            # If student exists in another institution, deny with 403 / 404 to prevent tenant scanning
            return Response(
                {"code": "not_found", "message": "Student profile not found in your institution."},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.check_object_permissions(request, profile)

        record_audit_event(
            action="tpo.student_profile_viewed",
            actor=request.user,
            institution=profile.institution,
            object_type="StudentProfile",
            object_id=str(profile.id),
            metadata={"student_email": profile.user.email},
        )

        serializer = StudentProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

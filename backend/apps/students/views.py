"""
Views for student profile and feature snapshot extraction.
Conforming to API_SPECIFICATION.md.
"""

import csv
from io import TextIOWrapper

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsSameInstitution, IsStudent, IsTPOOrAdmin
from apps.accounts.services import record_audit_event
from .selectors import get_student_profile_by_id, get_student_profile_by_user
from .serializers import (
    FeatureSnapshotSerializer,
    SkillCreateSerializer,
    StudentCertificationSerializer,
    StudentExperienceSerializer,
    StudentProfileDetailSerializer,
    StudentSkillSerializer,
    StudentProfileUpdateSerializer,
)
from .services import (
    build_feature_snapshot,
    add_or_update_student_skill,
    add_student_certification,
    add_student_experience,
    get_or_create_student_profile,
    update_student_profile,
)
from .models import Skill


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


class StudentSkillListCreateView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        profile = get_or_create_student_profile(request.user)
        return Response(StudentSkillSerializer(profile.skills.select_related("skill"), many=True).data)

    def post(self, request):
        serializer = SkillCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = get_or_create_student_profile(request.user)
        student_skill = add_or_update_student_skill(profile=profile, **serializer.validated_data)
        return Response(StudentSkillSerializer(student_skill).data, status=status.HTTP_201_CREATED)


class StudentCertificationListCreateView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        profile = get_or_create_student_profile(request.user)
        return Response(StudentCertificationSerializer(profile.certifications.all(), many=True).data)

    def post(self, request):
        serializer = StudentCertificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        certification = add_student_certification(profile=get_or_create_student_profile(request.user), **serializer.validated_data)
        return Response(StudentCertificationSerializer(certification).data, status=status.HTTP_201_CREATED)


class StudentExperienceListCreateView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        profile = get_or_create_student_profile(request.user)
        return Response(StudentExperienceSerializer(profile.experiences.all(), many=True).data)

    def post(self, request):
        serializer = StudentExperienceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        experience = add_student_experience(profile=get_or_create_student_profile(request.user), **serializer.validated_data)
        return Response(StudentExperienceSerializer(experience).data, status=status.HTTP_201_CREATED)


class StudentProfileCsvImportView(APIView):
    """Small, ownership-safe CSV import for a student's own profile and skills."""
    permission_classes = [IsStudent]

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload or not upload.name.lower().endswith(".csv"):
            return Response({"code": "validation_error", "message": "Upload one CSV file."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rows = list(csv.DictReader(TextIOWrapper(upload.file, encoding="utf-8-sig")))
        except UnicodeDecodeError:
            return Response({"code": "validation_error", "message": "CSV must be UTF-8 encoded."}, status=status.HTTP_400_BAD_REQUEST)
        if len(rows) != 1:
            return Response({"code": "validation_error", "message": "Student import requires exactly one data row."}, status=status.HTTP_400_BAD_REQUEST)
        row = rows[0]
        allowed = StudentProfileUpdateSerializer.ALLOWED_FIELDS
        data = {key: value for key, value in row.items() if key in allowed and value not in (None, "")}
        serializer = StudentProfileUpdateSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = update_student_profile(profile=get_or_create_student_profile(request.user), data=serializer.validated_data, actor=request.user)
        imported_skills = []
        for canonical_key in filter(None, (item.strip().lower().replace(" ", "-") for item in row.get("skills", "").split(";"))):
            skill = Skill.objects.filter(canonical_key=canonical_key).first()
            if skill:
                add_or_update_student_skill(profile=profile, skill=skill)
                imported_skills.append(skill.name)
        return Response({"updated_profile_fields": list(serializer.validated_data), "imported_skills": imported_skills, "invalid_rows": 0})


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

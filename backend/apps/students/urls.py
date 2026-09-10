"""
URL routing for students app.
Conforming to API_SPECIFICATION.md.
"""

from django.urls import path
from .views import (
    StudentDetailForStaffView,
    StudentCertificationListCreateView,
    StudentExperienceListCreateView,
    StudentFeatureSnapshotView,
    StudentMeProfileView,
    StudentSkillListCreateView,
)

urlpatterns = [
    path("students/me/profile/", StudentMeProfileView.as_view(), name="student_me_profile"),
    path("students/me/feature-snapshot/", StudentFeatureSnapshotView.as_view(), name="student_feature_snapshot"),
    path("students/me/skills/", StudentSkillListCreateView.as_view(), name="student_skills"),
    path("students/me/certifications/", StudentCertificationListCreateView.as_view(), name="student_certifications"),
    path("students/me/experiences/", StudentExperienceListCreateView.as_view(), name="student_experiences"),
    path("students/<uuid:student_id>/profile/", StudentDetailForStaffView.as_view(), name="student_detail_staff"),
]

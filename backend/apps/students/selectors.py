"""
Selectors for students app.
Encapsulates read queries and prefetching for student profiles.
"""

from typing import Optional
from django.db.models import QuerySet

from .models import Skill, StudentProfile


def get_student_profile_by_user(user) -> Optional[StudentProfile]:
    return (
        StudentProfile.objects.filter(user=user)
        .select_related("user", "institution")
        .prefetch_related("skills__skill", "certifications", "experiences")
        .first()
    )


def get_student_profile_by_id(
    profile_id, institution=None
) -> Optional[StudentProfile]:
    qs = StudentProfile.objects.filter(id=profile_id).select_related("user", "institution")
    if institution is not None:
        qs = qs.filter(institution=institution)
    return (
        qs.prefetch_related("skills__skill", "certifications", "experiences")
        .first()
    )


def list_skills(category: Optional[str] = None) -> QuerySet[Skill]:
    qs = Skill.objects.all()
    if category:
        qs = qs.filter(category=category)
    return qs.order_by("name")

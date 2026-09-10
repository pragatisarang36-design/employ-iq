"""
Services for student profile, skills, experiences, and feature snapshot extraction.
Conforming to DEVELOPMENT_PLAN.md and ML_ARCHITECTURE.md.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from django.db import transaction

from apps.accounts.services import record_audit_event
from .models import (
    Skill,
    StudentCertification,
    StudentExperience,
    StudentProfile,
    StudentSkill,
)


FEATURE_SCHEMA_VERSION = "v1.0"


def get_or_create_student_profile(user) -> StudentProfile:
    """Retrieves or initializes a StudentProfile for the given user."""
    profile, created = StudentProfile.objects.get_or_create(
        user=user,
        defaults={"institution": user.institution},
    )
    if created:
        record_audit_event(
            action="student.profile_created",
            actor=user,
            institution=user.institution,
            object_type="StudentProfile",
            object_id=str(profile.id),
            metadata={"email": user.email, "institution": user.institution.slug if user.institution else None},
        )
    return profile


@transaction.atomic
def update_student_profile(
    *,
    profile: StudentProfile,
    data: Dict[str, Any],
    actor=None,
) -> StudentProfile:
    """Updates declared academic and profile fields, and records an audit log."""
    updatable_fields = [
        "cohort",
        "department",
        "cgpa",
        "tenth_percentage",
        "twelfth_percentage",
        "current_backlogs",
        "history_of_backlogs",
        "aptitude_score",
        "communication_rating",
        "extracurricular_score",
    ]

    changed = {}
    for field in updatable_fields:
        if field in data:
            val = data[field]
            setattr(profile, field, val)
            changed[field] = str(val) if isinstance(val, Decimal) else val

    profile.save()

    record_audit_event(
        action="student.profile_updated",
        actor=actor or profile.user,
        institution=profile.institution,
        object_type="StudentProfile",
        object_id=str(profile.id),
        metadata={"updated_fields": list(changed.keys()), "changes": changed},
    )
    return profile


def add_or_update_student_skill(
    *,
    profile: StudentProfile,
    skill: Skill,
    proficiency: str = StudentSkill.Proficiency.BEGINNER,
    source: str = StudentSkill.Source.SELF_REPORTED,
) -> StudentSkill:
    student_skill, _ = StudentSkill.objects.update_or_create(
        student=profile,
        skill=skill,
        defaults={"proficiency": proficiency, "source": source},
    )
    return student_skill


def add_student_certification(
    *,
    profile: StudentProfile,
    name: str,
    issuer: str,
    earned_at=None,
) -> StudentCertification:
    return StudentCertification.objects.create(
        student=profile,
        name=name.strip(),
        issuer=issuer.strip(),
        earned_at=earned_at,
    )


def add_student_experience(
    *,
    profile: StudentProfile,
    kind: str,
    title: str,
    complexity: str = StudentExperience.Complexity.MEDIUM,
    duration_months: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
) -> StudentExperience:
    return StudentExperience.objects.create(
        student=profile,
        kind=kind,
        title=title.strip(),
        complexity=complexity,
        duration_months=duration_months,
        metadata=metadata or {},
    )


def build_feature_snapshot(profile: StudentProfile) -> Dict[str, Any]:
    """
    Extracts validated model-ready features from profile, assessment, experience,
    and skill facts without applying internal ML scaling/transforms.
    Conforming to API_SPECIFICATION.md and ML_ARCHITECTURE.md.
    """
    skills_qs = profile.skills.all()
    technical_skills_count = skills_qs.count()
    verified_skills_count = skills_qs.filter(source=StudentSkill.Source.ASSESSMENT).count()

    experiences_qs = profile.experiences.all()
    projects_count = experiences_qs.filter(kind=StudentExperience.Kind.PROJECT).count()
    internships_count = experiences_qs.filter(kind=StudentExperience.Kind.INTERNSHIP).count()
    open_source_count = experiences_qs.filter(kind=StudentExperience.Kind.OPEN_SOURCE).count()

    # Get latest dimension scores from assessments if available
    latest_scores = {}
    from apps.assessments.selectors import get_latest_scores_for_student
    latest_assessment_scores = get_latest_scores_for_student(profile)
    for dim, score_obj in latest_assessment_scores.items():
        latest_scores[f"{dim}_score"] = float(score_obj.score)

    features = {
        "cgpa": float(profile.cgpa),
        "tenth_percentage": float(profile.tenth_percentage),
        "twelfth_percentage": float(profile.twelfth_percentage),
        "current_backlogs": profile.current_backlogs,
        "history_of_backlogs": profile.history_of_backlogs,
        "technical_skills_count": technical_skills_count,
        "verified_skills_count": verified_skills_count,
        "certifications_count": profile.certifications.count(),
        "projects_count": projects_count,
        "internships_count": internships_count,
        "open_source_contributions": open_source_count,
        "aptitude_score": float(profile.aptitude_score),
        "communication_rating": float(profile.communication_rating),
        "extracurricular_score": float(profile.extracurricular_score),
        "quantitative_score": latest_scores.get("quantitative_score", 0.0),
        "logical_score": latest_scores.get("logical_score", 0.0),
        "coding_score": latest_scores.get("coding_score", 0.0),
        "communication_score": latest_scores.get("communication_score", 0.0),
        "interview_score": latest_scores.get("interview_score", 0.0),
        "presentation_score": latest_scores.get("presentation_score", 0.0),
    }

    return {
        "student_id": str(profile.id),
        "user_id": str(profile.user.id),
        "institution_id": str(profile.institution_id),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "features": features,
    }

"""
Services for assessment processing and scoring.
Conforming to DATABASE_SCHEMA.md and API_SPECIFICATION.md.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.db import transaction

from apps.accounts.services import record_audit_event
from .models import Assessment, AssessmentScore


@transaction.atomic
def record_assessment(
    *,
    student,
    assessment_type: str = Assessment.Type.DIAGNOSTIC,
    scores_data: List[Dict[str, Any]],
    actor=None,
) -> Assessment:
    """
    Persists an assessment header along with dimensional scores atomically.
    Records an audit log entry.
    """
    assessment = Assessment.objects.create(
        student=student,
        type=assessment_type,
        status=Assessment.Status.COMPLETED,
    )

    created_scores = []
    for item in scores_data:
        dimension = item["dimension"]
        score_val = Decimal(str(item["score"]))
        max_score_val = Decimal(str(item.get("max_score", 100.0)))

        score_obj = AssessmentScore.objects.create(
            assessment=assessment,
            dimension=dimension,
            score=score_val,
            max_score=max_score_val,
        )
        created_scores.append(score_obj)

    record_audit_event(
        action="assessment.submitted",
        actor=actor or student.user,
        institution=student.institution,
        object_type="Assessment",
        object_id=str(assessment.id),
        metadata={
            "type": assessment.type,
            "dimensions": [s.dimension for s in created_scores],
            "scores": {s.dimension: float(s.score) for s in created_scores},
        },
    )

    return assessment

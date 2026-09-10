"""
Selectors for assessments app.
Encapsulates read queries and aggregations for assessments.
"""

from typing import Dict
from django.db.models import QuerySet

from .models import Assessment, AssessmentScore


def list_assessments_for_student(student) -> QuerySet[Assessment]:
    return (
        Assessment.objects.filter(student=student)
        .prefetch_related("scores")
        .order_by("-submitted_at")
    )


def get_latest_scores_for_student(student) -> Dict[str, AssessmentScore]:
    """
    Returns a dictionary of the most recently submitted score object for each dimension.
    """
    assessments = (
        Assessment.objects.filter(student=student)
        .prefetch_related("scores")
        .order_by("-submitted_at")
    )

    latest_scores = {}
    for assessment in assessments:
        for score in assessment.scores.all():
            if score.dimension not in latest_scores:
                latest_scores[score.dimension] = score
    return latest_scores

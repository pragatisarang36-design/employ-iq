"""
URL routing for assessments app.
Conforming to API_SPECIFICATION.md.
"""

from django.urls import path
from .views import AssessmentListCreateView

urlpatterns = [
    path("assessments/", AssessmentListCreateView.as_view(), name="assessment_list_create"),
]

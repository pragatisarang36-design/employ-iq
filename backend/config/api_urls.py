"""
API routing for EmployIQ.
Provides /api/v1 per API_SPECIFICATION.md and backward-compatible /api/ routes.
"""

from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok", "service": "employiq-api"})


api_v1_patterns = [
    path("health/", health_check, name="health-check-v1"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.students.urls")),
    path("", include("apps.assessments.urls")),
    path("", include("apps.predictions.urls")),
    path("", include("apps.careers.urls")),
    path("", include("apps.rag.urls")),
    path("", include("apps.roadmaps.urls")),
]

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("v1/", include((api_v1_patterns, "v1"))),
    path("", include("apps.accounts.urls")),
    path("", include("apps.students.urls")),
    path("", include("apps.assessments.urls")),
    path("", include("apps.predictions.urls")),
    path("", include("apps.careers.urls")),
    path("", include("apps.rag.urls")),
    path("", include("apps.roadmaps.urls")),
]

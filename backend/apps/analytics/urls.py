from django.urls import path
from .views import AnalyticsOverviewView, DepartmentReadinessView, InstitutionalSkillDeficitsView, InterventionListView, StudentDashboardView
urlpatterns = [path("analytics/overview/", AnalyticsOverviewView.as_view()), path("analytics/interventions/", InterventionListView.as_view()), path("analytics/departments/", DepartmentReadinessView.as_view()), path("analytics/skills/", InstitutionalSkillDeficitsView.as_view()), path("dashboard/", StudentDashboardView.as_view(), name="student-dashboard")]

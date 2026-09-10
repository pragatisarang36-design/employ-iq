from django.urls import path
from .views import AnalyticsOverviewView, InterventionListView
urlpatterns = [path("analytics/overview/", AnalyticsOverviewView.as_view()), path("analytics/interventions/", InterventionListView.as_view())]

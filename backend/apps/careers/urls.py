from django.urls import path

from .views import CareerRoleListView, GapAnalysisView, RoleAlignmentView, RoleSelectView

urlpatterns = [
    path("careers/roles/", CareerRoleListView.as_view(), name="career-role-list"),
    path("careers/roles/<slug:slug>/select/", RoleSelectView.as_view(), name="career-role-select"),
    path("careers/roles/<slug:slug>/gap-analysis/", GapAnalysisView.as_view(), name="career-gap-analysis"),
    path("careers/roles/<slug:slug>/alignment/", RoleAlignmentView.as_view(), name="career-role-alignment"),
]

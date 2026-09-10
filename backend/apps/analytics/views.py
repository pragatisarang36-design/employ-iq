from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsStudent, IsTPOOrAdmin
from apps.students.services import get_or_create_student_profile
from .selectors import interventions, overview, student_dashboard

class AnalyticsOverviewView(APIView):
    permission_classes = [IsTPOOrAdmin]
    def get(self, request): return Response(overview(request.user.institution))

class InterventionListView(APIView):
    permission_classes = [IsTPOOrAdmin]
    def get(self, request): return Response({"count": len(interventions(request.user.institution)), "results": interventions(request.user.institution)})


class StudentDashboardView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        return Response(student_dashboard(get_or_create_student_profile(request.user)))

from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsTPOOrAdmin
from .selectors import interventions, overview

class AnalyticsOverviewView(APIView):
    permission_classes = [IsTPOOrAdmin]
    def get(self, request): return Response(overview(request.user.institution))

class InterventionListView(APIView):
    permission_classes = [IsTPOOrAdmin]
    def get(self, request): return Response({"count": len(interventions(request.user.institution)), "results": interventions(request.user.institution)})

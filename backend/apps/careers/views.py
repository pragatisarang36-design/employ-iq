from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent
from apps.students.services import get_or_create_student_profile

from .models import CareerRole
from .serializers import CareerRoleSerializer, GapAnalysisSerializer
from .services import create_gap_analysis, role_alignment, select_role


class CareerRoleListView(APIView):
    def get(self, request):
        return Response(CareerRoleSerializer(CareerRole.objects.all(), many=True).data)


class RoleSelectView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, slug):
        role = CareerRole.objects.filter(slug=slug).first()
        if not role:
            return Response({"code": "not_found", "message": "Career role not found."}, status=status.HTTP_404_NOT_FOUND)
        select_role(student=get_or_create_student_profile(request.user), role=role)
        return Response(CareerRoleSerializer(role).data, status=status.HTTP_200_OK)


class GapAnalysisView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, slug):
        role = CareerRole.objects.filter(slug=slug).first()
        if not role:
            return Response({"code": "not_found", "message": "Career role not found."}, status=status.HTTP_404_NOT_FOUND)
        snapshot = create_gap_analysis(student=get_or_create_student_profile(request.user), role=role)
        return Response(GapAnalysisSerializer(snapshot).data)


class RoleAlignmentView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, slug):
        role = CareerRole.objects.filter(slug=slug).first()
        if not role:
            return Response({"code": "not_found", "message": "Career role not found."}, status=status.HTTP_404_NOT_FOUND)
        result = role_alignment(student=get_or_create_student_profile(request.user), role=role)
        return Response({"role": CareerRoleSerializer(role).data, **{key: value for key, value in result.items() if key != "role"}})

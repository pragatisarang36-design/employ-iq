from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent
from apps.careers.models import CareerRole
from apps.students.services import get_or_create_student_profile
from .models import Roadmap, RoadmapItem
from .serializers import RoadmapItemSerializer, RoadmapSerializer
from .services import generate_roadmap


class RoadmapCreateView(APIView):
    permission_classes = [IsStudent]
    def post(self, request):
        role = CareerRole.objects.filter(slug=request.data.get("role_slug")).first()
        if not role:
            return Response({"code": "validation_error", "message": "A valid role_slug is required."}, status=status.HTTP_400_BAD_REQUEST)
        roadmap = generate_roadmap(student=get_or_create_student_profile(request.user), role=role)
        return Response(RoadmapSerializer(roadmap).data, status=status.HTTP_201_CREATED)


class CurrentRoadmapView(APIView):
    permission_classes = [IsStudent]
    def get(self, request):
        roadmap = Roadmap.objects.filter(student=get_or_create_student_profile(request.user), status=Roadmap.Status.ACTIVE).select_related("role").prefetch_related("items__skill").first()
        if not roadmap:
            return Response({"code": "not_found", "message": "No active roadmap exists."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RoadmapSerializer(roadmap).data)


class RoadmapItemUpdateView(APIView):
    permission_classes = [IsStudent]
    def patch(self, request, roadmap_id, item_id):
        item = RoadmapItem.objects.filter(id=item_id, roadmap_id=roadmap_id, roadmap__student=get_or_create_student_profile(request.user)).first()
        if not item:
            return Response({"code": "not_found", "message": "Roadmap item not found."}, status=status.HTTP_404_NOT_FOUND)
        if request.data.get("status") not in dict(RoadmapItem.Status.choices):
            return Response({"code": "validation_error", "message": "A valid status is required."}, status=status.HTTP_400_BAD_REQUEST)
        item.status = request.data["status"]
        item.save(update_fields=["status"])
        return Response(RoadmapItemSerializer(item).data)

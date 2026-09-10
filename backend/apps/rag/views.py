from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent
from apps.careers.models import CareerRole
from apps.students.services import get_or_create_student_profile
from .models import CopilotConversation
from .serializers import CopilotAskSerializer, CopilotConversationSerializer
from .services import ask_copilot, recommended_actions


class CopilotAskView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        serializer = CopilotAskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = None
        if serializer.validated_data.get("role_slug"):
            role = CareerRole.objects.filter(slug=serializer.validated_data["role_slug"]).first()
            if not role:
                return Response({"code": "not_found", "message": "Career role not found."}, status=status.HTTP_404_NOT_FOUND)
        student = get_or_create_student_profile(request.user)
        conversation, answer, citations = ask_copilot(student=student, question=serializer.validated_data["question"], role=role, conversation_id=serializer.validated_data.get("conversation_id"))
        actions = recommended_actions(student, role)
        return Response({"answer": answer, "citations": citations, "sources": citations, "recommended_actions": actions, "conversation_id": str(conversation.id), "safety_note": "Guidance is grounded only in the cited curated EmployIQ sources."})


class CopilotConversationListView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        student = get_or_create_student_profile(request.user)
        conversations = CopilotConversation.objects.filter(student=student).select_related("role").prefetch_related("messages")[:20]
        return Response(CopilotConversationSerializer(conversations, many=True).data)

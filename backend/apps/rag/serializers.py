from rest_framework import serializers

from .models import CopilotConversation, CopilotMessage


class CopilotAskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000, trim_whitespace=True)
    role_slug = serializers.SlugField(required=False, allow_null=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)


class CopilotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CopilotMessage
        fields = ["id", "role", "content", "citation_ids", "created_at"]


class CopilotConversationSerializer(serializers.ModelSerializer):
    messages = CopilotMessageSerializer(many=True, read_only=True)

    class Meta:
        model = CopilotConversation
        fields = ["id", "created_at", "role", "messages"]

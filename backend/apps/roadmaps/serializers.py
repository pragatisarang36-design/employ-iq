from rest_framework import serializers
from .models import Roadmap, RoadmapItem


class RoadmapItemSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    class Meta:
        model = RoadmapItem
        fields = ["id", "sequence", "title", "description", "skill", "skill_name", "status"]
        read_only_fields = ["id", "sequence", "title", "description", "skill", "skill_name"]


class RoadmapSerializer(serializers.ModelSerializer):
    role_slug = serializers.CharField(source="role.slug", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    items = RoadmapItemSerializer(many=True, read_only=True)
    class Meta:
        model = Roadmap
        fields = ["id", "role_slug", "role_name", "status", "generated_at", "items"]

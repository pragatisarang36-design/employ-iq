from rest_framework import serializers

from .models import CareerRole, SkillGapSnapshot


class CareerRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerRole
        fields = ["id", "slug", "name", "support_level", "description"]


class GapAnalysisSerializer(serializers.ModelSerializer):
    role = CareerRoleSerializer(read_only=True)

    class Meta:
        model = SkillGapSnapshot
        fields = ["id", "role", "gaps", "created_at"]

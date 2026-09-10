"""
Serializers for assessments and dimensional scores.
Conforming to API_SPECIFICATION.md.
"""

from decimal import Decimal
from rest_framework import serializers

from .models import Assessment, AssessmentScore


class AssessmentScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentScore
        fields = ["id", "dimension", "score", "max_score"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        score = attrs.get("score")
        max_score = attrs.get("max_score", Decimal("100.0"))

        if score is not None and score < Decimal("0.0"):
            raise serializers.ValidationError({"score": "Score cannot be negative."})

        if max_score is not None and max_score <= Decimal("0.0"):
            raise serializers.ValidationError({"max_score": "Max score must be greater than zero."})

        if score is not None and max_score is not None and score > max_score:
            raise serializers.ValidationError({"score": "Score cannot exceed max_score."})

        return attrs


class AssessmentCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=Assessment.Type.choices,
        default=Assessment.Type.DIAGNOSTIC,
    )
    scores = AssessmentScoreSerializer(many=True, required=True)

    def validate_scores(self, value):
        if not value:
            raise serializers.ValidationError("At least one dimension score must be provided.")
        # Ensure distinct dimensions in the single assessment observation
        dimensions = [item["dimension"] for item in value]
        if len(dimensions) != len(set(dimensions)):
            raise serializers.ValidationError("Duplicate dimension scores provided in a single submission.")
        return value


class AssessmentDetailSerializer(serializers.ModelSerializer):
    scores = AssessmentScoreSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = ["id", "type", "submitted_at", "status", "scores"]
        read_only_fields = ["id", "submitted_at", "status", "scores"]

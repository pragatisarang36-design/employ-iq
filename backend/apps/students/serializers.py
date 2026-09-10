"""
Serializers for students app conforming to API_SPECIFICATION.md and ML_ARCHITECTURE.md.
"""

from decimal import Decimal
from rest_framework import serializers

from apps.accounts.serializers import InstitutionSerializer, UserMeSerializer
from .models import (
    Skill,
    StudentCertification,
    StudentExperience,
    StudentProfile,
    StudentSkill,
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "category", "canonical_key"]


class StudentSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), source="skill", write_only=True
    )

    class Meta:
        model = StudentSkill
        fields = ["id", "skill", "skill_id", "proficiency", "source"]


class StudentCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCertification
        fields = ["id", "name", "issuer", "earned_at"]


class StudentExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentExperience
        fields = ["id", "kind", "title", "complexity", "duration_months", "metadata"]


class StudentProfileDetailSerializer(serializers.ModelSerializer):
    user = UserMeSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)
    skills = StudentSkillSerializer(many=True, read_only=True)
    certifications = StudentCertificationSerializer(many=True, read_only=True)
    experiences = StudentExperienceSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "institution",
            "cohort",
            "department",
            "cgpa",
            "tenth_percentage",
            "twelfth_percentage",
            "current_backlogs",
            "history_of_backlogs",
            "aptitude_score",
            "communication_rating",
            "extracurricular_score",
            "skills",
            "certifications",
            "experiences",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "institution", "created_at", "updated_at"]


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Validates declared profile fields with explicit server-side range constraints.
    Rejects undeclared model-affecting fields per API_SPECIFICATION.md.
    """

    ALLOWED_FIELDS = {
        "cohort",
        "department",
        "cgpa",
        "tenth_percentage",
        "twelfth_percentage",
        "current_backlogs",
        "history_of_backlogs",
        "aptitude_score",
        "communication_rating",
        "extracurricular_score",
    }

    class Meta:
        model = StudentProfile
        fields = [
            "cohort",
            "department",
            "cgpa",
            "tenth_percentage",
            "twelfth_percentage",
            "current_backlogs",
            "history_of_backlogs",
            "aptitude_score",
            "communication_rating",
            "extracurricular_score",
        ]

    def validate(self, attrs):
        # Reject any unknown fields passed in raw data
        extra_fields = set(self.initial_data.keys()) - self.ALLOWED_FIELDS
        if extra_fields:
            raise serializers.ValidationError(
                {field: "Unknown or unauthorized model-affecting field." for field in extra_fields}
            )

        if "cgpa" in attrs:
            cgpa = attrs["cgpa"]
            if cgpa < Decimal("0.0") or cgpa > Decimal("10.0"):
                raise serializers.ValidationError({"cgpa": "CGPA must be between 0.0 and 10.0."})

        if "tenth_percentage" in attrs:
            val = attrs["tenth_percentage"]
            if val < Decimal("0.0") or val > Decimal("100.0"):
                raise serializers.ValidationError({"tenth_percentage": "Percentage must be between 0.0 and 100.0."})

        if "twelfth_percentage" in attrs:
            val = attrs["twelfth_percentage"]
            if val < Decimal("0.0") or val > Decimal("100.0"):
                raise serializers.ValidationError({"twelfth_percentage": "Percentage must be between 0.0 and 100.0."})

        if "aptitude_score" in attrs:
            val = attrs["aptitude_score"]
            if val < Decimal("0.0") or val > Decimal("100.0"):
                raise serializers.ValidationError({"aptitude_score": "Score must be between 0.0 and 100.0."})

        if "communication_rating" in attrs:
            val = attrs["communication_rating"]
            if val < Decimal("0.0") or val > Decimal("10.0"):
                raise serializers.ValidationError({"communication_rating": "Rating must be between 0.0 and 10.0."})

        if "extracurricular_score" in attrs:
            val = attrs["extracurricular_score"]
            if val < Decimal("0.0") or val > Decimal("100.0"):
                raise serializers.ValidationError({"extracurricular_score": "Score must be between 0.0 and 100.0."})

        return attrs


class FeatureSnapshotSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    institution_id = serializers.UUIDField()
    feature_schema_version = serializers.CharField()
    generated_at = serializers.DateTimeField()
    features = serializers.DictField()

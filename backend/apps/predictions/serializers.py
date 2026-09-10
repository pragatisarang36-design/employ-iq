from rest_framework import serializers

from ml.feature_schema import FEATURE_LABELS

from .models import PredictionExplanation, PredictionRun


class PredictionExplanationSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = PredictionExplanation
        fields = ["feature_key", "label", "shap_value", "direction", "rank"]

    def get_label(self, obj):
        return FEATURE_LABELS.get(obj.feature_key, obj.feature_key.replace("_", " ").title())


class PredictionSerializer(serializers.ModelSerializer):
    probability_percent = serializers.SerializerMethodField()
    intervention_required = serializers.SerializerMethodField()
    model_version = serializers.CharField(source="model_version.version", read_only=True)
    feature_schema_version = serializers.CharField(source="model_version.feature_schema_version", read_only=True)
    generated_at = serializers.DateTimeField(source="created_at", read_only=True)
    explanation = PredictionExplanationSerializer(source="explanations", many=True, read_only=True)
    disclaimer = serializers.SerializerMethodField()
    strengths = serializers.SerializerMethodField()
    weaknesses = serializers.SerializerMethodField()
    readiness_score = serializers.SerializerMethodField()
    baseline_probability_percent = serializers.SerializerMethodField()

    class Meta:
        model = PredictionRun
        fields = ["id", "probability_percent", "baseline_probability_percent", "readiness_score", "readiness", "intervention_required", "model_version", "feature_schema_version", "generated_at", "explanation", "strengths", "weaknesses", "disclaimer"]

    def get_probability_percent(self, obj): return round(float(obj.probability) * 100, 2)
    def get_baseline_probability_percent(self, obj): return round(float(obj.baseline_probability) * 100, 2) if obj.baseline_probability is not None else None
    def get_intervention_required(self, obj): return float(obj.probability) < 0.60
    def get_disclaimer(self, obj): return "This readiness score is decision support, not a guarantee of placement."
    def get_readiness_score(self, obj): return self.get_probability_percent(obj)
    def get_strengths(self, obj): return [FEATURE_LABELS.get(item.feature_key, item.feature_key) for item in obj.explanations.all() if item.direction == "positive"]
    def get_weaknesses(self, obj): return [FEATURE_LABELS.get(item.feature_key, item.feature_key) for item in obj.explanations.all() if item.direction == "negative"]

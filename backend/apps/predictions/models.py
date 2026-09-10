import uuid
from django.db import models


class ModelVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=100, unique=True)
    algorithm = models.CharField(max_length=100)
    feature_schema_version = models.CharField(max_length=30)
    metrics = models.JSONField(default=dict)
    artifact_uri = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "model_versions"


class PredictionRun(models.Model):
    class Readiness(models.TextChoices):
        READY = "ready", "Ready"
        NEAR_READY = "near_ready", "Near ready"
        NEEDS_TRAINING = "needs_training", "Needs training"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="prediction_runs")
    model_version = models.ForeignKey(ModelVersion, on_delete=models.PROTECT, related_name="prediction_runs")
    probability = models.DecimalField(max_digits=5, decimal_places=4)
    readiness = models.CharField(max_length=30, choices=Readiness.choices)
    input_snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "prediction_runs"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["student", "-created_at"])]


class PredictionExplanation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prediction_run = models.ForeignKey(PredictionRun, on_delete=models.CASCADE, related_name="explanations")
    feature_key = models.CharField(max_length=100)
    shap_value = models.DecimalField(max_digits=10, decimal_places=4)
    direction = models.CharField(max_length=10)
    rank = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "prediction_explanations"
        ordering = ["rank"]
        constraints = [models.UniqueConstraint(fields=["prediction_run", "rank"], name="unique_prediction_explanation_rank")]

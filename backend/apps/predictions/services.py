from decimal import Decimal

from django.db import transaction

from apps.accounts.services import record_audit_event
from apps.students.services import build_feature_snapshot
from ml.inference import ARTIFACT_PATH, load_active_artifact
from ml.client import predict

from .models import ModelVersion, PredictionExplanation, PredictionRun


def get_or_register_active_model() -> ModelVersion:
    artifact = load_active_artifact()
    ModelVersion.objects.filter(is_active=True).exclude(version=artifact["version"]).update(is_active=False)
    model, _ = ModelVersion.objects.update_or_create(
        version=artifact["version"],
        defaults={"algorithm": artifact["algorithm"], "feature_schema_version": artifact["feature_schema_version"],
                  "metrics": artifact["metrics"], "artifact_uri": str(ARTIFACT_PATH), "is_active": True},
    )
    return model


@transaction.atomic
def create_prediction(*, student, actor):
    snapshot = build_feature_snapshot(student)
    result = predict(snapshot)
    model = get_or_register_active_model()
    run = PredictionRun.objects.create(student=student, model_version=model, probability=Decimal(str(result["probability"])), baseline_probability=Decimal(str(result["baseline_probability"])),
        readiness=result["readiness"], input_snapshot=snapshot)
    PredictionExplanation.objects.bulk_create([
        PredictionExplanation(prediction_run=run, feature_key=item["feature_key"], shap_value=Decimal(str(item["shap_value"])),
                              direction=item["direction"], rank=index)
        for index, item in enumerate(result["explanation"], start=1)
    ])
    record_audit_event(action="prediction.created", actor=actor, institution=student.institution, object_type="PredictionRun", object_id=str(run.id), metadata={"model_version": model.version, "readiness": run.readiness})
    return run

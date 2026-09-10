from .models import PredictionRun


def get_latest_prediction(student):
    return PredictionRun.objects.filter(student=student).select_related("model_version").prefetch_related("explanations").first()


def get_prediction_for_student(prediction_id, student):
    return PredictionRun.objects.filter(id=prediction_id, student=student).select_related("model_version").prefetch_related("explanations").first()


def get_prediction_for_institution(prediction_id, institution):
    return PredictionRun.objects.filter(id=prediction_id, student__institution=institution).select_related("model_version").prefetch_related("explanations").first()

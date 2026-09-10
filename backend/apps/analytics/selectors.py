from django.db.models import Count

from apps.predictions.models import PredictionRun
from apps.students.models import StudentProfile


def overview(institution):
    students = StudentProfile.objects.filter(institution=institution)
    latest_by_student = {}
    for run in PredictionRun.objects.filter(student__institution=institution).select_related("student").order_by("student_id", "-created_at"):
        latest_by_student.setdefault(run.student_id, run)
    readiness = {"ready": 0, "near_ready": 0, "needs_training": 0}
    for run in latest_by_student.values(): readiness[run.readiness] += 1
    return {"total_students": students.count(), "students_with_predictions": len(latest_by_student), "readiness_breakdown": readiness, "average_probability_percent": round(sum(float(run.probability) for run in latest_by_student.values()) / len(latest_by_student) * 100, 2) if latest_by_student else 0}


def interventions(institution):
    latest_by_student = {}
    for run in PredictionRun.objects.filter(student__institution=institution).select_related("student__user").order_by("student_id", "-created_at"):
        latest_by_student.setdefault(run.student_id, run)
    return [{"student_id": str(run.student_id), "student_name": run.student.user.full_name, "email": run.student.user.email, "probability_percent": round(float(run.probability) * 100, 2), "readiness": run.readiness, "generated_at": run.created_at} for run in latest_by_student.values() if float(run.probability) < 0.60]

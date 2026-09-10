from django.db.models import Count

from apps.predictions.models import PredictionRun
from apps.students.models import StudentProfile
from apps.careers.models import StudentRoleSelection
from apps.careers.services import create_gap_analysis
from apps.roadmaps.models import Roadmap


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


def department_readiness(institution):
    buckets = {}
    for run in PredictionRun.objects.filter(student__institution=institution).select_related("student").order_by("student_id", "-created_at"):
        buckets.setdefault(run.student_id, run)
    departments = {}
    for run in buckets.values():
        department = run.student.department or "Unspecified"
        item = departments.setdefault(department, {"department": department, "students_with_predictions": 0, "probability_total": 0.0, "below_60_count": 0})
        item["students_with_predictions"] += 1
        item["probability_total"] += float(run.probability) * 100
        item["below_60_count"] += int(float(run.probability) < 0.60)
    return [{**item, "average_probability_percent": round(item.pop("probability_total") / item["students_with_predictions"], 2)} for item in departments.values()]


def institutional_skill_deficits(institution):
    counts = {}
    for snapshot in __import__("apps.careers.models", fromlist=["SkillGapSnapshot"]).SkillGapSnapshot.objects.filter(student__institution=institution):
        for gap in snapshot.gaps:
            name = gap.get("skill")
            if name:
                counts[name] = counts.get(name, 0) + 1
    return [{"skill": skill, "students_with_gap": count} for skill, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def student_dashboard(student):
    """Frontend-friendly single payload.  It never crosses institution boundaries."""
    prediction = PredictionRun.objects.filter(student=student).select_related("model_version").prefetch_related("explanations").first()
    selection = StudentRoleSelection.objects.filter(student=student, is_primary=True).select_related("role").first()
    gaps = []
    if selection:
        gap_snapshot = create_gap_analysis(student=student, role=selection.role, prediction_run=prediction)
        gaps = gap_snapshot.gaps
    roadmap = Roadmap.objects.filter(student=student, status=Roadmap.Status.ACTIVE).select_related("role").prefetch_related("items__skill").first()
    assessment_scores = {}
    for assessment in student.assessments.prefetch_related("scores").all()[:1]:
        assessment_scores = {score.dimension: float(score.score) for score in assessment.scores.all()}
    strengths = []
    weaknesses = []
    if prediction:
        for explanation in prediction.explanations.all():
            (strengths if explanation.direction == "positive" else weaknesses).append(explanation.feature_key.replace("_", " ").title())
    return {
        "profile": {"id": str(student.id), "name": student.user.full_name, "department": student.department, "cgpa": float(student.cgpa)},
        "target_role": {"slug": selection.role.slug, "name": selection.role.name} if selection else None,
        "prediction": {"probability_percent": round(float(prediction.probability) * 100, 2), "readiness_score": round(float(prediction.probability) * 100, 2), "readiness": prediction.readiness, "generated_at": prediction.created_at} if prediction else None,
        "assessment_scores": assessment_scores,
        "skill_count": student.skills.count(),
        "strongest_skills": strengths,
        "weakest_skills": weaknesses,
        "skill_gaps": gaps,
        "roadmap": {"id": str(roadmap.id), "role_slug": roadmap.role.slug, "items": [{"id": str(item.id), "sequence": item.sequence, "title": item.title, "status": item.status} for item in roadmap.items.all()]} if roadmap else None,
        "recommended_actions": [f"Improve {gap['skill']} ({gap['priority']} priority)." for gap in gaps[:3]] or ["Create a prediction and choose a target career role to personalize your next steps."],
    }

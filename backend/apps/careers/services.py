from django.db import transaction

from apps.students.models import StudentSkill

from .models import CareerRole, SkillGapSnapshot, StudentRoleSelection

LEVEL_SCORE = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}


@transaction.atomic
def select_role(*, student, role):
    StudentRoleSelection.objects.filter(student=student, is_primary=True).exclude(role=role).update(is_primary=False)
    selection, _ = StudentRoleSelection.objects.update_or_create(student=student, role=role, defaults={"is_primary": True})
    return selection


@transaction.atomic
def create_gap_analysis(*, student, role, prediction_run=None):
    student_levels = {item.skill_id: item.proficiency for item in student.skills.select_related("skill")}
    gaps = []
    for benchmark in role.benchmarks.select_related("skill").order_by("priority", "skill__name"):
        current = student_levels.get(benchmark.skill_id)
        if current is None or LEVEL_SCORE[current] < LEVEL_SCORE[benchmark.target_level]:
            gaps.append({"skill_id": str(benchmark.skill_id), "skill": benchmark.skill.name, "category": benchmark.skill.category,
                         "current_level": current or "not_started", "target_level": benchmark.target_level,
                         "priority": benchmark.priority, "rationale": benchmark.rationale})
    return SkillGapSnapshot.objects.create(student=student, role=role, prediction_run=prediction_run, gaps=gaps)

import uuid
from django.conf import settings
from django.db import models
from apps.students.models import StudentSkill


class CareerRole(models.Model):
    class SupportLevel(models.TextChoices):
        FULL = "full", "Fully supported"
        STARTER = "starter", "Starter guidance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    support_level = models.CharField(max_length=20, choices=SupportLevel.choices, default=SupportLevel.FULL)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "career_roles"
        ordering = ["name"]


class RoleSkillBenchmark(models.Model):
    class Priority(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(CareerRole, on_delete=models.CASCADE, related_name="benchmarks")
    skill = models.ForeignKey("students.Skill", on_delete=models.PROTECT, related_name="role_benchmarks")
    target_level = models.CharField(max_length=20, choices=StudentSkill.Proficiency.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices)
    rationale = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = "role_skill_benchmarks"
        constraints = [models.UniqueConstraint(fields=["role", "skill"], name="unique_role_skill_benchmark")]


class StudentRoleSelection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="role_selections")
    role = models.ForeignKey(CareerRole, on_delete=models.PROTECT, related_name="student_selections")
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "student_role_selections"
        constraints = [models.UniqueConstraint(fields=["student", "role"], name="unique_student_role_selection")]


class SkillGapSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="skill_gap_snapshots")
    role = models.ForeignKey(CareerRole, on_delete=models.CASCADE, related_name="gap_snapshots")
    prediction_run = models.ForeignKey("predictions.PredictionRun", on_delete=models.SET_NULL, null=True, blank=True)
    gaps = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "skill_gap_snapshots"
        ordering = ["-created_at"]

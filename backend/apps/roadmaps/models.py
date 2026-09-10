import uuid
from django.db import models


class Roadmap(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="roadmaps")
    role = models.ForeignKey("careers.CareerRole", on_delete=models.PROTECT)
    based_on_gap_snapshot = models.ForeignKey("careers.SkillGapSnapshot", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roadmaps"
        ordering = ["-generated_at"]


class RoadmapItem(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name="items")
    sequence = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    skill = models.ForeignKey("students.Skill", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)

    class Meta:
        db_table = "roadmap_items"
        ordering = ["sequence"]
        constraints = [models.UniqueConstraint(fields=["roadmap", "sequence"], name="unique_roadmap_sequence")]

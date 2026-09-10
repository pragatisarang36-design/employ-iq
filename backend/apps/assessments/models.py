import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Assessment(models.Model):
    class Type(models.TextChoices):
        DIAGNOSTIC = "diagnostic", "Diagnostic Assessment"
        PRACTICE = "practice", "Practice Test"
        MOCK_INTERVIEW = "mock_interview", "Mock Interview"
        PROCTORED = "proctored", "Proctored Assessment"

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        EVALUATED = "evaluated", "Evaluated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    type = models.CharField(
        max_length=50,
        choices=Type.choices,
        default=Type.DIAGNOSTIC,
        db_index=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.COMPLETED,
    )

    class Meta:
        db_table = "assessments"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Assessment [{self.type}] - {self.student.user.email} at {self.submitted_at.isoformat()}"


class AssessmentScore(models.Model):
    class Dimension(models.TextChoices):
        QUANTITATIVE = "quantitative", "Quantitative Aptitude"
        LOGICAL = "logical", "Logical Reasoning"
        CODING = "coding", "Coding & Problem Solving"
        COMMUNICATION = "communication", "Communication Skills"
        INTERVIEW = "interview", "Technical Interview"
        PRESENTATION = "presentation", "Presentation Skills"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="scores",
    )
    dimension = models.CharField(
        max_length=50,
        choices=Dimension.choices,
        db_index=True,
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.0"))],
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("100.0"),
        validators=[MinValueValidator(Decimal("1.0"))],
    )

    class Meta:
        db_table = "assessment_scores"
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "dimension"],
                name="unique_assessment_dimension_score",
            ),
        ]
        indexes = [
            models.Index(fields=["assessment", "dimension"]),
        ]

    def __str__(self):
        return f"{self.dimension}: {self.score}/{self.max_score} (Assessment {self.assessment_id})"

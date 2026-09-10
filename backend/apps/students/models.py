import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Skill(models.Model):
    class Category(models.TextChoices):
        PROGRAMMING_LANGUAGE = "programming_language", "Programming Language"
        FRAMEWORK = "framework", "Framework / Library"
        DATABASE = "database", "Database"
        CLOUD_DEVOPS = "cloud_devops", "Cloud & DevOps"
        CORE_CS = "core_cs", "Core CS (DSA, OS, DBMS, Networks)"
        SOFT_SKILL = "soft_skill", "Soft Skill / Communication"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.PROGRAMMING_LANGUAGE,
        db_index=True,
    )
    canonical_key = models.SlugField(max_length=100, unique=True, db_index=True)

    class Meta:
        db_table = "skills"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category})"


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    institution = models.ForeignKey(
        "accounts.Institution",
        on_delete=models.PROTECT,
        related_name="student_profiles",
    )
    cohort = models.CharField(max_length=50, blank=True, default="")
    department = models.CharField(max_length=100, blank=True, default="")

    # Academic facts
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("10.0"))],
    )
    tenth_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("100.0"))],
    )
    twelfth_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("100.0"))],
    )
    current_backlogs = models.PositiveIntegerField(default=0)
    history_of_backlogs = models.PositiveIntegerField(default=0)

    # Observed / self-reported scores
    aptitude_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("100.0"))],
    )
    communication_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("10.0"))],
    )
    extracurricular_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("100.0"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_profiles"
        indexes = [
            models.Index(fields=["institution", "cohort", "department"]),
        ]

    def __str__(self):
        return f"Profile: {self.user.email} [{self.institution.slug}]"


class StudentSkill(models.Model):
    class Proficiency(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    class Source(models.TextChoices):
        SELF_REPORTED = "self_reported", "Self Reported"
        ASSESSMENT = "assessment", "Assessment Verified"
        COURSEWORK = "coursework", "Coursework"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name="student_skills",
    )
    proficiency = models.CharField(
        max_length=20,
        choices=Proficiency.choices,
        default=Proficiency.BEGINNER,
    )
    source = models.CharField(
        max_length=30,
        choices=Source.choices,
        default=Source.SELF_REPORTED,
    )

    class Meta:
        db_table = "student_skills"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "skill"],
                name="unique_student_skill",
            ),
        ]

    def __str__(self):
        return f"{self.student.user.email} - {self.skill.name} ({self.proficiency})"


class StudentCertification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255)
    earned_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "student_certifications"

    def __str__(self):
        return f"{self.name} by {self.issuer} ({self.student.user.email})"


class StudentExperience(models.Model):
    class Kind(models.TextChoices):
        PROJECT = "project", "Project"
        INTERNSHIP = "internship", "Internship"
        OPEN_SOURCE = "open_source", "Open Source"
        RESEARCH = "research", "Research"

    class Complexity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="experiences",
    )
    kind = models.CharField(max_length=30, choices=Kind.choices, default=Kind.PROJECT)
    title = models.CharField(max_length=255)
    complexity = models.CharField(max_length=20, choices=Complexity.choices, default=Complexity.MEDIUM)
    duration_months = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "student_experiences"

    def __str__(self):
        return f"{self.kind}: {self.title} ({self.student.user.email})"

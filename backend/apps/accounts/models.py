import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "institutions"
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    TPO = "tpo", "TPO"
    ADMIN = "admin", "Admin"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, institution=None, role=UserRole.STUDENT, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(
            email=email,
            institution=institution,
            role=role,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
    )
    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "email"],
                condition=models.Q(institution__isnull=False),
                name="unique_institution_user_email",
            ),
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(institution__isnull=True),
                name="unique_platform_admin_email",
            ),
        ]
        indexes = [
            models.Index(fields=["institution", "role"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        inst_label = f" ({self.institution.slug})" if self.institution else ""
        return f"{self.email} [{self.role}]{inst_label}"

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT

    @property
    def is_tpo(self):
        return self.role == UserRole.TPO

    @property
    def is_institution_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=100, db_index=True)
    object_type = models.CharField(max_length=100, blank=True, default="")
    object_id = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["institution", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        actor_email = self.actor.email if self.actor else "system"
        return f"[{self.action}] by {actor_email} at {self.created_at.isoformat()}"

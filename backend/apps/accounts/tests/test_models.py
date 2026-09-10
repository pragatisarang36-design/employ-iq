import uuid
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import AuditEvent, Institution, User, UserRole
from apps.accounts.services import record_audit_event, redact_sensitive_data


class ModelTests(TestCase):
    def setUp(self):
        self.inst1 = Institution.objects.create(name="MIT", slug="mit")
        self.inst2 = Institution.objects.create(name="Stanford", slug="stanford")

    def test_institution_creation(self):
        self.assertEqual(str(self.inst1), "MIT")
        self.assertTrue(isinstance(self.inst1.id, uuid.UUID))
        self.assertTrue(self.inst1.is_active)

    def test_user_creation_and_defaults(self):
        user = User.objects.create_user(
            email="STUDENT@mit.edu",
            password="securePassword123!",
            institution=self.inst1,
        )
        self.assertEqual(user.email, "student@mit.edu")  # Normalized to lowercase
        self.assertTrue(user.check_password("securePassword123!"))
        self.assertEqual(user.role, UserRole.STUDENT)
        self.assertTrue(user.is_student)
        self.assertFalse(user.is_tpo)
        self.assertFalse(user.is_institution_admin)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_tpo_and_admin_roles(self):
        tpo = User.objects.create_user(
            email="tpo@mit.edu",
            password="password123",
            institution=self.inst1,
            role=UserRole.TPO,
        )
        self.assertTrue(tpo.is_tpo)
        self.assertFalse(tpo.is_student)
        self.assertFalse(tpo.is_institution_admin)

        admin = User.objects.create_user(
            email="admin@mit.edu",
            password="password123",
            institution=self.inst1,
            role=UserRole.ADMIN,
        )
        self.assertTrue(admin.is_institution_admin)

    def test_superuser_creation(self):
        admin = User.objects.create_superuser(
            email="super@employiq.internal",
            password="superpassword123",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, UserRole.ADMIN)
        self.assertTrue(admin.is_institution_admin)

    def test_multi_tenant_email_uniqueness(self):
        from django.db import transaction

        # Same email in SAME institution must raise IntegrityError
        User.objects.create_user(
            email="alice@college.edu",
            password="pass1",
            institution=self.inst1,
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user(
                    email="alice@college.edu",
                    password="pass2",
                    institution=self.inst1,
                )

        # Same email in DIFFERENT institution must succeed (multi-tenant isolation)
        user_inst2 = User.objects.create_user(
            email="alice@college.edu",
            password="pass2",
            institution=self.inst2,
        )
        self.assertIsNotNone(user_inst2.id)

    def test_platform_admin_email_uniqueness(self):
        from django.db import transaction

        User.objects.create_superuser(
            email="platform_admin@employiq.internal",
            password="password1",
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_superuser(
                    email="platform_admin@employiq.internal",
                    password="password2",
                )



    def test_audit_event_creation_and_redaction(self):
        user = User.objects.create_user(
            email="audit_target@mit.edu",
            password="pass",
            institution=self.inst1,
        )
        payload = {
            "password": "secret_password",
            "token": "secret_token_value",
            "safe_field": "visible_value",
            "nested": {
                "refresh_token": "another_secret",
                "normal": 123,
            },
        }
        event = record_audit_event(
            action="test.action",
            actor=user,
            object_type="User",
            object_id=str(user.id),
            metadata=payload,
        )

        self.assertEqual(event.institution, self.inst1)
        self.assertEqual(event.metadata["password"], "[REDACTED]")
        self.assertEqual(event.metadata["token"], "[REDACTED]")
        self.assertEqual(event.metadata["safe_field"], "visible_value")
        self.assertEqual(event.metadata["nested"]["refresh_token"], "[REDACTED]")
        self.assertEqual(event.metadata["nested"]["normal"], 123)

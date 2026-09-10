from django.test import TestCase

from apps.accounts.models import AuditEvent, Institution, User, UserRole
from apps.accounts.selectors import get_audit_events_for_institution
from apps.accounts.services import record_audit_event, redact_sensitive_data


class AuditLoggingTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Delta Tech", slug="delta")
        self.actor = User.objects.create_user(
            email="actor@delta.edu",
            password="password",
            institution=self.institution,
            role=UserRole.ADMIN,
        )

    def test_record_audit_event_basic(self):
        event = record_audit_event(
            action="config.updated",
            actor=self.actor,
            object_type="SystemConfig",
            object_id="cfg_001",
            metadata={"setting": "theme", "value": "dark"},
        )
        self.assertIsNotNone(event.id)
        self.assertEqual(event.actor, self.actor)
        self.assertEqual(event.institution, self.institution)
        self.assertEqual(event.action, "config.updated")
        self.assertEqual(event.metadata["setting"], "theme")

    def test_redact_sensitive_data_comprehensive(self):
        sensitive_dict = {
            "user_email": "test@delta.edu",
            "password": "plaintext_password",
            "secret_key": "xyz123",
            "auth_token": "bearer_abc",
            "nested": {
                "refresh": "refresh_val",
                "api_key": "api_secret",
                "non_sensitive": "keep_me",
            },
            "array_data": [
                {"access": "access_token_str", "valid": True},
                "plain_string",
            ],
        }

        cleaned = redact_sensitive_data(sensitive_dict)

        self.assertEqual(cleaned["user_email"], "test@delta.edu")
        self.assertEqual(cleaned["password"], "[REDACTED]")
        self.assertEqual(cleaned["secret_key"], "[REDACTED]")
        self.assertEqual(cleaned["auth_token"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["refresh"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["non_sensitive"], "keep_me")
        self.assertEqual(cleaned["array_data"][0]["access"], "[REDACTED]")
        self.assertTrue(cleaned["array_data"][0]["valid"])
        self.assertEqual(cleaned["array_data"][1], "plain_string")

    def test_get_audit_events_for_institution_selector(self):
        record_audit_event(
            action="action.one",
            actor=self.actor,
            institution=self.institution,
        )
        record_audit_event(
            action="action.two",
            actor=self.actor,
            institution=self.institution,
        )

        all_events = get_audit_events_for_institution(self.institution)
        self.assertEqual(all_events.count(), 2)

        filtered_events = get_audit_events_for_institution(self.institution, action="action.one")
        self.assertEqual(filtered_events.count(), 1)
        self.assertEqual(filtered_events.first().action, "action.one")

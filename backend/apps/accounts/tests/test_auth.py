from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import AuditEvent, Institution, User, UserRole


class AuthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(name="Tech University", slug="tech-uni")
        self.student = User.objects.create_user(
            email="student@tech.edu",
            password="StrongPassword123!",
            institution=self.institution,
            role=UserRole.STUDENT,
            first_name="Jane",
            last_name="Doe",
        )

    def test_obtain_token_success(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "StrongPassword123!",
                "institution_slug": "tech-uni",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Inspect token claims
        access_token = AccessToken(response.data["access"])
        self.assertEqual(access_token["role"], UserRole.STUDENT)
        self.assertEqual(access_token["email"], "student@tech.edu")
        self.assertEqual(access_token["institution_id"], str(self.institution.id))

        # Check audit event
        audit = AuditEvent.objects.filter(action="auth.login").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor, self.student)
        self.assertEqual(audit.institution, self.institution)

    def test_obtain_token_invalid_password(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "wrong_password",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "validation_error")

    def test_token_refresh_and_rotation(self):
        login_res = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        refresh_token = login_res.data["refresh"]

        refresh_res = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_res.data)

        # Verify audit event for refresh
        refresh_audit = AuditEvent.objects.filter(action="auth.token_refresh").first()
        self.assertIsNotNone(refresh_audit)

    def test_logout_and_token_blacklisting(self):
        login_res = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        access_token = login_res.data["access"]
        refresh_token = login_res.data["refresh"]

        # Call logout with authorization header and refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_res = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_res.data["status"], "ok")

        # Now attempting to use the blacklisted refresh token MUST fail
        failed_refresh = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(failed_refresh.status_code, status.HTTP_401_UNAUTHORIZED)

        # Verify logout audit event
        logout_audit = AuditEvent.objects.filter(action="auth.logout").first()
        self.assertIsNotNone(logout_audit)
        self.assertEqual(logout_audit.actor, self.student)

    def test_user_me_endpoint(self):
        # Without auth -> 401
        unauth_res = self.client.get("/api/v1/me/")
        self.assertEqual(unauth_res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unauth_res.data["code"], "authentication_failed")

        # With auth -> 200
        self.client.force_authenticate(user=self.student)
        me_res = self.client.get("/api/v1/me/")
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data["email"], "student@tech.edu")
        self.assertEqual(me_res.data["role"], "student")
        self.assertEqual(me_res.data["institution"]["slug"], "tech-uni")

    def test_registration_endpoint(self):
        reg_res = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "new_student@tech.edu",
                "password": "StrongPassword999!",
                "institution_slug": "tech-uni",
                "role": "student",
                "first_name": "Bob",
                "last_name": "Smith",
            },
            format="json",
        )
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reg_res.data["email"], "new_student@tech.edu")
        self.assertEqual(reg_res.data["role"], "student")

        # Attempt duplicate registration in same institution
        dup_res = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "new_student@tech.edu",
                "password": "StrongPassword999!",
                "institution_slug": "tech-uni",
                "role": "student",
            },
            format="json",
        )
        self.assertEqual(dup_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(dup_res.data["code"], "validation_error")

    def test_health_check_endpoints(self):
        # Base /api/health/ used by React shell
        res_legacy = self.client.get("/api/health/")
        self.assertEqual(res_legacy.status_code, status.HTTP_200_OK)
        self.assertEqual(res_legacy.json(), {"status": "ok", "service": "employiq-api"})

        # Versioned /api/v1/health/
        res_v1 = self.client.get("/api/v1/health/")
        self.assertEqual(res_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(res_v1.json(), {"status": "ok", "service": "employiq-api"})

    def test_multi_tenant_token_disambiguation(self):
        # Create second institution with user having same email address
        inst2 = Institution.objects.create(name="Polytech", slug="polytech")
        User.objects.create_user(
            email="student@tech.edu",
            password="PolytechPassword123!",
            institution=inst2,
            role=UserRole.STUDENT,
        )

        # 1. Login without institution_slug when multiple exist -> must fail with 400
        ambiguous_res = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        self.assertEqual(ambiguous_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("institution_slug", ambiguous_res.data["details"])

        # 2. Login with institution_slug for first institution -> succeeds
        res1 = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "StrongPassword123!",
                "institution_slug": "tech-uni",
            },
            format="json",
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        token1 = AccessToken(res1.data["access"])
        self.assertEqual(token1["institution_id"], str(self.institution.id))

        # 3. Login with institution_slug for second institution -> succeeds
        res2 = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "PolytechPassword123!",
                "institution_slug": "polytech",
            },
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        token2 = AccessToken(res2.data["access"])
        self.assertEqual(token2["institution_id"], str(inst2.id))

        # 4. Login with non-existent institution_slug -> 400
        invalid_slug_res = self.client.post(
            "/api/v1/auth/token/",
            {
                "email": "student@tech.edu",
                "password": "StrongPassword123!",
                "institution_slug": "non-existent-college",
            },
            format="json",
        )
        self.assertEqual(invalid_slug_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_invalid_or_malformed_token(self):
        self.client.force_authenticate(user=self.student)
        res = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": "malformed.token.value"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["code"], "validation_error")



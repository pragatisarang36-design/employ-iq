from rest_framework.test import APITestCase
from apps.accounts.models import Institution, User, UserRole

class AnalyticsApiTests(APITestCase):
    def test_tpo_can_access_empty_institution_overview(self):
        institution = Institution.objects.create(name="Demo", slug="analytics-demo")
        tpo = User.objects.create_user(email="tpo@demo.edu", password="Password123!", institution=institution, role=UserRole.TPO)
        self.client.force_authenticate(tpo)
        response = self.client.get("/api/v1/analytics/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_students"], 0)

from decimal import Decimal

from rest_framework.test import APITestCase

from apps.accounts.models import Institution, User, UserRole
from apps.students.models import StudentProfile


class PredictionApiTests(APITestCase):
    def setUp(self):
        institution = Institution.objects.create(name="Demo Institute", slug="demo")
        self.user = User.objects.create_user(email="student@demo.edu", password="Password123!", institution=institution, role=UserRole.STUDENT)
        StudentProfile.objects.create(user=self.user, institution=institution, cgpa=Decimal("8.2"), tenth_percentage=Decimal("85"), twelfth_percentage=Decimal("82"), current_backlogs=0, aptitude_score=Decimal("78"), communication_rating=Decimal("7.0"), extracurricular_score=Decimal("65"))
        self.client.force_authenticate(self.user)

    def test_student_can_create_and_retrieve_a_real_prediction(self):
        created = self.client.post("/api/v1/predictions/", {}, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertGreaterEqual(created.data["probability_percent"], 0)
        self.assertLessEqual(created.data["probability_percent"], 100)
        self.assertEqual(created.data["model_version"], "placement-readiness-lightgbm-v3")
        self.assertIsNotNone(created.data["baseline_probability_percent"])
        self.assertEqual(len(created.data["explanation"]), 5)
        latest = self.client.get("/api/v1/predictions/latest/")
        self.assertEqual(latest.status_code, 200)

    def test_tpo_can_retrieve_same_institution_prediction_only(self):
        created = self.client.post("/api/v1/predictions/", {}, format="json")
        tpo = User.objects.create_user(email="tpo@demo.edu", password="Password123!", institution=self.user.institution, role=UserRole.TPO)
        self.client.force_authenticate(tpo)
        self.assertEqual(self.client.get(f"/api/v1/predictions/{created.data['id']}/").status_code, 200)
        other = Institution.objects.create(name="Other", slug="other-predictions")
        outsider = User.objects.create_user(email="tpo@other.edu", password="Password123!", institution=other, role=UserRole.TPO)
        self.client.force_authenticate(outsider)
        self.assertEqual(self.client.get(f"/api/v1/predictions/{created.data['id']}/").status_code, 404)

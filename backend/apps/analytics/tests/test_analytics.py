from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import Institution, User, UserRole
from apps.careers.models import CareerRole, RoleSkillBenchmark
from apps.rag.models import KnowledgeDocument
from apps.rag.services import checksum
from apps.students.models import Skill

class AnalyticsApiTests(APITestCase):
    def test_tpo_can_access_empty_institution_overview(self):
        institution = Institution.objects.create(name="Demo", slug="analytics-demo")
        tpo = User.objects.create_user(email="tpo@demo.edu", password="Password123!", institution=institution, role=UserRole.TPO)
        self.client.force_authenticate(tpo)
        response = self.client.get("/api/v1/analytics/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_students"], 0)

    def test_student_dashboard_is_scoped_and_frontend_ready(self):
        institution = Institution.objects.create(name="Student Demo", slug="student-dashboard")
        student = User.objects.create_user(email="student@demo.edu", password="Password123!", institution=institution, role=UserRole.STUDENT)
        self.client.force_authenticate(student)
        response = self.client.get("/api/v1/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["skill_count"], 0)
        self.assertIsNone(response.data["prediction"])

    def test_demo_student_end_to_end_flow(self):
        institution = Institution.objects.create(name="End To End", slug="e2e")
        skill = Skill.objects.create(name="Python", canonical_key="e2e-python", category="programming_language")
        role = CareerRole.objects.create(slug="e2e-backend", name="Backend Developer")
        RoleSkillBenchmark.objects.create(role=role, skill=skill, target_level="intermediate", priority="high", rationale="Core backend skill")
        content = "Learn Python, practise REST APIs, and build a tested backend project."
        KnowledgeDocument.objects.create(title="Backend Guide", role=role, topic="skills", content=content, status="published", checksum=checksum(content))
        registration = self.client.post("/api/v1/auth/register/", {"email": "demo@e2e.edu", "password": "Password123!", "institution_slug": "e2e", "role": "student"}, format="json")
        self.assertEqual(registration.status_code, 201)
        token = self.client.post("/api/v1/auth/token/", {"email": "demo@e2e.edu", "password": "Password123!", "institution_slug": "e2e"}, format="json")
        self.assertEqual(token.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
        self.assertEqual(self.client.patch("/api/v1/students/me/profile/", {"cgpa": "8.4", "aptitude_score": "80", "communication_rating": "7.5"}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/students/me/skills/", {"skill_id": str(skill.id), "proficiency": "beginner"}, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/v1/assessments/", {"type": "diagnostic", "scores": [{"dimension": "coding", "score": 80}, {"dimension": "logical", "score": 75}]}, format="json").status_code, 201)
        self.assertEqual(self.client.get("/api/v1/students/me/feature-snapshot/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/predictions/", {}, format="json").status_code, 201)
        self.assertEqual(self.client.get("/api/v1/careers/roles/e2e-backend/gap-analysis/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/careers/roles/e2e-backend/alignment/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/roadmaps/", {"role_slug": "e2e-backend"}, format="json").status_code, 201)
        copilot = self.client.post("/api/v1/copilot/ask/", {"question": "What should I improve for backend development?", "role_slug": "e2e-backend"}, format="json")
        self.assertEqual(copilot.status_code, 200)
        self.assertTrue(copilot.data["sources"])
        dashboard = self.client.get("/api/v1/dashboard/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIsNotNone(dashboard.data["prediction"])

    def test_student_can_import_single_profile_csv(self):
        institution = Institution.objects.create(name="CSV Demo", slug="csv-demo")
        user = User.objects.create_user(email="csv@demo.edu", password="Password123!", institution=institution, role=UserRole.STUDENT)
        self.client.force_authenticate(user)
        upload = SimpleUploadedFile("profile.csv", b"cgpa,aptitude_score,skills\n8.5,77,\n", content_type="text/csv")
        response = self.client.post("/api/v1/students/me/import-csv/", {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("cgpa", response.data["updated_profile_fields"])

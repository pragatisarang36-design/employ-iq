from rest_framework.test import APITestCase

from apps.accounts.models import Institution, User, UserRole
from apps.careers.models import CareerRole
from apps.rag.models import KnowledgeDocument
from apps.rag.services import checksum
from apps.students.models import StudentProfile


class CopilotApiTests(APITestCase):
    def setUp(self):
        institution = Institution.objects.create(name="Demo", slug="demo-rag")
        user = User.objects.create_user(email="student@demo.edu", password="Password123!", institution=institution, role=UserRole.STUDENT)
        StudentProfile.objects.create(user=user, institution=institution)
        self.role = CareerRole.objects.create(slug="data-analyst", name="Data Analyst")
        content = "Practice SQL joins and aggregations, then explain the business insight clearly."
        KnowledgeDocument.objects.create(title="SQL Interview Guide", role=self.role, topic="interviews", content=content, status="published", checksum=checksum(content))
        self.client.force_authenticate(user)

    def test_copilot_returns_grounded_citation_and_history(self):
        response = self.client.post("/api/v1/copilot/ask/", {"question": "How should I prepare for SQL interviews?", "role_slug": "data-analyst"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["citations"]), 1)
        self.assertIn("SQL Interview Guide", response.data["answer"])
        self.assertEqual(self.client.get("/api/v1/copilot/conversations/").status_code, 200)

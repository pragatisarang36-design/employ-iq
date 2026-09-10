from rest_framework.test import APITestCase

from apps.accounts.models import Institution, User, UserRole
from apps.careers.models import CareerRole, RoleSkillBenchmark
from apps.students.models import Skill, StudentProfile


class CareerApiTests(APITestCase):
    def setUp(self):
        institution = Institution.objects.create(name="Demo", slug="demo-careers")
        self.user = User.objects.create_user(email="student@demo.edu", password="Password123!", institution=institution, role=UserRole.STUDENT)
        StudentProfile.objects.create(user=self.user, institution=institution)
        self.role = CareerRole.objects.create(slug="data-analyst", name="Data Analyst")
        skill = Skill.objects.create(name="SQL", canonical_key="sql", category="database")
        RoleSkillBenchmark.objects.create(role=self.role, skill=skill, target_level="intermediate", priority="high")
        self.client.force_authenticate(self.user)

    def test_student_can_select_role_and_get_gap_analysis(self):
        self.assertEqual(self.client.get("/api/v1/careers/roles/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/careers/roles/data-analyst/select/").status_code, 200)
        response = self.client.get("/api/v1/careers/roles/data-analyst/gap-analysis/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["gaps"][0]["skill"], "SQL")

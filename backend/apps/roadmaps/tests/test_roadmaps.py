from rest_framework.test import APITestCase
from apps.accounts.models import Institution, User, UserRole
from apps.careers.models import CareerRole, RoleSkillBenchmark
from apps.students.models import Skill, StudentProfile

class RoadmapApiTests(APITestCase):
    def setUp(self):
        inst = Institution.objects.create(name="Demo", slug="demo-roadmap")
        user = User.objects.create_user(email="student@demo.edu", password="Password123!", institution=inst, role=UserRole.STUDENT)
        StudentProfile.objects.create(user=user, institution=inst)
        role = CareerRole.objects.create(slug="full-stack-developer", name="Full-Stack Developer")
        skill = Skill.objects.create(name="React", canonical_key="react", category="framework")
        RoleSkillBenchmark.objects.create(role=role, skill=skill, target_level="intermediate", priority="high")
        self.client.force_authenticate(user)
    def test_student_generates_and_updates_roadmap(self):
        response = self.client.post("/api/v1/roadmaps/", {"role_slug": "full-stack-developer"}, format="json")
        self.assertEqual(response.status_code, 201)
        item = response.data["items"][0]
        self.assertEqual(self.client.patch(f"/api/v1/roadmaps/{response.data['id']}/items/{item['id']}/", {"status": "completed"}, format="json").status_code, 200)

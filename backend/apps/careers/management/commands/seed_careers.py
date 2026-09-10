from django.core.management.base import BaseCommand

from apps.careers.models import CareerRole, RoleSkillBenchmark
from apps.students.models import Skill, StudentSkill


TRACKS = {
    "full-stack-developer": {"name": "Full-Stack Developer", "description": "Build web applications across frontend, backend, data, and deployment.", "skills": [("python", "Python", "programming_language", "intermediate", "high"), ("javascript", "JavaScript", "programming_language", "intermediate", "high"), ("react", "React", "framework", "intermediate", "high"), ("django", "Django", "framework", "intermediate", "high"), ("postgresql", "PostgreSQL", "database", "intermediate", "medium"), ("git", "Git", "cloud_devops", "intermediate", "medium")]},
    "data-analyst": {"name": "Data Analyst", "description": "Turn data into clear, actionable business insights.", "skills": [("python", "Python", "programming_language", "intermediate", "high"), ("sql", "SQL", "database", "intermediate", "high"), ("excel", "Excel", "soft_skill", "intermediate", "high"), ("statistics", "Statistics", "core_cs", "intermediate", "high"), ("power-bi", "Power BI", "framework", "beginner", "medium"), ("communication", "Communication", "soft_skill", "intermediate", "medium")]},
}


class Command(BaseCommand):
    help = "Seed the two fully supported EmployIQ career tracks."

    def handle(self, *args, **options):
        for slug, track in TRACKS.items():
            role, _ = CareerRole.objects.update_or_create(slug=slug, defaults={"name": track["name"], "description": track["description"], "support_level": CareerRole.SupportLevel.FULL})
            for key, name, category, target, priority in track["skills"]:
                skill, _ = Skill.objects.get_or_create(canonical_key=key, defaults={"name": name, "category": category})
                RoleSkillBenchmark.objects.update_or_create(role=role, skill=skill, defaults={"target_level": target, "priority": priority, "rationale": f"{name} is a core {role.name} capability."})
        self.stdout.write(self.style.SUCCESS("Career tracks seeded."))

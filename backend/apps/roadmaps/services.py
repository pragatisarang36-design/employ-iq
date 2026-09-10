from django.db import transaction

from apps.careers.models import CareerRole
from apps.careers.services import create_gap_analysis
from apps.students.models import Skill

from .models import Roadmap, RoadmapItem


@transaction.atomic
def generate_roadmap(*, student, role):
    gaps = create_gap_analysis(student=student, role=role)
    Roadmap.objects.filter(student=student, role=role, status=Roadmap.Status.ACTIVE).update(status=Roadmap.Status.COMPLETED)
    roadmap = Roadmap.objects.create(student=student, role=role, based_on_gap_snapshot=gaps)
    for sequence, gap in enumerate(gaps.gaps[:6], start=1):
        skill = Skill.objects.filter(id=gap["skill_id"]).first()
        RoadmapItem.objects.create(roadmap=roadmap, sequence=sequence, skill=skill, title=f"Build {gap['skill']} to {gap['target_level'].replace('_', ' ')}", description=f"Priority: {gap['priority']}. {gap['rationale']}")
    if not gaps.gaps:
        RoadmapItem.objects.create(roadmap=roadmap, sequence=1, title="Maintain your role-ready skill portfolio", description="Keep projects, interview practice, and evidence current.")
    return roadmap

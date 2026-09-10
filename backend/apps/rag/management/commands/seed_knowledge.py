from django.core.management.base import BaseCommand
from apps.careers.models import CareerRole
from apps.rag.models import KnowledgeDocument
from apps.rag.services import checksum

DOCS = [
 ("Full-Stack Developer Core Skills", "full-stack-developer", "skills", "Build confidence in JavaScript, React, Python, Django, PostgreSQL, and Git. Practice each skill by shipping small end-to-end features rather than watching tutorials only."),
 ("Full-Stack Project Ideas", "full-stack-developer", "projects", "Create a student placement tracker, expense manager, or team task board. Include authentication, validation, a relational database, tests, and deployment notes to demonstrate production thinking."),
 ("Full-Stack Interview Preparation", "full-stack-developer", "interviews", "Practice explaining request flow from React to Django to PostgreSQL. Prepare examples of debugging, API design, database indexing, and trade-offs in your own projects."),
 ("Full-Stack Learning Path", "full-stack-developer", "learning", "Start with JavaScript and React fundamentals, then build Django REST APIs and connect PostgreSQL. Use Git branches and concise README files for every project."),
 ("Data Analyst Core Skills", "data-analyst", "skills", "Develop practical SQL, Excel, statistics, Python, and dashboard skills. Focus on framing business questions, cleaning data, and communicating a clear conclusion."),
 ("Data Analyst Project Ideas", "data-analyst", "projects", "Build a sales dashboard, placement-outcome analysis, or customer churn exploration. State the question, document cleaning decisions, show visualizations, and recommend an action."),
 ("Data Analyst Interview Preparation", "data-analyst", "interviews", "Practice SQL joins, aggregations, window functions, descriptive statistics, and explaining a dashboard to a non-technical stakeholder. Be explicit about assumptions and data quality."),
 ("Data Analyst Learning Path", "data-analyst", "learning", "Begin with spreadsheets and SQL, add Python pandas for repeatable analysis, then learn Power BI or Tableau. Publish two compact portfolios with a question, method, finding, and recommendation."),
 ("Communication for Interviews", None, "communication", "Use a concise STAR structure: situation, task, action, result. Record a two-minute explanation of a project and replace jargon with the user problem, your contribution, and measurable outcome."),
 ("Study and Practice Habits", None, "study", "Choose one high-priority gap per week, practise in short focused blocks, and finish with a visible artifact such as a solved SQL set, Git commit, mock interview reflection, or project feature."),
]

class Command(BaseCommand):
    help = "Seed curated EmployIQ career guidance documents."
    def handle(self, *args, **options):
        for title, role_slug, topic, content in DOCS:
            role = CareerRole.objects.filter(slug=role_slug).first() if role_slug else None
            KnowledgeDocument.objects.update_or_create(title=title, defaults={"role": role, "topic": topic, "content": content, "source_type": "curated", "status": KnowledgeDocument.Status.PUBLISHED, "version": "v1", "checksum": checksum(content)})
        self.stdout.write(self.style.SUCCESS("Curated knowledge base seeded."))

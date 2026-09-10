import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Institution, User, UserRole
from apps.students.models import (
    Skill,
    StudentCertification,
    StudentExperience,
    StudentProfile,
    StudentSkill,
)


class StudentModelTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="IIT Delhi", slug="iitd")
        self.user = User.objects.create_user(
            email="arjun@iitd.ac.in",
            password="StrongPassword123!",
            institution=self.institution,
            role=UserRole.STUDENT,
        )
        self.skill_python = Skill.objects.create(
            name="Python",
            category=Skill.Category.PROGRAMMING_LANGUAGE,
            canonical_key="python",
        )
        self.skill_react = Skill.objects.create(
            name="React",
            category=Skill.Category.FRAMEWORK,
            canonical_key="react",
        )

    def test_skill_creation_and_uniqueness(self):
        self.assertEqual(str(self.skill_python), "Python (programming_language)")
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Skill.objects.create(
                    name="Python 3",
                    category=Skill.Category.PROGRAMMING_LANGUAGE,
                    canonical_key="python",  # Duplicate canonical_key
                )

    def test_student_profile_creation(self):
        profile = StudentProfile.objects.create(
            user=self.user,
            institution=self.institution,
            cohort="2022-2026",
            department="Computer Science",
            cgpa=Decimal("8.75"),
            tenth_percentage=Decimal("92.50"),
            twelfth_percentage=Decimal("89.00"),
            current_backlogs=0,
            history_of_backlogs=0,
        )
        self.assertTrue(isinstance(profile.id, uuid.UUID))
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.institution, self.institution)
        self.assertEqual(profile.cgpa, Decimal("8.75"))

    def test_student_profile_validation(self):
        # Invalid CGPA (> 10)
        profile = StudentProfile(
            user=self.user,
            institution=self.institution,
            cgpa=Decimal("11.5"),
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_student_skill_unique_constraint(self):
        profile = StudentProfile.objects.create(
            user=self.user,
            institution=self.institution,
        )
        StudentSkill.objects.create(
            student=profile,
            skill=self.skill_python,
            proficiency=StudentSkill.Proficiency.ADVANCED,
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                StudentSkill.objects.create(
                    student=profile,
                    skill=self.skill_python,  # Duplicate skill for same student
                    proficiency=StudentSkill.Proficiency.INTERMEDIATE,
                )

    def test_student_certification_and_experience(self):
        profile = StudentProfile.objects.create(
            user=self.user,
            institution=self.institution,
        )
        cert = StudentCertification.objects.create(
            student=profile,
            name="AWS Certified Cloud Practitioner",
            issuer="Amazon Web Services",
        )
        self.assertEqual(cert.name, "AWS Certified Cloud Practitioner")

        exp = StudentExperience.objects.create(
            student=profile,
            kind=StudentExperience.Kind.INTERNSHIP,
            title="Backend Engineering Intern",
            complexity=StudentExperience.Complexity.HIGH,
            duration_months=3,
            metadata={"tech_stack": ["Python", "Django", "PostgreSQL"]},
        )
        self.assertEqual(exp.duration_months, 3)
        self.assertIn("tech_stack", exp.metadata)

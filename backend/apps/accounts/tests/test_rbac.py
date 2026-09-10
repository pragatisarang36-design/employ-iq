from django.test import RequestFactory, TestCase

from apps.accounts.models import Institution, User, UserRole
from apps.accounts.permissions import (
    IsAdmin,
    IsSameInstitution,
    IsSelfOrAuthorizedStaff,
    IsStudent,
    IsTPO,
    IsTPOOrAdmin,
)


class RBACTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.inst1 = Institution.objects.create(name="Alpha University", slug="alpha")
        self.inst2 = Institution.objects.create(name="Beta Institute", slug="beta")

        self.student1 = User.objects.create_user(
            email="student1@alpha.edu",
            password="pass",
            institution=self.inst1,
            role=UserRole.STUDENT,
        )
        self.student2 = User.objects.create_user(
            email="student2@beta.edu",
            password="pass",
            institution=self.inst2,
            role=UserRole.STUDENT,
        )
        self.tpo1 = User.objects.create_user(
            email="tpo1@alpha.edu",
            password="pass",
            institution=self.inst1,
            role=UserRole.TPO,
        )
        self.tpo2 = User.objects.create_user(
            email="tpo2@beta.edu",
            password="pass",
            institution=self.inst2,
            role=UserRole.TPO,
        )
        self.admin1 = User.objects.create_user(
            email="admin1@alpha.edu",
            password="pass",
            institution=self.inst1,
            role=UserRole.ADMIN,
        )

    def test_role_permissions(self):
        perm_student = IsStudent()
        perm_tpo = IsTPO()
        perm_admin = IsAdmin()
        perm_tpo_or_admin = IsTPOOrAdmin()

        # Student request
        req = self.factory.get("/")
        req.user = self.student1
        self.assertTrue(perm_student.has_permission(req, None))
        self.assertFalse(perm_tpo.has_permission(req, None))
        self.assertFalse(perm_admin.has_permission(req, None))
        self.assertFalse(perm_tpo_or_admin.has_permission(req, None))

        # TPO request
        req.user = self.tpo1
        self.assertFalse(perm_student.has_permission(req, None))
        self.assertTrue(perm_tpo.has_permission(req, None))
        self.assertFalse(perm_admin.has_permission(req, None))
        self.assertTrue(perm_tpo_or_admin.has_permission(req, None))

        # Admin request
        req.user = self.admin1
        self.assertFalse(perm_student.has_permission(req, None))
        self.assertFalse(perm_tpo.has_permission(req, None))
        self.assertTrue(perm_admin.has_permission(req, None))
        self.assertTrue(perm_tpo_or_admin.has_permission(req, None))

    def test_same_institution_isolation(self):
        perm = IsSameInstitution()

        req = self.factory.get("/")
        req.user = self.student1

        # Same institution object
        self.assertTrue(perm.has_object_permission(req, None, self.inst1))
        self.assertTrue(perm.has_object_permission(req, None, self.tpo1))

        # Different institution object
        self.assertFalse(perm.has_object_permission(req, None, self.inst2))
        self.assertFalse(perm.has_object_permission(req, None, self.student2))

    def test_self_or_authorized_staff_permission(self):
        perm = IsSelfOrAuthorizedStaff()

        req = self.factory.get("/")

        # Student accessing own user record
        req.user = self.student1
        self.assertTrue(perm.has_object_permission(req, None, self.student1))

        # Student attempting to access another student's record
        self.assertFalse(perm.has_object_permission(req, None, self.student2))

        # TPO from same institution accessing student record
        req.user = self.tpo1
        self.assertTrue(perm.has_object_permission(req, None, self.student1))

        # TPO from different institution accessing student record (Tenant Isolation breach attempt)
        req.user = self.tpo2
        self.assertFalse(perm.has_object_permission(req, None, self.student1))

    def test_unauthenticated_and_anonymous_rbac(self):
        from django.contrib.auth.models import AnonymousUser

        req = self.factory.get("/")
        req.user = AnonymousUser()

        self.assertFalse(IsStudent().has_permission(req, None))
        self.assertFalse(IsTPO().has_permission(req, None))
        self.assertFalse(IsAdmin().has_permission(req, None))
        self.assertFalse(IsTPOOrAdmin().has_permission(req, None))
        self.assertFalse(IsSameInstitution().has_object_permission(req, None, self.inst1))
        self.assertFalse(IsSelfOrAuthorizedStaff().has_object_permission(req, None, self.student1))


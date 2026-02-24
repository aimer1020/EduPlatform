from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from users.models import User, Teacher, Student
from courses.models.course_models import Course, Education
from courses.models.interactionCourse_models import Enrollment
from users.permissions import (
    IsTeacherOwnerOrReadOnly,
    IsEnrollmentOwner,
    IsStudentEnrolledOrReadOnly,
)
import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


class PermissionTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

        education = Education.objects.create(country="Egypt", country_code="EGY")
        file_io = io.BytesIO()
        image = Image.new("RGB", (300, 300), color="white")
        image.save(file_io, "JPEG")
        file_io.seek(0)

        # 2. تحويلها لملف يفهمه ديجانجو (SimpleUploadedFile)
        temp_img = SimpleUploadedFile(
            name="test_course_image.jpg",
            content=file_io.read(),
            content_type="image/jpeg",
        )
        # Create users
        self.admin_user = User.objects.create_user(
            username="admin", user_type="admin", is_staff=True, is_superuser=True
        )
        self.teacher_user = User.objects.create_user(
            username="teacher1", user_type="teacher"
        )
        self.other_teacher_user = User.objects.create_user(
            username="teacher2", user_type="teacher"
        )
        self.student_user = User.objects.create_user(
            username="student1", user_type="student"
        )
        self.other_student_user = User.objects.create_user(
            username="student2", user_type="student"
        )

        # Create teacher profiles
        self.teacher = Teacher.objects.create(user=self.teacher_user, is_verified=True)
        self.other_teacher = Teacher.objects.create(
            user=self.other_teacher_user, is_verified=True
        )

        # Create student profiles
        self.student = Student.objects.create(
            user=self.student_user, phone="01234567890", parent_phone="01012345678"
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            phone="01012345676",
            parent_phone="01122334455",
        )

        # Create course
        self.course = Course.objects.create(
            teacher=self.teacher,
            education=education,
            title="Test Course",
            description="Test Description",
            price=100.00,
            course_img=temp_img,
            is_published=True,
        )

        # Create enrollment
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status="active",
            price_paid=100.00,
            original_price=100.00,
            payment_method="credit_card",
        )

    def test_is_teacher_owner_or_read_only(self):
        permission = IsTeacherOwnerOrReadOnly()

        # Test with owner teacher (Success)
        request = self.factory.get("/")
        force_authenticate(request, user=self.teacher_user)
        request.user = self.teacher_user  # Ensure the user is set correctly
        self.assertTrue(permission.has_object_permission(request, None, self.course))

        # Test with a different teacher (Fail)
        request = self.factory.put("/")
        force_authenticate(request, user=self.other_teacher_user)
        request.user = self.other_teacher_user
        self.assertFalse(permission.has_object_permission(request, None, self.course))

        # Test with an admin (Success)
        request = self.factory.get("/")
        force_authenticate(request, user=self.admin_user)
        request.user = self.admin_user
        self.assertTrue(permission.has_object_permission(request, None, self.course))

    def test_is_enrollment_owner(self):
        permission = IsEnrollmentOwner()

        # Test with the student who owns the enrollment (Success)
        request = self.factory.get("/")
        force_authenticate(request, user=self.student_user)
        request.user = self.student_user  # Ensure the user is set correctly
        self.assertTrue(
            permission.has_object_permission(request, None, self.enrollment)
        )

        # Test with a different student (Fail)
        request = self.factory.put("/")
        force_authenticate(request, user=self.other_student_user)
        request.user = self.other_student_user
        self.assertFalse(
            permission.has_object_permission(request, None, self.enrollment)
        )

        # Test with the course teacher (Success)
        request = self.factory.get("/")
        force_authenticate(request, user=self.teacher_user)
        request.user = self.teacher_user
        self.assertTrue(
            permission.has_object_permission(request, None, self.enrollment)
        )

    def test_is_student_enrolled_or_read_only(self):
        permission = IsStudentEnrolledOrReadOnly()

        # Test with an enrolled student (Success)
        request = self.factory.get("/")
        force_authenticate(request, user=self.student_user)
        request.user = self.student_user
        self.assertTrue(permission.has_object_permission(request, None, self.course))

        # Test with a non-enrolled student (Fail)
        request = self.factory.put("/")
        force_authenticate(request, user=self.other_student_user)
        request.user = self.other_student_user
        self.assertFalse(permission.has_object_permission(request, None, self.course))

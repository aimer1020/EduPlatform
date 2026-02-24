from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from users.models import Teacher, Student

User = get_user_model()


class UserModelTest(TestCase):

    def test_user_creation(self):
        user = User.objects.create_user(
            username="testuser", password="password123", user_type="teacher"
        )
        user.full_clean()
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("password123"))

    def test_is_staff_logic(self):
        user = User.objects.create_user(
            username="staffuser", password="password123", is_staff=True
        )
        user.full_clean()
        self.assertTrue(user.is_staff)

    def test_invalid_user_type(self):
        with self.assertRaises(ValidationError):
            user = User(username="invaliduser", user_type="invalid")
            user.full_clean()


class TeacherModelTest(TestCase):

    def setUp(self):
        self.teacher_user = User.objects.create(
            username="teacheruser", password="password123", user_type="teacher"
        )
        self.teacher_user.save()

    def test_teacher_creation(self):
        self.assertEqual(self.teacher_user.user_type, "teacher")
        teacher = Teacher(user=self.teacher_user, is_verified=True)
        teacher.full_clean()
        teacher.save()
        self.assertEqual(teacher.user, self.teacher_user)
        self.assertTrue(teacher.is_verified)

    def test_teacher_creation_invalid_user_type(self):
        student_user = get_user_model().objects.create(
            username="studentuser", password="password123", user_type="student"
        )
        student_user.save()

        with self.assertRaises(ValidationError):
            teacher = Teacher(user=student_user, is_verified=True)
            teacher.full_clean()


class StudentModelTest(TestCase):

    def setUp(self):
        self.student_user = User.objects.create_user(
            username="studentuser", password="password123", user_type="student"
        )

    def test_student_creation(self):
        student = Student.objects.create(
            user=self.student_user,
            academic_year=2,
            phone="01012345678",
            parent_phone="01098765432",
            parent_name="Parent Name",
        )
        student.full_clean()
        student.save()
        self.assertEqual(student.user, self.student_user)
        self.assertEqual(student.academic_year, 2)

    def test_student_creation_invalid_user_type(self):
        teacher_user = User.objects.create_user(
            username="teacheruser", password="password123", user_type="teacher"
        )

        with self.assertRaises(ValidationError):
            student = Student(
                user=teacher_user,
                academic_year=2,
                phone="01012345678",
                parent_phone="01098765432",
            )
            student.full_clean()

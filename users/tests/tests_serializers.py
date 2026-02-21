from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from users.models import User, Teacher, Student
from users.serializers import teacherCreateUpdateSerializer, StudentCreateUpdateSerializer

class TeacherSerializerTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")
        self.teacher_user = User.objects.create_user(username="teacher1", password="password123", user_type="teacher")
        self.teacher = Teacher.objects.create(user=self.teacher_user, is_verified=True)

    def test_create_teacher(self):
        data = {
            "user_info": {
                "username": "new_teacher",
                "password": "newpassword123",
                "email": "new_teacher@example.com",
                "first_name": "New",
                "last_name": "Teacher",
                "user_type": "teacher"
            },
            "subject": None,
            "experience_years": 5
        }
        serializer = teacherCreateUpdateSerializer(data=data, context={"request": self.client})
        self.assertTrue(serializer.is_valid())
        teacher = serializer.save()
        self.assertEqual(teacher.user.username, data["user_info"]["username"])
        self.assertTrue(check_password(data["user_info"]["password"], teacher.user.password))

    def test_update_teacher(self):
        data = {
            "user_info": {
                "username": "updated_teacher",
                "email": "updated_teacher@example.com",
                "first_name": "Updated",
                "last_name": "Teacher"
            },
            "experience_years": 10
        }
        serializer = teacherCreateUpdateSerializer(instance=self.teacher, data=data, partial=True, context={"request": self.client})
        self.assertTrue(serializer.is_valid())
        teacher = serializer.save()
        self.assertEqual(teacher.user.username, data["user_info"]["username"])
        self.assertEqual(teacher.experience_years, data["experience_years"])

    def test_user_type_read_only(self):
        data = {
            "user_info": {
                "user_type": "student"
            }
        }
        serializer = teacherCreateUpdateSerializer(instance=self.teacher, data=data, partial=True, context={"request": self.client})
        self.assertTrue(serializer.is_valid())
        teacher = serializer.save()
        self.assertEqual(teacher.user.user_type, "teacher")  # user_type should not change

    def test_invalid_data(self):
        data = {
            "user_info": {
                "username": "",
                "password": "short",
                "email": "invalid_email",
                "first_name": "",
                "last_name": ""
            },
            "experience_years": -1
        }
        serializer = teacherCreateUpdateSerializer(data=data, context={"request": self.client})
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_info", serializer.errors)
        self.assertIn("experience_years", serializer.errors)

class StudentSerializerTests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(username="student1", password="password123", user_type="student")
        self.student = Student.objects.create(user=self.student_user, grade_level="10th")

    def test_create_student(self):
        data = {
            "user_info": {
                "username": "new_student",
                "password": "newpassword123",
                "email": "new_student@example.com",
                "first_name": "New",
                "last_name": "Student",
                "user_type": "student"
            },
            "grade_level": "9th"
        }
        serializer = StudentCreateUpdateSerializer(data=data, context={"request": self.client})
        self.assertTrue(serializer.is_valid())
        student = serializer.save()
        self.assertEqual(student.user.username, data["user_info"]["username"])
        self.assertTrue(check_password(data["user_info"]["password"], student.user.password))

    def test_update_student(self):
        data = {
            "user_info": {
                "username": "updated_student",
                "email": "updated_student@example.com",
                "first_name": "Updated",
                "last_name": "Student"
            },
            "grade_level": "11th"
        }
        serializer = StudentCreateUpdateSerializer(instance=self.student, data=data, partial=True, context={"request": self.client})
        self.assertTrue(serializer.is_valid())
        student = serializer.save()
        self.assertEqual(student.user.username, data["user_info"]["username"])
        self.assertEqual(student.grade_level, data["grade_level"])

    def test_user_type_read_only(self):
        data = {
            "user_info": {
                "user_type": "teacher"
            }
        }
        serializer = StudentCreateUpdateSerializer(instance=self.student, data=data, partial=True, context={"request": self.client})
        self.assertTrue(serializer.is_valid())
        student = serializer.save()
        self.assertEqual(student.user.user_type, "student")  # user_type should not change

    def test_invalid_data(self):
        data = {
            "user_info": {
                "username": "",
                "password": "short",
                "email": "invalid_email",
                "first_name": "",
                "last_name": ""
            },
            "grade_level": ""
        }
        serializer = StudentCreateUpdateSerializer(data=data, context={"request": self.client})
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_info", serializer.errors)
        self.assertIn("grade_level", serializer.errors)
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, Teacher, Student

class TeacherViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")
        self.teacher_user = User.objects.create_user(username="teacher1", password="password123", user_type="teacher")
        self.teacher = Teacher.objects.create(user=self.teacher_user, is_verified=True)

    def test_admin_can_create_teacher(self):
        self.client.force_authenticate(user=self.admin_user)
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
        url = reverse("teacher-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_admin_cannot_create_teacher(self):
        self.client.force_authenticate(user=self.teacher_user)
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
        url = reverse("teacher-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_only_access_own_profile(self):
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse("teacher-detail", kwargs={"pk": self.teacher.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.teacher.id)

    def test_teacher_cannot_access_other_profiles(self):
        other_teacher_user = User.objects.create_user(username="teacher2", password="password123", user_type="teacher")
        other_teacher = Teacher.objects.create(user=other_teacher_user, is_verified=True)
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse("teacher-detail", kwargs={"pk": other_teacher.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class StudentViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.student_user = User.objects.create_user(username="student1", password="password123", user_type="student")
        self.student = Student.objects.create(user=self.student_user, academic_year="10", phone='01234567890', parent_phone='01234567891')

    def test_student_can_access_own_profile(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse("student-detail", kwargs={"pk": self.student.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.student.id)

    def test_student_cannot_access_other_profiles(self):
        other_student_user = User.objects.create_user(username="student2", password="password123", user_type="student")
        other_student = Student.objects.create(user=other_student_user, academic_year="8", phone='01234567892', parent_phone='01234567893')
        self.client.force_authenticate(user=self.student_user)
        url = reverse("student-detail", kwargs={"pk": other_student.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_can_create_student(self):
        data = {
            "user_info": {
                "username": "new_student",
                "password": "newpassword123",
                "email": "new_student@example.com",
                "first_name": "New",
                "last_name": "Student",
            },
            "academic_year": 5,
            "phone": "01234567890",
            "parent_phone": "01234567891"
        }
        url = reverse("student-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_anonymous_user_cannot_create_teacher(self):
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
        url = reverse("teacher-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_list_only_own_profile(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse("student-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.student.id)


from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from users.models import User, Teacher, Student
from users.serializers import teacherCreateUpdateSerializer, StudentCreateUpdateSerializer
from rest_framework.authtoken.models import Token

class TeacherSerializerTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")
        self.teacher_user = User.objects.create_user(username="teacher1", password="password123", user_type="teacher")
        self.teacher = Teacher.objects.create(user=self.teacher_user, is_verified=True)

    def test_create_teacher(self):
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = self.admin_user
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
        serializer = teacherCreateUpdateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())
        teacher = serializer.save()
        self.assertEqual(teacher.user.username, data["user_info"]["username"])
        self.assertTrue(check_password(data["user_info"]["password"], teacher.user.password))

    def test_update_teacher(self):
        factory = APIRequestFactory()
    
        request = factory.patch('/')
        request.user = self.teacher_user

        data = {
            "user_info": {
                "username": "updated_teacher",
                "email": "updated_teacher@example.com",
                "first_name": "Updated",
                "last_name": "Teacher"
            },
            "experience_years": 10
        }
        serializer = teacherCreateUpdateSerializer(
            instance=self.teacher, 
            data=data, 
            partial=True, 
            context={"request": request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors) 
        teacher = serializer.save()
        self.assertEqual(teacher.user.username, data["user_info"]["username"])
        self.assertEqual(teacher.experience_years, data["experience_years"])

    def test_user_type_read_only(self):
        factory = APIRequestFactory()
        request = factory.patch('/') 
        request.user = self.teacher_user
        data = {
        "user_info": {"user_type": "admin"}
        }
        serializer = teacherCreateUpdateSerializer(
        instance=self.teacher, 
        data=data, 
        partial=True, 
        context={"request": request} 
        )
        self.assertTrue(serializer.is_valid())
        teacher = serializer.save()
        self.assertEqual(teacher.user.user_type, "teacher")  

    def test_invalid_data(self):
        factory = APIRequestFactory()
    
        request = factory.patch('/')
        request.user = self.teacher_user
        
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
        serializer = teacherCreateUpdateSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_info", serializer.errors)
        self.assertIn("experience_years", serializer.errors)

class StudentSerializerTests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(username="student1", password="password123", user_type="student")
        self.student = Student.objects.create(user=self.student_user, academic_year=3, phone='01234557890', parent_phone='01234547891')

    def test_create_student(self):
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = self.student_user
        data = {
            "user_info": {
                "username": "new_student",
                "password": "newpassword123",
                "email": "new_student@example.com",
                "first_name": "New",
                "last_name": "Student",
                },
            "academic_year": 9,
            "phone": "01234567890",
            "parent_phone": "01234567891"
        }
        serializer = StudentCreateUpdateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())
        student = serializer.save()
        self.assertEqual(student.user.username, data["user_info"]["username"])
        self.assertTrue(check_password(data["user_info"]["password"], student.user.password))

    def test_update_student(self):
        factory = APIRequestFactory()
        request = factory.patch('/')
        request.user = self.student_user
        data = {
            "user_info": {
                "username": "updated_student",
                "email": "updated_student@example.com",
                "first_name": "Updated",
                "last_name": "Student"
            },
            "academic_year": 7
        }
        serializer = StudentCreateUpdateSerializer(instance=self.student, data=data, partial=True, context={"request": request})
        self.assertTrue(serializer.is_valid())
        student = serializer.save()
        self.assertEqual(student.user.username, data["user_info"]["username"])
        self.assertEqual(student.academic_year, data["academic_year"])

    def test_user_type_read_only(self):
        factory = APIRequestFactory()
        request = factory.patch('/')
        request.user = self.student_user
        data = {
            "user_info": {
                "user_type": "teacher"
            }
        }
        serializer = StudentCreateUpdateSerializer(instance=self.student, data=data, partial=True, context={"request": request})
        self.assertTrue(serializer.is_valid())
        student = serializer.save()
        self.assertEqual(student.user.user_type, "student")  # user_type should not change

    def test_invalid_data(self):
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = self.student_user
        data = {
            "user_info": {
                "username": "",
                "password": "short",
                "email": "invalid_email",
                "first_name": "",
                "last_name": ""
            },
            "academic_year": ""
        }
        serializer = StudentCreateUpdateSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_info", serializer.errors)
        self.assertIn("academic_year", serializer.errors)


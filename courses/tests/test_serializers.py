from rest_framework import serializers
from rest_framework.test import APITestCase
from ..models.course_models import Course, Education, Subject
from ..Serializers.course_serializers import CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer
from users.models import Teacher, User

class CourseSerializerTests(APITestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username="teacher1", password="password123", user_type="teacher")
        self.user2 = User.objects.create_user(username="teacher2", password="password123", user_type="teacher")
        self.student = User.objects.create_user(username="student", password="password123", user_type="student")

        # Create teacher profiles
        self.teacher1 = Teacher.objects.create(user=self.user1, is_verified=True)
        self.teacher2 = Teacher.objects.create(user=self.user2, is_verified=True)

        # Create education and subject
        self.education = Education.objects.create(country="Egypt", country_code="EGY")
        self.subject = Subject.objects.create(name="Mathematics", code="MATH")

        # Create courses
        self.course1 = Course.objects.create(
            title="Course 1",
            description="Description 1",
            price=100,
            teacher=self.teacher1,
            education=self.education,
            subject=self.subject,
            is_published=True
        )

    def test_course_list_serializer(self):
        serializer = CourseListSerializer(self.course1)
        self.assertEqual(serializer.data["title"], self.course1.title)
        self.assertEqual(serializer.data["price"], "100.00")
        self.assertEqual(serializer.data["teacher_name"], self.user1.get_full_name())

    def test_course_detail_serializer(self):
        serializer = CourseDetailSerializer(self.course1)
        self.assertEqual(serializer.data["title"], self.course1.title)
        self.assertEqual(serializer.data["price"], "100.00")
        self.assertEqual(serializer.data["teacher_info"], {
            "name": str(self.teacher1),
            "experience_years": self.teacher1.experience_years
        })

    def test_course_create_update_serializer(self):
        data = {
            "title": "New Course",
            "description": "New course description",
            "price": 150,
            "education": self.education.id,
            "subject": self.subject.id,
            "is_published": True,
            "is_active": True
        }
        request = self.client
        request.user = self.user1  # Set the user in the request context
        serializer = CourseCreateUpdateSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid())
        course = serializer.save(teacher=self.teacher1)
        self.assertEqual(course.title, data["title"])
        self.assertEqual(course.price, data["price"])
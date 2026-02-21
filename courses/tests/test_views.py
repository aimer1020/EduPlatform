from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from courses.models.course_models import Course
from users.models import Teacher
from courses.Serializers.course_serializers import CourseListSerializer, CourseDetailSerializer
from django.urls import reverse

User = get_user_model()

class CourseViewSetTests(APITestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username="teacher1", password="password123", user_type="teacher")
        self.user2 = User.objects.create_user(username="teacher2", password="password123", user_type="teacher")
        self.student = User.objects.create_user(username="student", password="password123", user_type="student")

        # Create teacher profiles
        self.teacher1 = Teacher.objects.create(user=self.user1)
        self.teacher2 = Teacher.objects.create(user=self.user2)

        # Create courses
        self.course1 = Course.objects.create(
            title="Course 1",
            description="Description 1",
            price=100,
            teacher=self.teacher1,
            is_published=True
        )
        self.course2 = Course.objects.create(
            title="Course 2",
            description="Description 2",
            price=200,
            teacher=self.teacher1,
            is_published=False
        )

        # Initialize API client
        self.client = APIClient()

    def test_list_permissions_allow_any(self):
        url = reverse("course-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_permissions_allow_any(self):
        url = reverse("course-detail", kwargs={"pk": self.course1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_permissions_authenticated(self):
        url = reverse("course-list")
        # Unauthenticated user
        response = self.client.post(url, {
            "title": "New Course",
            "description": "New course description",
            "price": 50
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Ensure unauthenticated users get 403

        # Authenticated user
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, {
            "title": "New Course",
            "description": "New course description",
            "price": 50
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_permissions_owner_only(self):
        url = reverse("course-detail", kwargs={"pk": self.course1.id})
        self.client.force_authenticate(user=self.user2)
        response = self.client.put(url, {
            "title": "Updated Title"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user1)
        response = self.client.put(url , {
            "title": "Updated Title",
            "description": "Updated Description",
            "price": 150
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, "Updated Title")
        self.assertEqual(self.course1.description, "Updated Description")
        self.assertEqual(self.course1.price, 150)

    def test_delete_permissions_owner_only(self):
        
        url = reverse("course-detail", kwargs={"pk": self.course1.id})
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_serializer_logic(self):
        url = reverse("course-list")
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].keys(), CourseListSerializer(self.course1).data.keys())

    def test_retrieve_serializer_logic(self):
        url = reverse("course-detail", kwargs={"pk": self.course1.id})
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.keys(), CourseDetailSerializer(self.course1).data.keys())

    def test_queryset_filtering(self):
        url = reverse("course-list")
        # Anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only published courses

        # Authenticated teacher
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # All courses for the teacher

    def test_perform_create_teacher_assignment(self):
        url = reverse("course-list")
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, {
            "title": "New Course",
            "description": "New course description",
            "price": 50,
            "teacher": self.teacher2.id  # Attempt to override teacher
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["teacher"], self.teacher1.id)  # Ensure teacher1 is set

    def test_search_filter(self):
        url = reverse("course-list")
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url + "?search=Course 1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure only one course matches the search query
        matching_courses = [course for course in response.data if "Course 1" in course["title"]]
        self.assertEqual(len(matching_courses), 1)
        self.assertEqual(matching_courses[0]["title"], "Course 1")

    def test_ordering_filter(self):
        url = reverse("course-list")
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url + "?ordering=-price")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the courses are ordered by price in descending order
        prices = [course["price"] for course in response.data]
        self.assertEqual(prices, ["200.00", "100.00"])

    def test_partial_update(self):
        url = reverse("course-detail", kwargs={"pk": self.course1.id})
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(url, {
            "title": "Partially Updated Title"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, "Partially Updated Title")

    def test_update_nonexistent_course(self):
        url = reverse("course-detail", kwargs={"pk": 9999})
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(url, {
            "title": "Nonexistent Course"
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
from django.test import TestCase
from courses.models.course_models import Course, Subject, Education
from users.models import Teacher, Student
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image

User = get_user_model()


class EducationModelTest(TestCase):

    def setUp(self):
        self.education = Education.objects.create(
            country="Egypt", country_code="EGY", currency="EGP", is_active=True
        )

    def test_education_creation(self):
        self.assertEqual(str(self.education), "Egypt")
        self.assertTrue(self.education.is_active)

    def test_soft_delete(self):
        self.education.soft_delete()
        self.assertFalse(self.education.is_active)
        self.assertIsNotNone(self.education.deleted_at)
        self.assertTrue(Education.objects.filter(pk=self.education.pk).exists())


class SubjectModelTest(TestCase):

    def setUp(self):
        self.subject = Subject.objects.create(
            name="Mathematics", code="MATH", is_active=True
        )

    def test_subject_creation(self):
        self.assertEqual(str(self.subject), "Mathematics")
        self.assertTrue(self.subject.is_active)


class CourseModelTest(TestCase):

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username="teacheruser", password="password123", user_type="teacher"
        )
        self.teacher_user.save()

        self.teacher = Teacher.objects.create(user=self.teacher_user, is_verified=True)

        self.student_user = User.objects.create_user(
            username="studentuser", password="password123", user_type="student"
        )
        self.student_user.save()

        self.education = Education.objects.create(
            country="Egypt", country_code="EGY", currency="EGP", is_active=True
        )

        self.subject = Subject.objects.create(
            name="Mathematics", code="MATH", is_active=True
        )

        # Create a dummy image file with updated dimensions
        file_io = io.BytesIO()
        image = Image.new("RGB", (300, 300), color="white")
        image.save(file_io, "JPEG")
        file_io.seek(0)
        temp_img = SimpleUploadedFile(
            name="test_image.jpg", content=file_io.read(), content_type="image/jpeg"
        )

        self.course = Course.objects.create(
            teacher=self.teacher,
            education=self.education,
            subject=self.subject,
            title="Algebra 101",
            description="This is a test course description.",
            course_img=temp_img,
            price=100.00,
        )

    def test_course_creation(self):
        self.assertEqual(str(self.course), "Algebra 101")
        self.assertTrue(self.course.is_active)
        self.assertFalse(self.course.is_published)

    def test_clean_method_teacher_verification(self):
        unverified_teacher_user = User.objects.create_user(
            username="unverifiedteacher", password="password123", user_type="teacher"
        )
        unverified_teacher_user.save()

        unverified_teacher = Teacher.objects.create(
            user=unverified_teacher_user, is_verified=False
        )

        file_io = io.BytesIO()
        image = Image.new("RGB", (100, 100), color="white")
        image.save(file_io, "JPEG")
        file_io.seek(0)
        temp_img = SimpleUploadedFile(
            name="test_image.jpg", content=file_io.read(), content_type="image/jpeg"
        )

        course = Course(
            teacher=unverified_teacher,
            education=self.education,
            subject=self.subject,
            title="Geometry 101",
            description="This is a test course description.",
            course_img=temp_img,
            price=100.00,
        )
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_clean_method_inactive_education(self):
        self.education.is_active = False
        self.education.save()

        file_io = io.BytesIO()
        image = Image.new("RGB", (300, 300), color="white")
        image.save(file_io, "JPEG")
        file_io.seek(0)
        temp_img = SimpleUploadedFile(
            name="test_image.jpg", content=file_io.read(), content_type="image/jpeg"
        )

        course = Course(
            teacher=self.teacher,
            education=self.education,
            subject=self.subject,
            title="Geometry 101",
            description="This is a test course description.",
            course_img=temp_img,
            price=100.00,
        )
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_clean_method_image_dimensions(self):
        file_io = io.BytesIO()
        image = Image.new("RGB", (100, 100), color="white")
        image.save(file_io, "JPEG")
        file_io.seek(0)
        temp_img = SimpleUploadedFile(
            name="test_image.jpg", content=file_io.read(), content_type="image/jpeg"
        )

        course = Course(
            teacher=self.teacher,
            education=self.education,
            subject=self.subject,
            title="Geometry 101",
            description="This is a test course description.",
            course_img=temp_img,
            price=100.00,
        )
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_clean_method_price_validation(self):
        file_io = io.BytesIO()
        image = Image.new("RGB", (100, 100), color="white")
        image.save(file_io, "JPEG")
        file_io.seek(0)
        temp_img = SimpleUploadedFile(
            name="test_image.jpg", content=file_io.read(), content_type="image/jpeg"
        )

        course = Course(
            teacher=self.teacher,
            education=self.education,
            subject=self.subject,
            title="Geometry 101",
            description="This is a test course description.",
            course_img=temp_img,
            price=0.00,
        )
        with self.assertRaises(ValidationError):
            course.full_clean()

    def test_soft_delete(self):
        self.course.soft_delete()
        self.assertFalse(self.course.is_active)
        self.assertFalse(self.course.is_published)
        self.assertIsNotNone(self.course.deleted_at)
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    def test_publish_method(self):
        self.course.publish()
        self.assertTrue(self.course.is_published)
        self.assertIsNotNone(self.course.published_at)

    def test_unpublish_method(self):
        self.course.publish()
        self.course.unpublish()
        self.assertFalse(self.course.is_published)

    def test_activate_method(self):
        self.course.is_active = False
        self.course.save()
        self.course.activate()
        self.assertTrue(self.course.is_active)

    def test_deactivate_method(self):
        self.course.deactivate()
        self.assertFalse(self.course.is_active)

    def test_can_enroll(self):
        student = Student.objects.create(
            user=self.student_user,
            academic_year=2,
            phone="01012345678",
            parent_phone="01098765432",
            parent_name="Parent Name",
        )
        self.course.publish()
        self.course.is_active = True
        self.course.save()
        can_enroll, reason = self.course.can_enroll(student)
        self.assertTrue(can_enroll)

        self.course.is_active = False
        self.course.save()
        can_enroll, reason = self.course.can_enroll(student)
        self.assertFalse(can_enroll)
        self.assertEqual(reason, "Course is not currently active")

    def test_get_course_stats(self):
        stats = self.course.get_course_stats()
        self.assertEqual(stats["enrollments"], 0)
        self.assertEqual(stats["revenue"], 0)
        self.assertEqual(stats["reviews"], 0)
        self.assertEqual(stats["average_rating"], 0)
        self.assertEqual(stats["chapters"], 0)
        self.assertEqual(stats["lessons"], 0)

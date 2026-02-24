from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.course_views import (
    CourseViewSet,
)
from .views.interactionCourse_views import (
    CourseEnrollmentViewSet,
    CourseReviewViewSet,
)

router1 = DefaultRouter()
router1.register(r"courses", CourseViewSet, basename="course")
router1.register(r"enrollments", CourseEnrollmentViewSet, basename="enrollments")
router1.register(r"reviews", CourseReviewViewSet, basename="reviews")

urlpatterns = [
    path("course-api/", include(router1.urls)),
]

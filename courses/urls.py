from django.db import router
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.course_views import (
    CourseViewSet,
)
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    path('apis/', include(router.urls)),
]
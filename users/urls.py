from django.db import router
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeacherViewSet,
    StudentViewSet, 
)
router = DefaultRouter()
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'students', StudentViewSet, basename='student')

urlpatterns = [
    path('user-api/', include(router.urls)),
]
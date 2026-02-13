from django.contrib import admin
from .models import Teacher, Student
from django.contrib.auth import get_user_model

User = get_user_model()

admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(User)

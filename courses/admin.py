from django.contrib import admin
from .models import Education, Course, Lesson, Chapter, Subject

admin.site.register(Education)
admin.site.register(Course)
admin.site.register(Chapter)
admin.site.register(Lesson)
admin.site.register(Subject)

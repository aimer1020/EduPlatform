from rest_framework import serializers
from .models import User, Teacher, Student
from django.db import transaction

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True}, 
        }

class TeacherlistSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['id', 'user_info']
        
    def get_user_info(self, obj):
        if obj.user:
            return {
                'username': obj.user.username,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'user_type': obj.user.user_type,
            }
        return None
    
class TeacherDetailSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['id', 'subject', 'additional_subjects', 'experience_years', 'user_info', 'created_at']
        
    def get_user_info(self, obj):
        if obj.user:
            return {
                'username': obj.user.username,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'user_type': obj.user.user_type,
            }
        return None
    
class teacherCreateUpdateSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source='user')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        request = self.context.get('request')
        if request and request.user:
            if not (request.user.is_staff or request.user.is_superuser):
                user_fields = self.fields['user_info'].fields
                if 'user_type' in user_fields:
                    user_fields['user_type'].read_only = True
    
    class Meta:
        model = Teacher
        fields = ['id', 'subject', 'additional_subjects', 'experience_years', 'user_info']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        with transaction.atomic():
            user = User.objects.create_user(**user_data)
            teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        with transaction.atomic():
            if user_data:
                user_instance = instance.user
                for attr, value in user_data.items():
                    if attr == 'password':
                        user_instance.set_password(value)
                    else:
                        setattr(user_instance, attr, value)
                user_instance.save()
            #update teacher fields
            return super().update(instance, validated_data)
    def to_internal_value(self, data):
        instance = getattr(self, 'instance', None)
        if instance and 'user_info' in data:
            self.fields['user_info'].instance = instance.user
        return super().to_internal_value(data)

class StudentlistSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = ['id', 'user_info', 'grade_level']
        
    def get_user_info(self, obj):
        if obj.user:
            return {
                'username': obj.user.username,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'user_type': obj.user.user_type,
            }
        return None
    
class StudentDetailSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = ['id', 'user_info', 'enrollments', 'academic_year', 'grade_level', 'phone', 'parent_phone', 'created_at', 'enrolled_courses_count']
        
    def get_user_info(self, obj):
        if obj.user:
            return {
                'username': obj.user.username,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'user_type': obj.user.user_type,
            }
        return None

class StudentCreateUpdateSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source='user')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        request = self.context.get('request')
        if request and request.user:
            if not (request.user.is_staff or request.user.is_superuser):
                user_fields = self.fields['user_info'].fields
                if 'user_type' in user_fields:
                    user_fields['user_type'].read_only = True
    
    class Meta:
        model = Student
        fields = ['id', 'user_info', 'academic_year', 'phone', 'parent_phone']
        read_only_fields = ['enrollment_date']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        with transaction.atomic():
            user = User.objects.create_user(**user_data)
            student = Student.objects.create(user=user, **validated_data)
        return student
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        with transaction.atomic():
            if user_data:
                user_instance = instance.user
                for attr, value in user_data.items():
                    if attr == 'password':
                        user_instance.set_password(value)
                    else:
                        setattr(user_instance, attr, value)
                user_instance.save()
            #update student fields
            return super().update(instance, validated_data)
    
    def to_internal_value(self, data):
        instance = getattr(self, 'instance', None)
        if instance and 'user_info' in data:
            self.fields['user_info'].instance = instance.user
        return super().to_internal_value(data)

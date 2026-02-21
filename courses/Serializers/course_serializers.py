from rest_framework import serializers
from ..models.course_models import Course, Education, Subject
from ..validators import MAX_COURSE_PRICE, MIN_COURSE_PRICE, validate_image_size, validate_image_dimensions

class EducationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'
        
class EducationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'title', 'description', 'price', 'education_img', 'is_published']
        
class SubjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'
        
class SubjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']

class CourseDetailSerializer(serializers.ModelSerializer):
        teacher_info = serializers.SerializerMethodField()
        education_name = serializers.ReadOnlyField(source='education.country')
        subject_name = serializers.ReadOnlyField(source='subject.name')
    
        class Meta:
            model = Course
            fields = [
                    'id', 'title', 'teacher_info', 
                    'subject_name', 'education_name', 'description', 
                    'price', 'course_img', 'is_published',
                    'is_active', 'teacher', 'subject', 
                    'education', 'created_at', 'published_at'
                    ]
        
        def get_teacher_info(self, obj):
            if obj.teacher:
                return {
                    'name': str(obj.teacher),
                    'experience_years': obj.teacher.experience_years
                }
            return None

class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.StringRelatedField(read_only=True, source='teacher')
    class Meta:
        model = Course
        fields = ['id', 'title', 'subject', 'price', 'course_img', 'is_published', 'is_active', 'teacher_name']

class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'teacher', 'education', 'subject', 'title', 'description',    'price', 'course_img', 'is_published', 'is_active'] 
        read_only_fields = ['teacher'] 
    
    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None

        if self.instance and user and getattr(user, 'user_type', None) == 'student':
            raise serializers.ValidationError("Students are not allowed to update courses.")

        is_active = attrs.get('is_active', self.instance.is_active if self.instance else True)
        is_published = attrs.get('is_published', self.instance.is_published if self.instance else False)

        if not is_active and is_published:
            raise serializers.ValidationError({
                "is_published": "Cannot publish a course that is not active."
            })
        return attrs
    
    def validate_price(self, value):
        if value < MIN_COURSE_PRICE or value > MAX_COURSE_PRICE:
            raise serializers.ValidationError(f"Price must be between {MIN_COURSE_PRICE} and {MAX_COURSE_PRICE} EGP.")
        return value
    
    def validate_title(self, value):
        if value.isdigit():
            raise serializers.ValidationError("Title cannot be purely numeric.")
        return value
    
    def validate_course_img(self, value):
        if value:
            validate_image_size(value)            
            validate_image_dimensions(value)
            
            if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("Unsupported file extension. Allowed: .jpg, .jpeg, .png")
        return value
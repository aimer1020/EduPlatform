# EduPlatform
A learning platform for primary and preparatory students following Egyptian and Saudi curricula.

![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.2-green)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub stars](https://img.shields.io/github/stars/username/EduPlatform)

## Table of Contents
- [About](#about)
- [Features](#features)
- [Models Overview](#models-overview)
- [Courses Architecture](#courses-architecture)
- [Installation](#installation)
- [API Documentation](#api-documentation)
- [API Architecture](#api-architecture)
- [Security and Permissions](#security-and-permissions)
- [Access Control Strategy](#access-control-strategy)
- [Testing](#testing)
- [Acknowledgements](#acknowledgements)
- [FAQ / Troubleshooting](#faq--troubleshooting)

------

## About
EduPlatform is a backend-powered educational platform built using Python and Django.
It is designed to deliver structured curriculum content for Egyptian and Saudi educational systems, providing a scalable and secure REST API for managing users, courses, and academic content.
The system supports Students, Teachers, and Admin roles with strict access control and modular architecture.  

Built with **Python**, **Django**, and modern web technologies, it targets students, teachers, and schools who want a structured digital learning experience.

------

## Features

### Educational Platform
- Curriculum-based content (Egyptian & Saudi)
- Structured academic hierarchy:
  Education → Subject → Course → Chapter → Lesson
- Interactive lessons and quizzes
- Progress tracking and statistics

### User Management
- Custom User model extending AbstractUser
- Role-based classification (Teacher / Student)
- Dedicated Teacher & Student profiles
- Custom validation (BDF, phone)
- Profile-specific fields

### REST API (Django REST Framework)
- Full Course API (CRUD)
- Full Teacher & Student APIs
- Router-based endpoint structure
- Dedicated serializers for each entity

### Security
- Role-Based Access Control (RBAC)
- Owner-based permissions (users manage only their own data)
- Admin full access
- Custom permission classes

### Testing
- Model tests
- API endpoint tests
- Serializer tests
- Permission tests
------

## Models-Overview

### User System
The user system is built on a custom User model extending Django's AbstractUser.
Key enhancements:
  - Role-based classification (Teacher / Student)
  - Custom validators
  - Optimized relationships using OneToOne profiles
  - Improved data integrity and scalability design

### TeacherProfile
- Linked OneToOne to User
- Fields:
  - Subject specialization
  - Teaching experience
  - CV upload
  - Verification status

### StudentProfile
- Linked OneToOne to User
- Fields:
  - Academic year
  - Contact information
  - Parent/guardian details
    
   
-----------------

## Courses Architecture
The courses app is designed with a modular structure for better scalability and maintainability.

### Model Structure
- course_models.py
  - Custom validators
  - Upload path helper functions
  - Education model
  - Subject model
  - Course model

### Academic Hierarchy

Education → Subject → Course → Chapter → Lesson

This hierarchy ensures structured content organization aligned with Egyptian and Saudi curricula.

------

## Installation

1. Clone the repository:
```bash
git clone https://github.com/username/EduPlatform.git
cd EduPlatform

2. Create virtual environment:
python -m venv env        # Windows
source env/bin/activate   # Linux/macOS

-Activate environment:
  -env\Scripts\activate      # Windows
  -source env/bin/activate   # Linux/macOS

3. Install dependencies:
pip install -r requirements.txt

4. Apply migrations:
python manage.py migrate

5. Run server:
python manage.py runserver
```
-----

## API documentation


### Users API

-Base URL:
  -Users API:  user-api/
  -Courses API: course-api/
Access to endpoints is restricted based on user role.

### Teacher Endpoints
- GET user-api/teachers/
- POST user-api/teachers/
- GET user-api/teachers/{id}/
- PUT user-api/teachers/{id}/
- DELETE user-api/teachers/{id}/

### Student Endpoints
- GET user-api/students/
- POST user-api/students/
- GET user-api/students//{id}/
- PUT user-api/students/{id}/
- DELETE user-api/students/{id}/

### Course Endpoints
-GET     /course-api/courses/
-POST    /course-api/courses/
-GET     /course-api/courses/{id}/
-PUT     /course-api/courses/{id}/
-DELETE  /course-api/courses/{id}/

---------------------------------------------------------

## API Architecture

The API layer follows a modular structure:

- permissions files → access control
- serializers files → Data serialization & validation
- view files → API logic and endpoints
- test files → Model, view, serializers, Permissions, and API test coverage

This structure ensures maintainability and scalability.

-----------------

## Security and Permissions

The platform implements role-based access control using custom
Django REST Framework permission classes.

- Teachers and Students have differentiated access
- API endpoints are protected based on user role
- Unauthorized access is properly restricted
- Permission behavior is covered by automated tests
- The system implements strict Role-Based Access Control (RBAC):
  - Teachers can view and modify only their own profile
  - Students can update only their own profile
  - Admin users have unrestricted access
  - Permissions are enforced at the API level
  - All permission rules are covered by automated tests

This ensures secure and structured access management.

-------------------
## Access Control Strategy

- Ownership-based editing restrictions
- Role verification before action execution
- Explicit permission classes per view
- Tested access rules to prevent privilege escalation

------------------

## Testing

Automated tests cover:
- Course model
- Course API
- User serializers
- Teacher and Student APIs
- Custom permissions and role restrictions

Run tests:
```bash
python manage.py test
```

-------------------------------

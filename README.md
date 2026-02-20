# EduPlatform
A learning platform for primary and preparatory students following Egyptian and Saudi curricula.

![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.2-green)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub stars](https://img.shields.io/github/stars/username/EduPlatform)

## Table of Contents
- [About](#about)
- [Features](#features)
- [Models Overview](#Models-Overview)
- [Courses Architecture](#Courses-Architecture)
- [Installation](#Installation)
- [API Documentation](#api-documentation)
- [API Architecture](#API-Architecture)
- [Security & Permissions](#Security-and-Permissions)
- [Testing](#Testing)
- [Roadmap](#roadmap)
- [Acknowledgements](#acknowledgements)
- [FAQ / Troubleshooting](#faq--troubleshooting)

------

## About
EduPlatform is an educational web platform designed to support students in primary and preparatory school.  
It provides curriculum content for both the Egyptian and Saudi educational systems, interactive lessons, exercises, quizzes, and progress tracking.  

Built with **Python**, **Django**, and modern web technologies, it targets students, teachers, and schools who want a structured digital learning experience.

------

## Features
- Interactive lessons for Egyptian and Saudi curricula  
- Exercises and quizzes with instant feedback  
- User authentication and profile management (Students & Teachers)  
- Progress tracking and performance statistics  
- Teacher/admin panel to manage content and monitor students  
- Multi-language support (Arabic/English)  
- Responsive design for desktop and tablet
- User management system with extended User model
- Differentiated profiles for Teachers and Students
- Custom validation for BDF and phone numbers
- Teacher-specific fields: subject specialization, experience, CV, verification status
- Student-specific fields: academic year, contact information, and parent/guardian details
- Modular course management system
- Structured academic hierarchy:
  - Education Level
  - Subject
  - Course
  - Chapter
  - Lesson
- Custom validators for course-related data
- Organized model structure (lesson_models.py & course_models.py)
- Robust user system with extended User model and role-based classification
- Optimized profile models with strong validation and data integrity
- RESTful Course API built with Django REST Framework
- Structured serializers and views architecture
- Unit tests for models and API endpoints
- Scalable API structure ready for expansion
- - Role-based access control using custom permission classes
- Secure API endpoints with authorization rules
- Permission test coverage to ensure access integrity

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
   - lesson_models.py
     - Custom validators
     - Lesson model

   - course_models.py
     - Custom validators
     - Upload path helper functions
     - Education model
     - Subject model
     - Course model
     - Chapter model

  ### Academic Hierarchy

    Education → Subject → Course → Chapter → Lesson

    This hierarchy ensures structured content organization aligned with
    Egyptian and Saudi curricula.
------

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/username/EduPlatform.git

----------------------

## API documentation
API layer will be implemented using Django REST Framework.

   ### Users API (planned)
   - **POST /api/users/register/** - Register new user
   - **GET /api/users/{id}/** - Retrieve user profile
   - **PUT /api/users/{id}/** - Update user profile
   - **GET /api/teachers/** - List all teachers
   - **GET /api/students/** - List all students

## Course API

Base URL: courses/apis/courses/

### Endpoints

- **GET courses/apis/courses/**  
  Retrieve list of courses

- **POST courses/apis/courses/**  
  Create a new course

- **GET courses/apis/courses/{id}/**  
  Retrieve a specific course

- **PUT courses/apis/courses/{id}/**  
  Update a course

- **DELETE courses/apis/courses/{id}/**  
  Delete a course

---------------------------------------------------------

## API Architecture

The API layer follows a modular structure:

- course_serializers.py → Data serialization & validation
- course_view.py → API logic and endpoints
- tests/ → Model and API test coverage

This structure ensures maintainability and scalability.

-----------------

## Security and Permissions

The platform implements role-based access control using custom
Django REST Framework permission classes.

- Teachers and Students have differentiated access
- API endpoints are protected based on user role
- Unauthorized access is properly restricted
- Permission behavior is covered by automated tests

This ensures secure and structured access management.
-------------------

## Testing

The project includes automated tests for:

- Course model validation
- Course API endpoints
- Custom user permissions

Run tests using:
```bash
python manage.py test
-------------------------------

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
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
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
- 


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
    
   
------
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

## API documentation
API layer will be implemented using Django REST Framework.

   ### Users API (planned)
   - **POST /api/users/register/** - Register new user
   - **GET /api/users/{id}/** - Retrieve user profile
   - **PUT /api/users/{id}/** - Update user profile
   - **GET /api/teachers/** - List all teachers
   - **GET /api/students/** - List all students


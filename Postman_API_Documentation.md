# LMS (Learning Management System) API Documentation for Postman Testing

## Base URL
```
http://localhost:8000/api
```

## Authentication
This API uses JWT (JSON Web Token) authentication. After login, include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

---

## 1. Authentication APIs

### 1.1 User Registration
**Endpoint:** `POST /auth/register/`  
**Permission:** Public (No authentication required)

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response (Success - 201):**
```json
{
    "success": true,
    "message": "Registration successful! Please check your email for verification.",
    "data": {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "john@example.com",
        "username": "john_doe"
    }
}
```

**Response (Error - 400):**
```json
{
    "success": false,
    "message": "Registration failed",
    "errors": {
        "email": ["This field is required."],
        "password": ["This field is required."]
    }
}
```

### 1.2 User Login
**Endpoint:** `POST /auth/login/`  
**Permission:** Public

**Request Body:**
```json
{
    "email": "john@example.com",
    "password": "SecurePassword123!"
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "john_doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student",
            "is_verified": true,
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
}
```

### 1.3 User Profile
**Endpoint:** `GET /auth/profile/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "student",
        "is_verified": true,
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

### 1.4 Update Profile
**Endpoint:** `PUT /auth/profile/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "first_name": "Johnny",
    "last_name": "Doe",
    "username": "johnny_doe"
}
```

### 1.5 Email Verification
**Endpoint:** `GET /auth/verify-email/<token>/`  
**Permission:** Public

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Email verified successfully! You can now login."
}
```

### 1.6 User Logout
**Endpoint:** `POST /auth/logout/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Logout successful"
}
```

---

## 2. Course APIs

### 2.1 Get All Courses
**Endpoint:** `GET /courses/courses/`  
**Permission:** Public

**Query Parameters:**
- `course_type`: Filter by course type
- `teacher`: Filter by teacher ID
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `search`: Search in title, description, teacher name
- `ordering`: Sort by created_at, title, price

**Example URL:**
```
GET /courses/courses/?min_price=100&max_price=500&search=python&ordering=-created_at
```

**Response (Success - 200):**
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/courses/courses/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Python Programming Basics",
            "description": "Learn Python from scratch",
            "price": 299.99,
            "course_type": "programming",
            "teacher": {
                "id": "456e7890-e89b-12d3-a456-426614174000",
                "username": "teacher_john",
                "first_name": "John",
                "last_name": "Teacher"
            },
            "thumbnail": "http://localhost:8000/media/courses/python_thumb.jpg",
            "created_at": "2024-01-10T10:00:00Z",
            "is_active": true
        }
    ]
}
```

### 2.2 Get Course Details
**Endpoint:** `GET /courses/courses/<course_id>/`  
**Permission:** Public

**Response (Success - 200):**
```json
{
    "id": 1,
    "title": "Python Programming Basics",
    "description": "Complete Python course for beginners",
    "price": 299.99,
    "course_type": "programming",
    "teacher": {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "username": "teacher_john",
        "first_name": "John",
        "last_name": "Teacher"
    },
    "videos": [
        {
            "id": 1,
            "title": "Introduction to Python",
            "duration": 1200,
            "video_url": "http://localhost:8000/media/videos/intro.mp4",
            "order": 1
        }
    ],
    "quizzes": [
        {
            "id": 1,
            "title": "Python Basics Quiz",
            "questions_count": 10,
            "passing_score": 70
        }
    ],
    "total_duration": 7200,
    "total_videos": 15,
    "created_at": "2024-01-10T10:00:00Z",
    "is_active": true
}
```

### 2.3 Get Course Videos
**Endpoint:** `GET /courses/courses/<course_id>/videos/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "course_id": 1,
    "course_title": "Python Programming Basics",
    "videos": [
        {
            "id": 1,
            "title": "Introduction to Python",
            "description": "Basic introduction to Python programming",
            "video_url": "http://localhost:8000/media/videos/intro.mp4",
            "duration": 1200,
            "order": 1,
            "is_completed": false
        },
        {
            "id": 2,
            "title": "Variables and Data Types",
            "description": "Learn about Python variables",
            "video_url": "http://localhost:8000/media/videos/variables.mp4",
            "duration": 1800,
            "order": 2,
            "is_completed": false
        }
    ]
}
```

### 2.4 Enroll in Course
**Endpoint:** `POST /courses/courses/<course_id>/enroll/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "payment_method": "jazzcash",
    "payment_details": {
        "transaction_id": "TXN123456789"
    }
}
```

**Response (Success - 201):**
```json
{
    "success": true,
    "message": "Successfully enrolled in course",
    "data": {
        "enrollment_id": 1,
        "course_id": 1,
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "enrolled_at": "2024-01-15T10:30:00Z",
        "payment_status": "completed"
    }
}
```

### 2.5 Get Course Progress
**Endpoint:** `GET /courses/courses/<course_id>/progress/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "course_id": 1,
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "progress": {
        "completed_videos": 5,
        "total_videos": 15,
        "completed_quizzes": 2,
        "total_quizzes": 5,
        "completion_percentage": 33.33,
        "last_accessed": "2024-01-15T10:30:00Z"
    }
}
```

---

## 3. Video APIs

### 3.1 Get Video Details
**Endpoint:** `GET /courses/videos/<video_id>/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "id": 1,
    "title": "Introduction to Python",
    "description": "Basic introduction to Python programming",
    "video_url": "http://localhost:8000/media/videos/intro.mp4",
    "duration": 1200,
    "order": 1,
    "course": {
        "id": 1,
        "title": "Python Programming Basics"
    },
    "is_completed": false,
    "quiz_assignments": [
        {
            "id": 1,
            "title": "Intro Quiz",
            "type": "quiz"
        }
    ]
}
```

### 3.2 Mark Video as Complete
**Endpoint:** `POST /courses/videos/<video_id>/complete/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "watched_duration": 1200
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Video marked as completed",
    "data": {
        "video_id": 1,
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "completed_at": "2024-01-15T10:30:00Z",
        "watched_duration": 1200
    }
}
```

---

## 4. Payment APIs

### 4.1 Initiate JazzCash Payment
**Endpoint:** `POST /payments/jazzcash/initiate/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "course_id": 1,
    "amount": 299.99,
    "phone_number": "03001234567"
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Payment initiated successfully",
    "data": {
        "payment_id": "PAY123456789",
        "jazzcash_url": "https://jazzcash.com.pk/pay/PAY123456789",
        "transaction_id": "TXN123456789",
        "amount": 299.99,
        "expires_at": "2024-01-15T11:00:00Z"
    }
}
```

### 4.2 Verify JazzCash Payment
**Endpoint:** `POST /payments/jazzcash/verify/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "payment_id": "PAY123456789",
    "transaction_id": "TXN123456789",
    "status": "completed"
}
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Payment verified successfully",
    "data": {
        "payment_id": "PAY123456789",
        "status": "completed",
        "verified_at": "2024-01-15T10:45:00Z"
    }
}
```

### 4.3 Initiate EasyPaisa Payment
**Endpoint:** `POST /payments/easypaisa/initiate/`  
**Permission:** Authenticated users only  
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "course_id": 1,
    "amount": 299.99,
    "phone_number": "03001234567"
}
```

---

## 5. Student Dashboard APIs

### 5.1 Student Dashboard Overview
**Endpoint:** `GET /students/`  
**Permission:** Authenticated students only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "user": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "john_doe",
            "first_name": "John",
            "last_name": "Doe"
        },
        "stats": {
            "total_enrolled_courses": 5,
            "completed_courses": 2,
            "in_progress_courses": 3,
            "total_certificates": 2,
            "total_spent": 1499.95
        },
        "recent_courses": [
            {
                "id": 1,
                "title": "Python Programming Basics",
                "progress": 75,
                "last_accessed": "2024-01-15T10:30:00Z"
            }
        ]
    }
}
```

### 5.2 Student Enrolled Courses
**Endpoint:** `GET /students/courses/`  
**Permission:** Authenticated students only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "enrolled_courses": [
            {
                "id": 1,
                "title": "Python Programming Basics",
                "description": "Learn Python from scratch",
                "progress": 75,
                "enrolled_at": "2024-01-10T10:00:00Z",
                "last_accessed": "2024-01-15T10:30:00Z",
                "completion_status": "in_progress"
            }
        ]
    }
}
```

### 5.3 Student Payment History
**Endpoint:** `GET /students/payments/`  
**Permission:** Authenticated students only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "payments": [
            {
                "id": 1,
                "course_title": "Python Programming Basics",
                "amount": 299.99,
                "payment_method": "jazzcash",
                "status": "completed",
                "transaction_id": "TXN123456789",
                "paid_at": "2024-01-10T10:30:00Z"
            }
        ],
        "total_spent": 299.99
    }
}
```

---

## 6. Teacher Dashboard APIs

### 6.1 Teacher Dashboard Overview
**Endpoint:** `GET /teacher/`  
**Permission:** Authenticated teachers only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "teacher": {
            "id": "456e7890-e89b-12d3-a456-426614174000",
            "username": "teacher_john",
            "first_name": "John",
            "last_name": "Teacher"
        },
        "stats": {
            "total_courses": 10,
            "total_students": 250,
            "total_revenue": 24999.50,
            "active_courses": 8
        },
        "recent_enrollments": [
            {
                "student_name": "John Doe",
                "course_title": "Python Programming Basics",
                "enrolled_at": "2024-01-15T10:30:00Z"
            }
        ]
    }
}
```

### 6.2 Teacher Courses
**Endpoint:** `GET /teacher/courses/`  
**Permission:** Authenticated teachers only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "courses": [
            {
                "id": 1,
                "title": "Python Programming Basics",
                "description": "Learn Python from scratch",
                "price": 299.99,
                "enrolled_students": 45,
                "total_videos": 15,
                "is_active": true,
                "created_at": "2024-01-10T10:00:00Z"
            }
        ]
    }
}
```

---

## 7. Admin Dashboard APIs

### 7.1 Admin Dashboard Overview
**Endpoint:** `GET /admin/overview/`  
**Permission:** Admin users only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "stats": {
            "total_users": 1250,
            "total_teachers": 45,
            "total_students": 1200,
            "total_courses": 150,
            "total_revenue": 125000.00,
            "pending_payments": 25
        },
        "recent_activities": [
            {
                "type": "user_registration",
                "message": "New user John Doe registered",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ]
    }
}
```

### 7.2 Admin Users List
**Endpoint:** `GET /admin/users/`  
**Permission:** Admin users only  
**Headers:** `Authorization: Bearer <access_token>`

**Response (Success - 200):**
```json
{
    "success": true,
    "data": {
        "users": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "student",
                "is_verified": true,
                "created_at": "2024-01-10T10:00:00Z"
            }
        ]
    }
}
```

---

## Postman Collection Setup Guide

### 1. Environment Variables
Create a Postman environment with these variables:
- `base_url`: `http://localhost:8000/api`
- `access_token`: (will be set automatically after login)
- `refresh_token`: (will be set automatically after login)

### 2. Authorization Setup
1. For endpoints requiring authentication, use Type: "Bearer Token"
2. Token: `{{access_token}}`

### 3. Test Scripts
Add this to your Login request's "Tests" tab to automatically save tokens:

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Save access token", function () {
    var jsonData = pm.response.json();
    if (jsonData.success && jsonData.data.access_token) {
        pm.environment.set("access_token", jsonData.data.access_token);
        pm.environment.set("refresh_token", jsonData.data.refresh_token);
    }
});
```

### 4. Common Headers
Add these headers to all requests:
- `Content-Type`: `application/json`
- `Accept`: `application/json`

### 5. Testing Flow
1. Start with User Registration
2. Verify email (if applicable)
3. Login to get tokens
4. Test other endpoints with authentication
5. Test course enrollment and progress tracking

---

## Error Responses

### Common Error Codes:
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Sample Error Response:
```json
{
    "success": false,
    "message": "Authentication failed",
    "error": "Invalid or expired token"
}
```
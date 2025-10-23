# 📡 PDSS API Documentation

## Overview

The PDSS backend provides a RESTful API built with FastAPI. All endpoints use JSON for request/response payloads.

**Base URL:** `http://localhost:8000`

**API Documentation:** 
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Patterns](#common-patterns)
3. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication-endpoints)
   - [Users](#users-endpoints)
   - [Projects](#projects-endpoints)
   - [Project Items](#project-items-endpoints)
   - [Items Master](#items-master-endpoints)
   - [Procurement](#procurement-endpoints)
   - [Finance](#finance-endpoints)
   - [Optimization](#optimization-endpoints)
   - [Currencies](#currencies-endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)

---

## Authentication

### JWT Bearer Token

All protected endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Token Lifecycle

- **Expiration:** 30 minutes (configurable)
- **Refresh:** Login again to get new token
- **Storage:** Store securely in client (e.g., httpOnly cookie)

---

## Common Patterns

### Pagination

```javascript
GET /endpoint?skip=0&limit=100
```

**Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 1000)

**Response:**
```json
[
  { "id": 1, ... },
  { "id": 2, ... }
]
```

### Filtering

```javascript
GET /endpoint?field=value&another_field=value
```

### Sorting

```javascript
GET /endpoint?sort_by=created_at&sort_order=desc
```

---

## API Endpoints

### Authentication Endpoints

#### Login

```http
POST /auth/login
```

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` - Invalid credentials
- `422` - Validation error

---

### Users Endpoints

#### Get Current User

```http
GET /users/me
```

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### List Users (Admin Only)

```http
GET /users/?skip=0&limit=100
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  },
  ...
]
```

#### Create User (Admin Only)

```http
POST /users/
```

**Request:**
```json
{
  "username": "newuser",
  "password": "password123",
  "role": "pm",
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": 5,
  "username": "newuser",
  "role": "pm",
  "is_active": true,
  "created_at": "2025-10-20T10:00:00Z"
}
```

#### Update User (Admin Only)

```http
PUT /users/{user_id}
```

**Request:**
```json
{
  "username": "updateduser",
  "password": "newpassword123",
  "role": "pmo",
  "is_active": true
}
```

**Response (200 OK):**
```json
{
  "id": 5,
  "username": "updateduser",
  "role": "pmo",
  "is_active": true,
  "created_at": "2025-10-20T10:00:00Z"
}
```

#### Delete User (Admin Only)

```http
DELETE /users/{user_id}
```

**Response (200 OK):**
```json
{
  "message": "User deleted successfully"
}
```

---

### Projects Endpoints

#### List Projects

```http
GET /projects/?skip=0&limit=100
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Hospital Equipment Project",
    "budget": 1000000.00,
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "description": "Medical equipment procurement",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  },
  ...
]
```

#### Get Project

```http
GET /projects/{project_id}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Hospital Equipment Project",
  "budget": 1000000.00,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "description": "Medical equipment procurement",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Create Project

```http
POST /projects/
```

**Request:**
```json
{
  "name": "New Project",
  "budget": 500000.00,
  "start_date": "2025-02-01",
  "end_date": "2025-06-30",
  "description": "Project description"
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "name": "New Project",
  "budget": 500000.00,
  "start_date": "2025-02-01",
  "end_date": "2025-06-30",
  "description": "Project description",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": null
}
```

#### Update Project

```http
PUT /projects/{project_id}
```

**Request:**
```json
{
  "name": "Updated Project Name",
  "budget": 600000.00
}
```

**Response (200 OK):**
```json
{
  "id": 2,
  "name": "Updated Project Name",
  "budget": 600000.00,
  "start_date": "2025-02-01",
  "end_date": "2025-06-30",
  "description": "Project description",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-20T11:00:00Z"
}
```

#### Delete Project

```http
DELETE /projects/{project_id}
```

**Response (200 OK):**
```json
{
  "message": "Project deleted successfully"
}
```

---

### Project Items Endpoints

#### List Items by Project

```http
GET /items/project/{project_id}?skip=0&limit=100
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "project_id": 1,
    "master_item_id": 5,
    "item_code": "SIEMENS-001",
    "item_name": "MRI Scanner",
    "quantity": 2,
    "delivery_options": ["2025-06-01", "2025-07-01"],
    "status": "PENDING",
    "external_purchase": false,
    "description": "High-field MRI scanner",
    "is_finalized": false,
    "finalized_by": null,
    "finalized_at": null,
    "created_at": "2025-01-05T00:00:00Z",
    "updated_at": null
  },
  ...
]
```

#### Get Finalized Items

```http
GET /items/finalized?skip=0&limit=100
```

**Response (200 OK):**
```json
[
  {
    "id": 10,
    "project_id": 1,
    "master_item_id": 8,
    "item_code": "GE-025",
    "item_name": "Ultrasound Machine",
    "quantity": 5,
    "delivery_options": ["2025-05-01"],
    "status": "DECIDED",
    "external_purchase": false,
    "description": "Portable ultrasound",
    "is_finalized": true,
    "finalized_by": 2,
    "finalized_at": "2025-10-15T14:30:00Z",
    "created_at": "2025-01-10T00:00:00Z",
    "updated_at": "2025-10-15T14:30:00Z"
  },
  ...
]
```

#### Create Project Item

```http
POST /items/
```

**Request:**
```json
{
  "project_id": 1,
  "master_item_id": 5,
  "item_code": "SIEMENS-001",
  "item_name": "MRI Scanner",
  "quantity": 2,
  "delivery_options": ["2025-06-01", "2025-07-01"],
  "external_purchase": false,
  "description": "High-field MRI scanner"
}
```

**Response (201 Created):**
```json
{
  "id": 15,
  "project_id": 1,
  "master_item_id": 5,
  "item_code": "SIEMENS-001",
  "item_name": "MRI Scanner",
  "quantity": 2,
  "delivery_options": ["2025-06-01", "2025-07-01"],
  "status": "PENDING",
  "external_purchase": false,
  "description": "High-field MRI scanner",
  "is_finalized": false,
  "finalized_by": null,
  "finalized_at": null,
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": null
}
```

#### Finalize Project Item (PMO/Admin Only)

```http
PUT /items/{item_id}/finalize
```

**Request:**
```json
{
  "is_finalized": true
}
```

**Response (200 OK):**
```json
{
  "id": 15,
  "project_id": 1,
  "item_code": "SIEMENS-001",
  "item_name": "MRI Scanner",
  "is_finalized": true,
  "finalized_by": 2,
  "finalized_at": "2025-10-20T10:30:00Z",
  ...
}
```

---

### Procurement Endpoints

#### List Procurement Options

```http
GET /procurement/options?skip=0&limit=100&item_code=SIEMENS-001
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "project_item_id": 15,
    "item_code": "SIEMENS-001",
    "supplier_name": "Medical Equipment Co.",
    "base_cost": 500000.00,
    "currency_id": 1,
    "currency_code": "USD",
    "shipping_cost": 5000.00,
    "lomc_lead_time": 90,
    "discount_bundle_threshold": 3,
    "discount_bundle_percent": 10.0,
    "payment_terms": {
      "type": "cash",
      "discount_percent": 2.0
    },
    "is_finalized": false,
    "created_at": "2025-10-18T00:00:00Z"
  },
  ...
]
```

#### Create Procurement Option

```http
POST /procurement/options
```

**Request:**
```json
{
  "project_item_id": 15,
  "item_code": "SIEMENS-001",
  "supplier_name": "Medical Equipment Co.",
  "base_cost": 500000.00,
  "currency_id": 1,
  "shipping_cost": 5000.00,
  "lomc_lead_time": 90,
  "discount_bundle_threshold": 3,
  "discount_bundle_percent": 10.0,
  "payment_terms": {
    "type": "cash",
    "discount_percent": 2.0
  }
}
```

**Response (201 Created):**
```json
{
  "id": 25,
  "project_item_id": 15,
  "item_code": "SIEMENS-001",
  "supplier_name": "Medical Equipment Co.",
  "base_cost": 500000.00,
  "currency_id": 1,
  "currency_code": "USD",
  "shipping_cost": 5000.00,
  "lomc_lead_time": 90,
  "discount_bundle_threshold": 3,
  "discount_bundle_percent": 10.0,
  "payment_terms": {
    "type": "cash",
    "discount_percent": 2.0
  },
  "is_finalized": false,
  "created_at": "2025-10-20T10:00:00Z"
}
```

---

### Optimization Endpoints

#### Run Optimization

```http
POST /optimization/run
```

**Request:**
```json
{
  "item_codes": ["SIEMENS-001", "GE-025"],
  "weights": {
    "cost": 0.4,
    "lead_time": 0.3,
    "quality": 0.2,
    "payment_terms": 0.1
  }
}
```

**Response (200 OK):**
```json
{
  "pareto_front": [
    {
      "option_id": 25,
      "item_code": "SIEMENS-001",
      "supplier_name": "Medical Equipment Co.",
      "total_cost": 495000.00,
      "lead_time": 90,
      "score": 0.85,
      "is_optimal": true
    },
    ...
  ],
  "recommendations": [
    {
      "item_code": "SIEMENS-001",
      "recommended_option_id": 25,
      "reason": "Best balance of cost and lead time"
    }
  ]
}
```

---

### Error Handling

#### Error Response Format

```json
{
  "detail": "Error message"
}
```

OR for validation errors:

```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "field_name"],
      "msg": "Input should be a valid string",
      "input": 123
    }
  ]
}
```

#### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

Currently no rate limiting implemented. For production, consider:
- 100 requests/minute per user
- 1000 requests/hour per IP
- Burst allowance of 10 requests

---

## Best Practices

### Client Implementation

✅ **DO:**
- Store tokens securely
- Handle token expiration
- Implement retry logic
- Validate responses
- Handle errors gracefully
- Use connection pooling
- Cache responses when appropriate

❌ **DON'T:**
- Store tokens in localStorage
- Ignore error responses
- Make unnecessary API calls
- Send passwords in GET requests
- Expose API keys

### Example Client (JavaScript)

```javascript
// API Client with axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
api.interceptors.request.use(config => {
  const token = getToken(); // Your token storage
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Usage
try {
  const response = await api.get('/projects/');
  console.log(response.data);
} catch (error) {
  console.error('Error:', error.response?.data?.detail);
}
```

---

*For complete, interactive API documentation, visit: http://localhost:8000/docs*

*Last Updated: October 20, 2025*


# API Contracts & Response Formats

All API endpoints follow a consistent response format for both success and error cases.

## Base URL

```
/api/v1
```

## Response Format

### Success Response

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

## Standard HTTP Status Codes

- `200 OK`: Successful GET, PUT, PATCH request
- `201 Created`: Successful POST request that creates a resource
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request parameters or malformed JSON
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User lacks permission for this resource
- `404 Not Found`: Resource does not exist
- `409 Conflict`: Request conflicts with existing data (e.g., duplicate email)
- `422 Unprocessable Entity`: Validation failed
- `500 Internal Server Error`: Server encountered an error

## Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `INVALID_CREDENTIALS` | 401 | Email or password is incorrect |
| `UNAUTHORIZED` | 401 | Authentication token is missing or expired |
| `ACCOUNT_DISABLED` | 403 | User account is disabled |
| `FORBIDDEN` | 403 | User lacks permission for this resource |
| `NOT_FOUND` | 404 | Resource does not exist |
| `CONFLICT` | 409 | Resource already exists (e.g., duplicate email) |
| `SYSTEM_ERROR` | 500 | Unexpected server error |

## Authentication

All protected endpoints require a JWT bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Login

**POST** `/auth/login`

Request:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "role": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "admin",
        "description": "Administrator role"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  },
  "message": "Login successful"
}
```

### Current User

**GET** `/auth/me` (requires authentication)

Response:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "role": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "admin"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Logout

**POST** `/auth/logout` (requires authentication)

Response:
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### Refresh Token

**POST** `/auth/refresh` (requires refresh token)

Request Header:
```
Authorization: Bearer <refresh_token>
```

Response:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

## Data Format Standards

### Dates and Times

All dates and times are in ISO 8601 format with UTC timezone:

```
2024-01-15T10:30:00Z
```

### Money Representation

All monetary values are represented as numbers with 2 decimal places:

```json
{
  "price": 99.99,
  "total_amount": 500.00
}
```

Never use binary floating-point values. Backend stores as NUMERIC(15,2).

### Status Values

Each entity type has documented status values:

**Subscription Status:**
- `active` - Actively billing
- `suspended` - Temporarily paused
- `cancelled` - Ended by customer
- `churned` - Naturally expired

**Invoice Status:**
- `draft` - Not yet sent
- `sent` - Sent to customer
- `viewed` - Customer viewed
- `partially_paid` - Payment received but not complete
- `paid` - Fully paid
- `overdue` - Past due date
- `cancelled` - Cancelled

**Payment Status:**
- `pending` - Awaiting processing
- `processing` - Currently processing
- `completed` - Successfully processed
- `failed` - Processing failed
- `refunded` - Refunded to customer

## Pagination

Endpoints that return lists support pagination with the following parameters:

Query Parameters:
- `page` (default: 1) - Page number
- `pageSize` (default: 20) - Items per page
- `sortBy` (optional) - Sort field
- `sortOrder` (optional) - 'asc' or 'desc'

Response:
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

## Filtering and Sorting

Endpoints support filtering via query parameters and sorting:

Example:
```
GET /api/v1/customers?status=active&sortBy=name&sortOrder=asc
```

## Common Field Conventions

- `id` - UUID v4
- `created_at` - ISO 8601 datetime
- `updated_at` - ISO 8601 datetime
- `status` - String enum (documented per entity)
- `is_active` - Boolean
- `is_deleted` - Boolean (soft delete)

## CORS

The API implements CORS restrictions:
- Allowed Origins: Configured in `CORS_ORIGINS` environment variable
- Allowed Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Allowed Headers: Content-Type, Authorization
- Credentials: Supported

## Rate Limiting

Rate limiting is applied to authentication endpoints to prevent brute force attacks:
- `/auth/login`: 5 attempts per minute per IP
- Other endpoints: 100 requests per minute per user

## Versioning

The API uses URL versioning:
- Current version: `/api/v1`
- All new features in v1 are backward compatible
- Future breaking changes will increment to `/api/v2`

## Module-Specific Endpoints

### Module 2: Sales & Subscriptions

- `POST /customers` - Create customer
- `GET /customers/{id}` - Get customer
- `PUT /customers/{id}` - Update customer
- `POST /products` - Create product
- `GET /plans/{id}` - Get plan details
- `POST /subscriptions` - Create subscription

### Module 3: Billing & Payments

- `POST /invoices` - Create invoice
- `GET /invoices/{id}` - Get invoice
- `POST /invoices/{id}/send` - Send invoice
- `POST /payments` - Record payment
- `GET /payments/{id}` - Get payment details

### Module 4: Analytics & Notifications

- `GET /analytics/dashboard` - Dashboard metrics
- `GET /notifications` - List notifications
- `PUT /notifications/{id}/read` - Mark as read
- `GET /audit-logs` - List audit logs

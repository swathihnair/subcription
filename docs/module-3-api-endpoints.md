# Module 3: Billing & Finance API Endpoints

This document describes all API endpoints for the Billing, Invoices & Finance module.

## Base URL
All endpoints are prefixed with `/api/v1`

## Authentication
All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

## Common Error Responses

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | VALIDATION_ERROR | Request data is invalid |
| 401 | UNAUTHORIZED | Missing or invalid authentication |
| 403 | FORBIDDEN | User lacks required permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Duplicate resource or conflicting state |
| 500 | SYSTEM_ERROR | Internal server error |

---

## Invoice Endpoints

### List Invoices
```
GET /api/v1/invoices
```

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `pageSize` (integer, default: 20) - Items per page
- `status` (string) - Filter by status: draft, open, partially_paid, paid, overdue, void
- `customer_id` (UUID) - Filter by customer
- `subscription_id` (UUID) - Filter by subscription
- `from_date` (ISO datetime) - Filter invoices from date
- `to_date` (ISO datetime) - Filter invoices to date

**Permissions:** `view_invoices` or `all` (finance, admin roles)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "invoice_number": "INV-20261031-12345",
      "customer_id": "uuid",
      "subscription_id": "uuid",
      "status": "open",
      "invoice_date": "2026-10-31T00:00:00Z",
      "due_date": "2026-11-30T00:00:00Z",
      "subtotal_amount": 100.00,
      "tax_amount": 10.00,
      "total_amount": 110.00,
      "amount_paid": 0.00,
      "amount_due": 110.00,
      "currency": "USD",
      "customer": { /* customer object */ }
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 45,
    "totalPages": 3
  }
}
```

---

### Get Invoice Details
```
GET /api/v1/invoices/{id}
```

**Permissions:** `view_invoices` or `all`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "invoice_number": "INV-20261031-12345",
    "customer_id": "uuid",
    "subscription_id": "uuid",
    "status": "open",
    "invoice_date": "2026-10-31T00:00:00Z",
    "due_date": "2026-11-30T00:00:00Z",
    "billing_period_start": "2026-10-01T00:00:00Z",
    "billing_period_end": "2026-10-31T23:59:59Z",
    "subtotal_amount": 100.00,
    "tax_amount": 10.00,
    "total_amount": 110.00,
    "amount_paid": 0.00,
    "amount_due": 110.00,
    "currency": "USD",
    "customer": { /* customer object */ },
    "subscription": { /* subscription object */ },
    "line_items": [
      {
        "id": "uuid",
        "description": "Pro Plan - monthly subscription",
        "quantity": 1,
        "unit_price": 100.00,
        "discount_amount": 0.00,
        "tax_rate": 10.00,
        "tax_amount": 10.00,
        "total_amount": 110.00
      }
    ]
  }
}
```

---

### Create Invoice
```
POST /api/v1/invoices
```

**Permissions:** `manage_payments` or `all` (finance, admin roles)

**Request Body:**
```json
{
  "customer_id": "uuid",
  "subscription_id": "uuid (optional)",
  "invoice_date": "2026-10-31T00:00:00Z",
  "due_date": "2026-11-30T00:00:00Z",
  "billing_period_start": "2026-10-01T00:00:00Z (optional)",
  "billing_period_end": "2026-10-31T23:59:59Z (optional)",
  "invoice_type": "manual (default) | recurring",
  "currency": "USD (default)",
  "line_items": [
    {
      "description": "Service description",
      "quantity": 1,
      "unit_price": 100.00,
      "tax_rate": 10.00,
      "discount_amount": 0.00
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": { /* invoice object */ },
  "message": "Invoice created successfully"
}
```

---

### Issue Invoice
```
POST /api/v1/invoices/{id}/issue
```

Changes invoice status from `draft` to `open`.

**Permissions:** `manage_payments` or `all`

**Response:**
```json
{
  "success": true,
  "data": { /* invoice object */ },
  "message": "Invoice issued successfully"
}
```

---

### Void Invoice
```
POST /api/v1/invoices/{id}/void
```

**Permissions:** `manage_payments` or `all`

**Request Body:**
```json
{
  "reason": "Reason for voiding (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": { /* invoice object */ },
  "message": "Invoice voided successfully"
}
```

---

### Get Invoice Payments
```
GET /api/v1/invoices/{id}/payments
```

**Permissions:** `view_invoices` or `all`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "payment_number": "PAY-20261031-12345",
      "amount": 110.00,
      "payment_date": "2026-10-31T12:00:00Z",
      "payment_method": "credit_card",
      "status": "completed"
    }
  ]
}
```

---

### Download Invoice PDF
```
GET /api/v1/invoices/{id}/pdf
```

**Permissions:** `view_invoices` or `all`

**Response:** PDF file download

---

## Payment Endpoints

### List Payments
```
GET /api/v1/payments
```

**Query Parameters:**
- `page` (integer, default: 1)
- `pageSize` (integer, default: 20)
- `status` (string) - Filter by status: pending, completed, failed, reversed
- `customer_id` (UUID)
- `invoice_id` (UUID)
- `payment_method` (string)
- `from_date` (ISO datetime)
- `to_date` (ISO datetime)

**Permissions:** `manage_payments` or `all`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "payment_number": "PAY-20261031-12345",
      "customer_id": "uuid",
      "invoice_id": "uuid",
      "amount": 110.00,
      "payment_date": "2026-10-31T12:00:00Z",
      "payment_method": "credit_card",
      "status": "completed",
      "customer": { /* customer object */ },
      "invoice": {
        "id": "uuid",
        "invoice_number": "INV-20261031-12345"
      }
    }
  ],
  "pagination": { /* pagination object */ }
}
```

---

### Get Payment Details
```
GET /api/v1/payments/{id}
```

**Permissions:** `manage_payments` or `all`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "payment_number": "PAY-20261031-12345",
    "customer_id": "uuid",
    "invoice_id": "uuid",
    "amount": 110.00,
    "payment_date": "2026-10-31T12:00:00Z",
    "payment_method": "credit_card",
    "external_transaction_id": "ext_tx_123456",
    "status": "completed",
    "notes": "Payment notes",
    "customer": { /* customer object */ },
    "invoice": { /* invoice object */ }
  }
}
```

---

### Record Payment
```
POST /api/v1/payments
```

**Permissions:** `manage_payments` or `all`

**Request Body:**
```json
{
  "invoice_id": "uuid",
  "amount": 110.00,
  "payment_date": "2026-10-31T12:00:00Z",
  "payment_method": "credit_card | bank_transfer | check | cash | other",
  "external_transaction_id": "ext_tx_123456 (optional, for idempotency)",
  "notes": "Payment notes (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": { /* payment object */ },
  "message": "Payment recorded successfully"
}
```

**Notes:**
- Duplicate `external_transaction_id` returns 409 CONFLICT
- Updates invoice `amount_paid`, `amount_due`, and `status`
- Status transitions: `open` → `partially_paid` → `paid`

---

### Reverse Payment
```
POST /api/v1/payments/{id}/reverse
```

**Permissions:** `manage_payments` or `all`

**Request Body:**
```json
{
  "reason": "Reason for reversal (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": { /* payment object with status: reversed */ },
  "message": "Payment reversed successfully"
}
```

---

## Billing Endpoints

### Trigger Manual Billing Run
```
POST /api/v1/billing/run
```

**Permissions:** `manage_payments` or `all`

**Request Body:**
```json
{
  "as_of_date": "2026-10-31T00:00:00Z (optional, defaults to now)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": 123,
    "subscriptions_processed": 50,
    "invoices_created": 45,
    "failures_count": 5,
    "failures": [
      {
        "subscription_id": "uuid",
        "subscription_number": "SUB-20261001-1234",
        "error": "Plan not found"
      }
    ]
  },
  "message": "Billing completed: 45 invoices created from 50 subscriptions"
}
```

---

### List Billing Jobs
```
GET /api/v1/billing/jobs
```

**Query Parameters:**
- `page` (integer, default: 1)
- `pageSize` (integer, default: 20)
- `status` (string) - Filter by status: running, completed, failed

**Permissions:** `manage_payments` or `all`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "status": "completed",
      "started_at": "2026-10-31T00:00:00Z",
      "completed_at": "2026-10-31T00:05:00Z",
      "subscriptions_processed": 50,
      "invoices_created": 45,
      "failures_count": 5,
      "error_log": "[{\"subscription_id\":\"...\",\"error\":\"...\"}]"
    }
  ],
  "pagination": { /* pagination object */ }
}
```

---

### Get Billing Job Details
```
GET /api/v1/billing/jobs/{id}
```

**Permissions:** `manage_payments` or `all`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "status": "completed",
    "started_at": "2026-10-31T00:00:00Z",
    "completed_at": "2026-10-31T00:05:00Z",
    "subscriptions_processed": 50,
    "invoices_created": 45,
    "failures_count": 5,
    "error_log": "[{\"subscription_id\":\"...\",\"error\":\"...\"}]"
  }
}
```

---

## Finance Endpoints

### Get Financial Summary
```
GET /api/v1/finance/summary
```

**Permissions:** `view_analytics` or `all` (finance, admin roles)

**Response:**
```json
{
  "success": true,
  "data": {
    "total_invoices": 150,
    "total_invoiced": 50000.00,
    "total_paid": 45000.00,
    "total_outstanding": 5000.00,
    "total_overdue": 1200.00,
    "by_status": {
      "open": {
        "count": 20,
        "amount_due": 3000.00
      },
      "partially_paid": {
        "count": 5,
        "amount_due": 800.00
      },
      "overdue": {
        "count": 8,
        "amount_due": 1200.00
      },
      "paid": {
        "count": 117,
        "amount_due": 0.00
      }
    }
  }
}
```

---

### Get Outstanding Balances
```
GET /api/v1/finance/outstanding-balances
```

**Query Parameters:**
- `page` (integer, default: 1)
- `pageSize` (integer, default: 20)
- `customer_id` (UUID, optional)

**Permissions:** `view_analytics` or `all`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "customer_id": "uuid",
      "company_name": "Acme Corp",
      "email": "billing@acme.com",
      "total_outstanding": 2500.00,
      "invoice_count": 5
    }
  ],
  "pagination": { /* pagination object */ }
}
```

---

## Role-Based Access Control

| Endpoint | admin | finance | sales | customer |
|----------|-------|---------|-------|----------|
| List Invoices | ✓ | ✓ | - | Own only |
| Get Invoice | ✓ | ✓ | - | Own only |
| Create Invoice | ✓ | ✓ | - | - |
| Issue Invoice | ✓ | ✓ | - | - |
| Void Invoice | ✓ | ✓ | - | - |
| Download PDF | ✓ | ✓ | - | Own only |
| List Payments | ✓ | ✓ | - | - |
| Record Payment | ✓ | ✓ | - | - |
| Reverse Payment | ✓ | ✓ | - | - |
| Run Billing | ✓ | ✓ | - | - |
| Billing Jobs | ✓ | ✓ | - | - |
| Financial Summary | ✓ | ✓ | - | - |
| Outstanding Balances | ✓ | ✓ | - | - |

---

## Request/Response Examples

### Example: Create and Pay Invoice

**1. Create Invoice**
```bash
POST /api/v1/invoices
Authorization: Bearer <token>
Content-Type: application/json

{
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "invoice_date": "2026-10-31T00:00:00Z",
  "due_date": "2026-11-30T00:00:00Z",
  "line_items": [
    {
      "description": "Pro Plan - Monthly",
      "quantity": 1,
      "unit_price": 99.00,
      "tax_rate": 10.00
    }
  ]
}
```

**2. Issue Invoice**
```bash
POST /api/v1/invoices/550e8400-e29b-41d4-a716-446655440001/issue
Authorization: Bearer <token>
```

**3. Record Payment**
```bash
POST /api/v1/payments
Authorization: Bearer <token>
Content-Type: application/json

{
  "invoice_id": "550e8400-e29b-41d4-a716-446655440001",
  "amount": 108.90,
  "payment_date": "2026-11-15T10:30:00Z",
  "payment_method": "credit_card",
  "external_transaction_id": "stripe_ch_abc123"
}
```

---

## Integration Notes

### Module 2 (Subscriptions) Integration
- Billing engine reads from `Subscription` model
- Updates `subscription.next_billing_date` after billing
- Creates invoices with `subscription_id` reference

### Module 4 (Analytics) Integration
- Financial summary data available via `/finance/summary`
- Outstanding balances data available via `/finance/outstanding-balances`
- Invoice and payment data can be queried for reports

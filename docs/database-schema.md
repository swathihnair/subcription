# Database Schema & Data Models

This document defines the shared data models for SubscriptIQ. All developers must adhere to these schemas to ensure seamless integration.

## Key Principles

- All IDs are UUIDs (v4)
- All timestamps are UTC in ISO 8601 format
- Monetary values use NUMERIC(15, 2) type
- Foreign keys enforce referential integrity
- Soft deletes use `is_deleted` flag where applicable
- Status values are documented enums

## Core Models

### users

Represents platform users with role-based access control.

**Owner:** Module 1 (Core)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| email | VARCHAR(120) | UNIQUE, NOT NULL | User's email |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| first_name | VARCHAR(50) | NULL | First name |
| last_name | VARCHAR(50) | NULL | Last name |
| role_id | UUID | NOT NULL, FK(roles.id) | User's role |
| customer_id | UUID | NULL, FK(customers.id) | Associated customer (for customer users) |
| is_active | BOOLEAN | DEFAULT true | Account active status |
| is_deleted | BOOLEAN | DEFAULT false | Soft delete flag |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| last_login_at | TIMESTAMP | NULL | Last login timestamp |

**Indexes:**
- email (unique)
- role_id
- is_active

### roles

Defines user roles and permissions.

**Owner:** Module 1 (Core)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| name | VARCHAR(50) | UNIQUE, NOT NULL | Role name (admin, finance, sales, customer) |
| description | VARCHAR(255) | NULL | Role description |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Pre-defined Roles:**
- `admin` - Full platform access
- `finance` - Invoice, payment, and financial reporting access
- `sales` - Customer, product, and subscription management
- `customer` - Limited portal access to own data

### customers

Represents billing and business customers.

**Owner:** Module 2 (Sales & Subscriptions)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Customer name |
| email | VARCHAR(120) | UNIQUE, NOT NULL | Customer email |
| status | VARCHAR(50) | NOT NULL | Status (active, inactive, churned) |
| phone | VARCHAR(20) | NULL | Phone number |
| billing_address | TEXT | NULL | Billing address |
| shipping_address | TEXT | NULL | Shipping address |
| total_contract_value | NUMERIC(15,2) | DEFAULT 0 | Total contract value |
| annual_recurring_revenue | NUMERIC(15,2) | DEFAULT 0 | ARR |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- email (unique)
- status

**Relationships:**
- 1 Customer → Many Users
- 1 Customer → Many Subscriptions
- 1 Customer → Many Invoices
- 1 Customer → Many Quotations

### products

Represents products in the catalog.

**Owner:** Module 2 (Sales & Subscriptions)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Product name |
| sku | VARCHAR(100) | UNIQUE, NOT NULL | Stock keeping unit |
| description | TEXT | NULL | Product description |
| status | VARCHAR(50) | NOT NULL | Status (active, discontinued, draft) |
| base_price | NUMERIC(15,2) | NOT NULL | Base price |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- sku (unique)
- status

**Relationships:**
- 1 Product → Many Plans

### plans

Represents billing plans for products.

**Owner:** Module 2 (Sales & Subscriptions)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| product_id | UUID | NOT NULL, FK(products.id) | Associated product |
| name | VARCHAR(255) | NOT NULL | Plan name |
| description | TEXT | NULL | Plan description |
| status | VARCHAR(50) | NOT NULL | Status (active, inactive) |
| price | NUMERIC(15,2) | NOT NULL | Recurring price |
| billing_cycle | VARCHAR(20) | NOT NULL | Cycle (monthly, quarterly, annually) |
| setup_fee | NUMERIC(15,2) | DEFAULT 0 | One-time setup fee |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- product_id
- status

**Relationships:**
- Many Plans → 1 Product
- 1 Plan → Many Subscriptions
- 1 Plan → Many Quotations

### subscriptions

Represents active customer subscriptions.

**Owner:** Module 2 (Sales & Subscriptions) - leads, coordinated with Module 3

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| customer_id | UUID | NOT NULL, FK(customers.id) | Associated customer |
| plan_id | UUID | NOT NULL, FK(plans.id) | Associated plan |
| subscription_number | VARCHAR(100) | UNIQUE, NOT NULL | Subscription reference number |
| status | VARCHAR(50) | NOT NULL | Status (active, suspended, cancelled, churned) |
| monthly_recurring_revenue | NUMERIC(15,2) | DEFAULT 0 | Monthly billing amount |
| annual_contract_value | NUMERIC(15,2) | DEFAULT 0 | Total annual value |
| start_date | TIMESTAMP | NOT NULL | Subscription start date |
| end_date | TIMESTAMP | NULL | Subscription end date |
| next_billing_date | TIMESTAMP | NULL | Next billing date |
| auto_renew | BOOLEAN | DEFAULT true | Auto-renewal flag |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- customer_id
- plan_id
- subscription_number (unique)
- status
- next_billing_date

**Relationships:**
- Many Subscriptions → 1 Customer
- Many Subscriptions → 1 Plan
- 1 Subscription → Many Invoices

### quotations

Represents sales quotations.

**Owner:** Module 2 (Sales & Subscriptions)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| customer_id | UUID | NOT NULL, FK(customers.id) | Associated customer |
| plan_id | UUID | NOT NULL, FK(plans.id) | Associated plan |
| quote_number | VARCHAR(100) | UNIQUE, NOT NULL | Quote reference number |
| status | VARCHAR(50) | NOT NULL | Status (draft, sent, accepted, rejected, expired) |
| amount | NUMERIC(15,2) | NOT NULL | Base amount |
| discount_amount | NUMERIC(15,2) | DEFAULT 0 | Discount amount |
| total_amount | NUMERIC(15,2) | NOT NULL | Total amount after discount |
| valid_until | TIMESTAMP | NULL | Quote expiration date |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- customer_id
- quote_number (unique)
- status

### invoices

Represents customer invoices.

**Owner:** Module 3 (Billing & Payments)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| customer_id | UUID | NOT NULL, FK(customers.id) | Associated customer |
| subscription_id | UUID | NULL, FK(subscriptions.id) | Associated subscription |
| invoice_number | VARCHAR(100) | UNIQUE, NOT NULL | Invoice number |
| status | VARCHAR(50) | NOT NULL | Status (draft, sent, paid, overdue, cancelled) |
| subtotal | NUMERIC(15,2) | NOT NULL | Subtotal before tax |
| tax_amount | NUMERIC(15,2) | DEFAULT 0 | Tax amount |
| discount_amount | NUMERIC(15,2) | DEFAULT 0 | Discount amount |
| total_amount | NUMERIC(15,2) | NOT NULL | Total amount |
| amount_paid | NUMERIC(15,2) | DEFAULT 0 | Amount paid |
| amount_due | NUMERIC(15,2) | NOT NULL | Amount remaining |
| invoice_date | TIMESTAMP | NOT NULL | Invoice date |
| due_date | TIMESTAMP | NOT NULL | Payment due date |
| sent_date | TIMESTAMP | NULL | Date sent to customer |
| notes | TEXT | NULL | Internal notes |
| memo | TEXT | NULL | Customer-visible memo |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- customer_id
- subscription_id
- invoice_number (unique)
- status
- due_date

**Relationships:**
- Many Invoices → 1 Customer
- Many Invoices → 1 Subscription
- 1 Invoice → Many InvoiceLineItems
- 1 Invoice → Many Payments

### invoice_line_items

Represents line items on invoices.

**Owner:** Module 3 (Billing & Payments)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| invoice_id | UUID | NOT NULL, FK(invoices.id) | Associated invoice |
| description | VARCHAR(500) | NOT NULL | Item description |
| quantity | NUMERIC(10,2) | NOT NULL | Quantity |
| unit_price | NUMERIC(15,2) | NOT NULL | Price per unit |
| tax_rate | NUMERIC(5,2) | DEFAULT 0 | Tax rate as percentage |
| line_total | NUMERIC(15,2) | NOT NULL | Total for line |
| tax_total | NUMERIC(15,2) | DEFAULT 0 | Tax for line |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- invoice_id

**Relationships:**
- Many InvoiceLineItems → 1 Invoice

### payments

Represents customer payments.

**Owner:** Module 3 (Billing & Payments)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| invoice_id | UUID | NOT NULL, FK(invoices.id) | Associated invoice |
| customer_id | UUID | NOT NULL, FK(customers.id) | Customer |
| payment_number | VARCHAR(100) | UNIQUE, NOT NULL | Payment reference number |
| status | VARCHAR(50) | NOT NULL | Status (pending, processing, completed, failed, refunded) |
| amount | NUMERIC(15,2) | NOT NULL | Payment amount |
| payment_method | VARCHAR(50) | NULL | Method (credit_card, bank_transfer, check) |
| external_transaction_id | VARCHAR(255) | NULL | External provider transaction ID |
| payment_date | TIMESTAMP | NOT NULL | Payment date |
| processed_at | TIMESTAMP | NULL | Date payment was processed |
| notes | TEXT | NULL | Payment notes |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- invoice_id
- customer_id
- payment_number (unique)
- status

**Relationships:**
- Many Payments → 1 Invoice
- Many Payments → 1 Customer

### audit_logs

Represents system audit trail.

**Owner:** Module 4 (Analytics & Notifications)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | NULL, FK(users.id) | User who performed action |
| action | VARCHAR(100) | NOT NULL | Action type (created, updated, deleted, login) |
| entity_type | VARCHAR(100) | NOT NULL | Entity type (User, Invoice, etc.) |
| entity_id | UUID | NULL | Entity ID |
| old_values | JSON | NULL | Previous values |
| new_values | JSON | NULL | New values |
| ip_address | VARCHAR(50) | NULL | Request IP address |
| user_agent | VARCHAR(500) | NULL | User agent string |
| created_at | TIMESTAMP | NOT NULL, INDEX | Creation timestamp |

**Indexes:**
- user_id
- entity_type
- entity_id
- created_at

**Relationships:**
- Many AuditLogs → 1 User

### notifications

Represents system notifications.

**Owner:** Module 4 (Analytics & Notifications)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| customer_id | UUID | NULL, FK(customers.id) | Associated customer |
| user_id | UUID | NULL, FK(users.id) | Associated user |
| type | VARCHAR(100) | NOT NULL | Notification type |
| subject | VARCHAR(255) | NOT NULL | Subject line |
| message | TEXT | NOT NULL | Notification message |
| is_read | BOOLEAN | DEFAULT false | Read status |
| is_sent | BOOLEAN | DEFAULT false | Sent status |
| channel | VARCHAR(50) | DEFAULT 'in_app' | Channel (in_app, email, sms) |
| external_id | VARCHAR(255) | NULL | External provider ID |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| sent_at | TIMESTAMP | NULL | Date sent |
| read_at | TIMESTAMP | NULL | Date read |

**Indexes:**
- customer_id
- user_id
- is_read
- created_at

**Relationships:**
- Many Notifications → 1 Customer
- Many Notifications → 1 User

## Database Constraints

### Foreign Keys

- All foreign keys enforce ON DELETE CASCADE where appropriate
- Payment methods use VARCHAR to avoid tight coupling with payment systems
- External IDs are stored as VARCHAR for flexibility with various providers

### Uniqueness

- Users: email unique per system
- Products: sku unique
- Customers: email unique
- Invoices: invoice_number unique
- Subscriptions: subscription_number unique
- Quotations: quote_number unique
- Payments: payment_number unique
- Roles: name unique

## Migration Strategy

- Flask-Migrate handles all schema changes
- Developers never manually execute DDL
- Each schema change requires a new migration file
- Migrations run in order during deployment
- Backward compatibility maintained where possible

## Data Consistency

- Monetary fields never use floating-point math in application layer
- All calculations in backend using NUMERIC type
- Timestamps always in UTC
- Status values validated at database level where feasible
- Foreign key constraints enforced at database level

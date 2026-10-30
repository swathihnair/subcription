# SubscriptIQ Architecture

## System Overview

SubscriptIQ is a modular subscription management platform with a shared core and four independent feature modules. The architecture enables parallel development while maintaining data consistency and API contracts.

## Layered Architecture

### Backend Stack

```
┌─────────────────────────────────────────────┐
│         API Layer (Flask Blueprints)        │
│  /auth, /customers, /invoices, /analytics  │
└──────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│      Business Logic Layer (Services)        │
│    Auth, Customer, Invoice, Analytics Svcs  │
└──────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│     Data Access Layer (SQLAlchemy ORM)      │
│         Models for all entities             │
└──────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────┐
│      Database Layer (PostgreSQL)            │
│    Roles, Users, Customers, Subscriptions   │
└──────────────────────────────────────────────┘
```

### Frontend Stack

```
┌──────────────────────────────────────┐
│      Pages & Feature Components      │
│  Login, Dashboard, Customer Portal   │
└──────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────┐
│    Shared UI Components & Layouts    │
│  Button, Input, Card, Navigation     │
└──────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────┐
│   Hooks & State Management           │
│  useAuth, useQuery, useForm           │
└──────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────┐
│       API Client & Services          │
│   Authentication, Data Fetching      │
└──────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────┐
│      REST API (/api/v1)              │
└──────────────────────────────────────┘
```

## Module Organization

### Module 1: Core Platform (You)

**Responsibility:** Foundation, auth, shared models, UI framework

**Deliverables:**
- Authentication system (login, JWT tokens, password hashing)
- User and role management
- Shared database models
- API response format contracts
- Frontend authentication flows
- Shared UI components library
- Deployment and testing infrastructure

**Database Ownership:**
- users
- roles
- audit_logs (shared with Module 4)
- notifications (shared with Module 4)

### Module 2: Sales & Subscriptions

**Responsibility:** Customer and subscription management

**Database Ownership:**
- customers
- products
- plans
- quotations
- subscriptions

**Key Endpoints:**
- `POST /customers` - Create customer
- `GET /customers/{id}` - Fetch customer
- `POST /subscriptions` - Create subscription

### Module 3: Billing & Payments

**Responsibility:** Invoicing and payment processing

**Database Ownership:**
- invoices
- invoice_line_items
- payments

**Key Endpoints:**
- `POST /invoices` - Create invoice
- `POST /invoices/{id}/send` - Send invoice to customer
- `POST /payments` - Record payment

### Module 4: Analytics & Notifications

**Responsibility:** Reporting, customer portal, notifications

**Database Ownership:**
- audit_logs (shared with Module 1)
- notifications (shared with Module 1)

**Key Endpoints:**
- `GET /analytics/dashboard` - Dashboard metrics
- `GET /notifications` - List user notifications
- `POST /notifications/{id}/read` - Mark notification read

## Directory Structure

```
subscriptiq/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # App factory
│   │   ├── extensions.py            # DB, JWT, CORS
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # User, Role models
│   │   │   ├── core.py              # Shared business models
│   │   │   ├── billing.py           # Invoice, Payment models
│   │   │   └── audit.py             # AuditLog, Notification models
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── routes.py            # Auth endpoints
│   │   └── api/
│   │       └── __init__.py          # API blueprint
│   ├── migrations/                  # Flask-Migrate migrations
│   ├── tests/
│   ├── config.py                    # Configuration
│   ├── requirements.txt
│   └── run.py                       # Entry point
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Main app component
│   │   ├── main.tsx                 # Entry point
│   │   ├── index.css                # Global styles
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx   # Auth guard
│   │   │   └── ui/                  # Reusable components
│   │   ├── pages/                   # Page components
│   │   ├── services/
│   │   │   ├── api.ts               # HTTP client
│   │   │   └── auth.ts              # Auth service
│   │   ├── hooks/
│   │   │   └── useAuth.ts           # Auth state
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript types
│   │   └── utils/
│   │       └── cn.ts                # Utility functions
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── docs/
│   ├── api-contracts.md             # API specs
│   ├── database-schema.md           # Data models
│   ├── architecture.md              # This file
│   ├── git-workflow.md              # Git guidelines
│   └── integration-checklist.md     # Pre-merge checklist
│
├── .env.example                     # Environment template
├── .gitignore
├── README.md
└── docker-compose.yml               # Local dev environment
```

## Data Flow

### Authentication Flow

```
User Login (Frontend)
        ↓
POST /auth/login (Backend)
        ↓
Validate credentials
Generate JWT tokens
        ↓
Response with tokens + user
        ↓
Store in localStorage (Frontend)
        ↓
Attach to all subsequent requests
        ↓
Protected routes check token validity
```

### API Request Flow (Protected Route)

```
React Component
        ↓
Calls useQuery() or custom hook
        ↓
API Service (api.ts)
        ↓
Adds JWT token from localStorage
        ↓
Makes HTTP request to /api/v1/{endpoint}
        ↓
Backend receives request
        ↓
JWT middleware validates token
        ↓
Route handler processes request
        ↓
ORM queries database
        ↓
Return formatted response
        ↓
Response interceptor handles 401/refresh
        ↓
Update UI with data
```

## Security Architecture

### Authentication

- JWTs for stateless API authentication
- Access tokens: 1-hour expiry (configurable)
- Refresh tokens: 30-day expiry (configurable)
- Passwords hashed with Werkzeug (bcrypt)
- CORS configured for frontend origin only

### Authorization

- Role-based access control (RBAC)
- Permissions checked at API endpoint level
- Backend enforces permissions (never frontend-only)
- Users cannot access other users' records via ID manipulation
- Audit logging for administrative actions

### Data Protection

- No secrets in version control
- Environment variables for sensitive config
- HTTPS required in production (via reverse proxy)
- Database connections pooled and encrypted
- Sensitive data never logged (passwords, tokens, card info)

## Integration Points

### Module 2 Integration

Module 1 provides:
- User authentication for sales team
- Shared customer model
- Audit logging hooks

Module 2 implements:
- Customer CRUD endpoints
- Subscription management
- Quotation workflow

**Data Contracts:**
- Customer model schema finalized (see database-schema.md)
- Subscription status values documented
- Quotation lifecycle documented

### Module 3 Integration

Module 1 provides:
- User authentication for finance team
- Audit logging for invoice changes

Module 3 implements:
- Invoice generation and management
- Payment processing
- Invoice delivery

**Data Contracts:**
- Invoice numbering scheme agreed
- Payment method types documented
- Monetary field precision (NUMERIC 15,2)

### Module 4 Integration

Module 1 provides:
- User/customer identity system
- Core notification infrastructure

Module 4 implements:
- Analytics dashboard
- Notification delivery (email, in-app)
- Audit log search and filtering

**Data Contracts:**
- Notification type enumeration
- Activity event types documented
- Analytics data points defined

## Database Initialization

```
Flask app startup
        ↓
SQLAlchemy engine created
        ↓
Flask-Migrate checked for pending migrations
        ↓
Migrations applied in order
        ↓
Tables created/modified
        ↓
Seed initial roles (admin, finance, sales, customer)
        ↓
Database ready
```

## Configuration Management

### Development

```
.env.example → .env
├── FLASK_ENV=development
├── DATABASE_URL=postgresql://...
├── JWT_SECRET_KEY=dev-key
└── CORS_ORIGINS=http://localhost:5173
```

### Testing

```
config.py[TestingConfig]
├── SQLALCHEMY_DATABASE_URI=sqlite:///:memory:
├── TESTING=True
└── Short token expiry
```

### Production

```
.env (not in git)
├── FLASK_ENV=production
├── DATABASE_URL=<real-db>
├── JWT_SECRET_KEY=<strong-random-key>
└── CORS_ORIGINS=https://subscriptiq.com
```

## Performance Considerations

- Connection pooling for database
- Token caching in localStorage
- React Query for API response caching
- Lazy loading of pages/features
- Pagination for large datasets
- Indexes on frequently queried columns

## Error Handling Strategy

- Consistent error response format (see api-contracts.md)
- Validation errors include field-level details
- Authorization errors distinguish between unauthorized (401) and forbidden (403)
- Server errors logged without sensitive data
- Frontend shows user-friendly error messages

## Testing Strategy

### Backend

- Unit tests for models and services
- Integration tests for API endpoints
- Auth flow testing (login, refresh, logout)
- Permission and role testing
- Database migration testing

### Frontend

- Component rendering tests
- Hook tests (useAuth)
- API service tests
- Protected route tests
- Form validation tests

## Deployment Architecture

```
Developer
    ↓
Push to feature branch
    ↓
GitHub PR (code review)
    ↓
CI/CD Pipeline
├── Run linters
├── Run tests
├── Build frontend
└── Build backend
    ↓
Approved + Merge to main
    ↓
Production Deployment
├── Database migrations
├── Backend deployment
├── Frontend deployment
└── Health checks
```

## Monitoring & Observability

- Structured logging (JSON format)
- Application logs in `logs/subscriptiq.log`
- Audit trails in `audit_logs` table
- Performance metrics collectible via APM tools
- Error tracking integration ready (Sentry, etc.)

## Future Scaling

- Microservices separation (each module could be independent)
- Message queues for async operations (Celery + Redis)
- Caching layer (Redis) for frequently accessed data
- Search service (Elasticsearch) for analytics queries
- CDN for frontend assets
- Database read replicas for analytics queries

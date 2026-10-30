# SubscriptIQ - Subscription Management & Revenue Intelligence Platform

A comprehensive subscription management platform developed by Brightloop Software, designed for tracking, analyzing, and optimizing recurring revenue across enterprise accounts.

## Project Overview

SubscriptIQ consists of four independent modules integrated on a shared core platform:

- **Module 1 (Core Platform)**: Authentication, shared models, API contracts, frontend foundation
- **Module 2 (Sales & Subscriptions)**: Customer, Product, Plan, Quotation, Subscription management
- **Module 3 (Billing & Payments)**: Invoice, Payment, Billing cycle management
- **Module 4 (Analytics & Notifications)**: Customer portal, Analytics, Notifications, Audit logs

## Technology Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS + shadcn/ui
- React Router v6
- TanStack Query for data fetching
- React Hook Form + Zod for forms
- Recharts for analytics

**Backend:**
- Python 3.10+
- Flask framework
- Flask-SQLAlchemy ORM
- Flask-JWT-Extended for authentication
- PostgreSQL database
- pytest for testing

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- PostgreSQL 13+
- Git

## Local Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd subscriptiq
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your local configuration

# Initialize database
flask db upgrade

# Run backend (development)
flask run
```

Backend runs on `http://localhost:5000` by default.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp ../.env.example .env.local
# Edit .env.local with API URL and settings

# Start development server
npm run dev
```

Frontend runs on `http://localhost:5173` by default.

## Database Setup

### Initialize PostgreSQL

```bash
# Create database and user
createdb subscriptiq_db
psql subscriptiq_db -c "CREATE USER subscriptiq_user WITH PASSWORD 'dev_password';"
psql subscriptiq_db -c "ALTER ROLE subscriptiq_user WITH CREATEDB;"
```

### Run Migrations

```bash
cd backend
flask db upgrade
```

### Create Admin User

```bash
cd backend
python
>>> from app import create_app, db
>>> from app.models import User, Role
>>> app = create_app()
>>> app.app_context().push()
>>> admin_role = Role.query.filter_by(name='admin').first()
>>> admin_user = User(email='admin@example.com', role_id=admin_role.id)
>>> admin_user.set_password('secure_password')
>>> db.session.add(admin_user)
>>> db.session.commit()
```

## Available Commands

### Backend

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Format code
black app/
flake8 app/

# Create new migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade
```

### Frontend

```bash
# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Format and lint
npm run lint
npm run format
```

## Environment Configuration

See `.env.example` for all available configuration options.

Key variables:
- `FLASK_ENV`: development, testing, or production
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `FRONTEND_URL`: Frontend origin for CORS

## API Documentation

API contracts and endpoint documentation are available in `docs/api-contracts.md`.

Base path: `/api/v1`

## Git Workflow

Each developer works on their assigned module on a dedicated branch:

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature or module branches

See `docs/git-workflow.md` for detailed guidelines.

## Module Assignments

- **Member 1**: Core Platform (auth, models, shared components)
- **Member 2**: Sales & Subscriptions
- **Member 3**: Billing & Payments
- **Member 4**: Analytics & Notifications

## Documentation

- `docs/architecture.md` - System design and structure
- `docs/database-schema.md` - Data model definitions
- `docs/api-contracts.md` - API response formats and contracts
- `docs/git-workflow.md` - Git and collaboration guidelines
- `docs/integration-checklist.md` - Pre-merge validation checklist

## Testing

Run all tests before pushing:

```bash
# Backend
pytest

# Frontend
npm run test

# Full integration check
./scripts/test-all.sh
```

## Deployment

Deployment documentation is in `docs/deployment.md` (to be added).

## Support

For questions about the project structure or integration, contact the team lead.

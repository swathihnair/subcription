# Development Quick Start

Get SubscriptIQ running locally in minutes.

## Prerequisites

- Node.js 18+
- Python 3.10+
- PostgreSQL 13+ (or use Docker)
- Git

## One-Time Setup

### 1. Clone & Install Dependencies

```bash
git clone <repo-url>
cd subscriptiq

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### 2. Setup Database

Using Docker (recommended):

```bash
docker-compose up -d postgres
```

Or manually create PostgreSQL:

```sql
createdb subscriptiq_db
createuser subscriptiq_user -P  -- enter: dev_password
```

### 3. Environment Configuration

```bash
# Copy and customize if needed
cp .env.example .env
cp frontend/src/.env.example frontend/src/.env.local
```

### 4. Initialize Database

```bash
cd backend
flask db upgrade
```

### 5. Create Admin User

```bash
cd backend
flask shell
```

```python
from app import create_app, db
from app.models import User, Role

admin_role = Role.query.filter_by(name='admin').first()
admin = User(
    email='admin@local.dev',
    first_name='Admin',
    last_name='User',
    role_id=admin_role.id
)
admin.set_password('password123')
db.session.add(admin)
db.session.commit()
print("✓ Admin created")
exit()
```

## Development Workflow

### Start Backend

```bash
cd backend
flask run
# Server runs on http://localhost:5000
```

### Start Frontend

```bash
cd frontend
npm run dev
# App runs on http://localhost:5173
```

### Run Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test -- --run
```

### Lint & Format

```bash
# Backend
cd backend
flake8 app/
black app/

# Frontend
cd frontend
npm run lint
npm run format
```

## Common Commands

### Backend

```bash
# Create new migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade

# View migration history
flask db history

# Interactive shell with app context
flask shell

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app
```

### Frontend

```bash
# Run development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run all tests
npm run test

# Run tests in watch mode
npm run test

# Type check
tsc -b
```

## Debugging

### Backend Debug Mode

Set in `.env`:

```
FLASK_ENV=development
FLASK_DEBUG=True
```

Backend will auto-reload on code changes.

### Frontend Debug Mode

Open Chrome DevTools (F12) to see:
- React Component Tree (React DevTools extension)
- Network requests
- Application/LocalStorage
- Console errors

### Database

Connect to PostgreSQL:

```bash
psql subscriptiq_db -U subscriptiq_user

# List tables
\dt

# Describe table
\d users

# Query
SELECT * FROM users;

# Exit
\q
```

## Troubleshooting

### Port Already in Use

**Backend (5000):**
```bash
# Find process on port 5000
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows

# Kill it
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

**Frontend (5173):**
```bash
# Kill process on port 5173
lsof -i :5173  # Mac/Linux
taskkill /FI "MEMUSAGE gt 1" /IM node.exe  # Windows
```

### Database Connection Error

```bash
# Check PostgreSQL is running
psql -U subscriptiq_user -d subscriptiq_db -c "SELECT 1"

# Start PostgreSQL (Docker)
docker-compose up -d postgres

# Start PostgreSQL (Mac/Homebrew)
brew services start postgresql

# Start PostgreSQL (Linux)
sudo systemctl start postgresql
```

### Migration Issues

```bash
# Reset database (development only!)
flask db downgrade base
flask db upgrade

# Or drop and recreate:
# dropdb subscriptiq_db
# createdb subscriptiq_db
# flask db upgrade
```

### Dependencies Issue

```bash
# Backend
pip install -r requirements.txt --force-reinstall

# Frontend
rm -rf node_modules package-lock.json
npm install
```

### Login Not Working

```bash
# Check user exists
cd backend
flask shell
from app.models import User
User.query.filter_by(email='admin@local.dev').first()
```

## File Structure Quick Reference

```
subscriptiq/
├── backend/          # Flask API
│   ├── app/
│   │   ├── models/   # Database models
│   │   ├── auth/     # Authentication routes
│   │   ├── api/      # API routes
│   │   └── extensions.py
│   ├── tests/        # Tests
│   └── run.py        # Entry point
├── frontend/         # React app
│   ├── src/
│   │   ├── pages/    # Page components
│   │   ├── components/ # Reusable components
│   │   ├── hooks/    # React hooks
│   │   ├── services/ # API client
│   │   └── types/    # TypeScript types
│   └── package.json
├── docs/             # Documentation
└── README.md         # Project overview
```

## IDE Setup

### VS Code (Recommended)

Extensions:
- Python
- ESLint
- Prettier - Code formatter
- Thunder Client or REST Client (for API testing)
- SQLTools with PostgreSQL driver

Settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  }
}
```

### PyCharm

- Open `backend/` as project
- Set Python interpreter to venv
- Enable Django/Flask support if needed

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/description

# Make changes and commit
git add .
git commit -m "type(scope): description"

# Push to remote
git push -u origin feature/description

# Create pull request on GitHub
```

See `docs/git-workflow.md` for detailed guidelines.

## API Testing

### Using Thunder Client (VS Code)

1. Install Thunder Client extension
2. Create request to `http://localhost:5000/api/v1/auth/login`
3. Method: POST
4. Body:
```json
{
  "email": "admin@local.dev",
  "password": "password123"
}
```

### Using curl

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@local.dev","password":"password123"}'
```

## Performance Tips

- Frontend: Use React DevTools Profiler to find slow components
- Backend: Use Flask-DebugToolbar for query analysis
- Database: Check slow queries: `ANALYZE` and `EXPLAIN`
- Use `npm run build` to check final bundle size

## Documentation

- **Architecture**: `docs/architecture.md`
- **API Contracts**: `docs/api-contracts.md`
- **Database Schema**: `docs/database-schema.md`
- **Git Workflow**: `docs/git-workflow.md`
- **Integration Checklist**: `docs/integration-checklist.md`

## Getting Help

1. Check README.md for overview
2. Check relevant docs/ file
3. Search existing GitHub issues
4. Create new GitHub issue with:
   - What you tried
   - What happened
   - Error messages
   - Your environment (OS, Python version, etc.)

---

Happy coding! 🚀

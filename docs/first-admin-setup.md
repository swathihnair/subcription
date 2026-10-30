# Creating the First Admin User

This guide explains how to create the first administrator account for SubscriptIQ.

## Prerequisites

- Backend is running: `flask run`
- Database is initialized: `flask db upgrade`
- PostgreSQL is accessible

## Option 1: Using Flask Shell (Recommended)

```bash
cd backend
flask shell
```

In the Flask shell:

```python
from app import create_app, db
from app.models import User, Role

# Get admin role
admin_role = Role.query.filter_by(name='admin').first()

# Create admin user
admin = User(
    email='admin@subscriptiq.local',
    first_name='Administrator',
    last_name='Account',
    role_id=admin_role.id,
    is_active=True
)

# Set a secure password (minimum 8 characters)
admin.set_password('your-secure-password-here')

# Save to database
db.session.add(admin)
db.session.commit()

print(f"Admin user created: {admin.email}")
exit()
```

## Option 2: Using Python Script

Create a script file `create_admin.py` in the backend directory:

```python
import sys
from app import create_app, db
from app.models import User, Role

app = create_app()

with app.app_context():
    # Check if admin already exists
    existing = User.query.filter_by(email='admin@subscriptiq.local').first()
    if existing:
        print("Admin user already exists!")
        sys.exit(1)
    
    # Get admin role
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("Admin role not found!")
        sys.exit(1)
    
    # Create admin user
    admin = User(
        email='admin@subscriptiq.local',
        first_name='Administrator',
        last_name='Account',
        role_id=admin_role.id,
        is_active=True
    )
    
    admin.set_password('your-secure-password-here')
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"✓ Admin user created successfully")
    print(f"  Email: {admin.email}")
    print(f"  ID: {admin.id}")
```

Run it:

```bash
python create_admin.py
```

## Login with Admin Account

1. Start the frontend: `npm run dev`
2. Navigate to `http://localhost:5173`
3. Login with:
   - Email: `admin@subscriptiq.local`
   - Password: `your-secure-password-here`

## Creating Additional Users

Once you have an admin account, you can create other users via the application UI (when implemented) or using the Flask shell:

```bash
cd backend
flask shell
```

```python
from app import db
from app.models import User, Role

# Create a finance user
finance_role = Role.query.filter_by(name='finance').first()
finance_user = User(
    email='finance@subscriptiq.local',
    first_name='Finance',
    last_name='Team',
    role_id=finance_role.id,
    is_active=True
)
finance_user.set_password('secure-password')
db.session.add(finance_user)
db.session.commit()

# Create a sales user
sales_role = Role.query.filter_by(name='sales').first()
sales_user = User(
    email='sales@subscriptiq.local',
    first_name='Sales',
    last_name='Team',
    role_id=sales_role.id,
    is_active=True
)
sales_user.set_password('secure-password')
db.session.add(sales_user)
db.session.commit()

print("Users created successfully")
exit()
```

## Available Roles

- **admin** - Full platform access
- **finance** - Invoice, payment, and financial reporting
- **sales** - Customer, product, and subscription management
- **customer** - Limited portal access to own data

## Password Requirements

- Minimum 8 characters
- Recommended: Mix of uppercase, lowercase, numbers, and symbols

## Security Tips

- **Never share** credentials
- **Change default password** immediately after first login
- **Use strong passwords** (16+ characters for admin)
- **Rotate passwords** periodically
- **Enable two-factor authentication** when implemented
- **Audit login attempts** using audit logs

## Troubleshooting

### "Admin role not found"

Ensure database migrations have been applied:

```bash
flask db upgrade
```

### "User with this email already exists"

Check if user already created:

```python
from app.models import User
user = User.query.filter_by(email='admin@subscriptiq.local').first()
if user:
    print(f"User exists: {user.email}")
```

### "Set password failed - password too short"

Password must be at least 8 characters:

```python
user.set_password('at-least-8-chars-long')
```

## Next Steps

1. Create additional users for your team
2. Set up customer accounts (Module 2)
3. Configure products and plans (Module 2)
4. Test subscription workflows
5. Verify invoice generation (Module 3)

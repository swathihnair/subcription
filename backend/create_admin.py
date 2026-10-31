"""Create admin user for testing"""
from app import create_app
from app.extensions import db
from app.models import User, Role

app = create_app()

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@local.dev').first()
    
    if not admin:
        # Get admin role
        admin_role = Role.query.filter_by(name='admin').first()
        
        if not admin_role:
            print("❌ Admin role not found. Database not properly initialized.")
            exit(1)
        
        # Create admin user
        admin = User(
            email='admin@local.dev',
            first_name='Admin',
            last_name='User',
            role_id=admin_role.id,
            is_active=True
        )
        admin.set_password('password123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@local.dev")
        print(f"   Password: password123")
    else:
        print("ℹ️  Admin user already exists")
        print(f"   Email: {admin.email}")

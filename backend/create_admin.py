#!/usr/bin/env python
"""Create admin user for development - simplified version"""
import os
from app import create_app, db
from app.models import User, Role

app = create_app()

with app.app_context():
    # Just recreate the tables from scratch using raw SQL
    db.drop_all()
    db.create_all()
    print("✓ Database reset and recreated")
    
    # Create roles
    roles_data = [
        ('admin', 'Administrator role'),
        ('finance', 'Finance role'),
        ('sales', 'Sales role'),
        ('customer', 'Customer role'),
    ]
    
    for role_name, description in roles_data:
        role = Role(name=role_name, description=description)
        db.session.add(role)
    
    db.session.commit()
    print("✓ Roles created")
    
    # Create admin user
    admin_role = Role.query.filter_by(name='admin').first()
    
    admin = User(
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        role_id=admin_role.id,
        is_active=True
    )
    admin.set_password('password123')
    db.session.add(admin)
    db.session.commit()
    print("✓ Admin user created")
    
    # Verify
    user = User.query.filter_by(email='admin@example.com').first()
    if user:
        print(f"\n✅ Successfully created user in database:")
        print(f"   Email: admin@example.com")
        print(f"   Password: password123")
        print(f"   Role: {user.role.name if user.role else 'None'}")
    else:
        print("✗ Failed to create user")


"""Pytest configuration and fixtures"""
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Role

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test roles
        for role_name in ['admin', 'finance', 'sales', 'customer']:
            role = Role(name=role_name, description=f'{role_name} role')
            db.session.add(role)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def admin_user(app):
    """Create admin test user"""
    admin_role = Role.query.filter_by(name='admin').first()
    user = User(
        email='admin@test.com',
        role_id=admin_role.id,
        first_name='Admin',
        last_name='User'
    )
    user.set_password('testpass123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def customer_user(app):
    """Create customer test user"""
    customer_role = Role.query.filter_by(name='customer').first()
    user = User(
        email='customer@test.com',
        role_id=customer_role.id,
        first_name='Customer',
        last_name='User'
    )
    user.set_password('testpass123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def auth_headers(client, admin_user):
    """Get auth headers for admin user"""
    response = client.post(
        '/api/v1/auth/login',
        json={'email': admin_user.email, 'password': 'testpass123'}
    )
    token = response.json['data']['access_token']
    return {'Authorization': f'Bearer {token}'}

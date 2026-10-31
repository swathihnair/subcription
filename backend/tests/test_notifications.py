"""Tests for notifications - Module 4"""
import pytest
from app import create_app, db
from app.models import User, Role, Customer, Notification
from app.services.notification_service import NotificationService
from flask_jwt_extended import create_access_token
from datetime import datetime

@pytest.fixture
def app():
    """Create test application"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        for role_name in ['admin', 'customer']:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name, description=f'{role_name} role')
                db.session.add(role)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def customer_user(app):
    with app.app_context():
        customer = Customer(name='Test Customer', email='customer@test.com', status='active')
        db.session.add(customer)
        db.session.flush()
        
        customer_role = Role.query.filter_by(name='customer').first()
        user = User(
            email='customer@test.com',
            role_id=customer_role.id,
            customer_id=customer.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

def test_create_notification(app, customer_user):
    """Test creating a notification"""
    with app.app_context():
        notification = NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            'Test Invoice',
            'Your invoice is ready',
            customer_id=customer_user.customer_id
        )
        
        assert notification is not None
        assert notification.type == NotificationService.INVOICE_ISSUED
        assert notification.subject == 'Test Invoice'
        assert notification.is_read is False

def test_get_notifications(app, client, customer_user):
    """Test getting notifications for a user"""
    with app.app_context():
        # Create notifications
        NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            'Invoice 1',
            'Test message 1',
            customer_id=customer_user.customer_id
        )
        NotificationService.create_notification(
            NotificationService.PAYMENT_RECORDED,
            'Payment 1',
            'Test message 2',
            customer_id=customer_user.customer_id
        )
        
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 2

def test_get_unread_count(app, client, customer_user):
    """Test getting unread notification count"""
    with app.app_context():
        # Create notifications
        NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            'Invoice 1',
            'Test message',
            customer_id=customer_user.customer_id
        )
        NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            'Invoice 2',
            'Test message',
            customer_id=customer_user.customer_id
        )
        
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            '/api/v1/notifications/unread-count',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['count'] == 2

def test_mark_notification_read(app, client, customer_user):
    """Test marking notification as read"""
    with app.app_context():
        notification = NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            'Invoice 1',
            'Test message',
            customer_id=customer_user.customer_id
        )
        
        token = create_access_token(identity=str(customer_user.id))
        response = client.post(
            f'/api/v1/notifications/{notification.id}/read',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_read'] is True
        assert data['data']['read_at'] is not None

def test_mark_all_read(app, client, customer_user):
    """Test marking all notifications as read"""
    with app.app_context():
        # Create notifications
        for i in range(3):
            NotificationService.create_notification(
                NotificationService.INVOICE_ISSUED,
                f'Invoice {i}',
                'Test message',
                customer_id=customer_user.customer_id
            )
        
        token = create_access_token(identity=str(customer_user.id))
        response = client.post(
            '/api/v1/notifications/read-all',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify all are read
        unread_count = Notification.query.filter_by(
            customer_id=customer_user.customer_id,
            is_read=False
        ).count()
        assert unread_count == 0

def test_notification_isolation(app, client):
    """Test that users can only access their own notifications"""
    with app.app_context():
        # Create two customers
        customer1 = Customer(name='Customer 1', email='c1@test.com', status='active')
        customer2 = Customer(name='Customer 2', email='c2@test.com', status='active')
        db.session.add_all([customer1, customer2])
        db.session.flush()
        
        customer_role = Role.query.filter_by(name='customer').first()
        
        user1 = User(email='c1@test.com', role_id=customer_role.id, customer_id=customer1.id)
        user1.set_password('password123')
        user2 = User(email='c2@test.com', role_id=customer_role.id, customer_id=customer2.id)
        user2.set_password('password123')
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Create notifications for both
        NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            'Invoice for Customer 1',
            'Test',
            customer_id=customer1.id
        )
        NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            'Invoice for Customer 2',
            'Test',
            customer_id=customer2.id
        )
        
        # User1 should only see their notification
        token1 = create_access_token(identity=str(user1.id))
        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token1}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 1
        assert 'Customer 1' in data['data'][0]['subject']

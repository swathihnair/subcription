"""Tests for customer portal endpoints - Module 4"""
import pytest
from app import create_app, db
from app.models import User, Role, Customer, Subscription, Invoice, Payment, Plan, Product
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

@pytest.fixture
def app():
    """Create test application"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Create roles only if they don't exist
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
    """Create test client"""
    return app.test_client()

@pytest.fixture
def customer_user(app):
    """Create a customer user"""
    with app.app_context():
        # Create customer
        customer = Customer(
            name='Test Customer',
            email='customer@test.com',
            status='active'
        )
        db.session.add(customer)
        db.session.flush()
        
        # Create customer user
        customer_role = Role.query.filter_by(name='customer').first()
        user = User(
            email='customer@test.com',
            role_id=customer_role.id,
            customer_id=customer.id,
            first_name='Test',
            last_name='Customer'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def other_customer_user(app):
    """Create another customer user"""
    with app.app_context():
        customer = Customer(
            name='Other Customer',
            email='other@test.com',
            status='active'
        )
        db.session.add(customer)
        db.session.flush()
        
        customer_role = Role.query.filter_by(name='customer').first()
        user = User(
            email='other@test.com',
            role_id=customer_role.id,
            customer_id=customer.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

def test_get_portal_profile(app, client, customer_user):
    """Test getting customer portal profile"""
    with app.app_context():
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            '/api/v1/portal/me',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['user']['email'] == 'customer@test.com'
        assert data['data']['customer']['name'] == 'Test Customer'

def test_get_portal_subscriptions(app, client, customer_user):
    """Test getting customer subscriptions"""
    with app.app_context():
        # Create product and plan
        product = Product(name='Test Product', sku='TEST-001', base_price=100, status='active')
        db.session.add(product)
        db.session.flush()
        
        plan = Plan(
            product_id=product.id,
            name='Test Plan',
            price=100,
            billing_cycle='monthly',
            status='active'
        )
        db.session.add(plan)
        db.session.flush()
        
        # Create subscription
        subscription = Subscription(
            customer_id=customer_user.customer_id,
            plan_id=plan.id,
            subscription_number='SUB-001',
            status='active',
            start_date=datetime.utcnow(),
            monthly_recurring_revenue=100
        )
        db.session.add(subscription)
        db.session.commit()
        
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            '/api/v1/portal/subscriptions',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['subscription_number'] == 'SUB-001'

def test_cannot_access_other_customer_subscription(app, client, customer_user, other_customer_user):
    """Test that customer cannot access another customer's subscription"""
    with app.app_context():
        # Create product and plan
        product = Product(name='Test Product', sku='TEST-001', base_price=100, status='active')
        db.session.add(product)
        db.session.flush()
        
        plan = Plan(
            product_id=product.id,
            name='Test Plan',
            price=100,
            billing_cycle='monthly',
            status='active'
        )
        db.session.add(plan)
        db.session.flush()
        
        # Create subscription for other customer
        subscription = Subscription(
            customer_id=other_customer_user.customer_id,
            plan_id=plan.id,
            subscription_number='SUB-OTHER',
            status='active',
            start_date=datetime.utcnow()
        )
        db.session.add(subscription)
        db.session.commit()
        
        # Try to access with customer_user token
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            f'/api/v1/portal/subscriptions/{subscription.id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 404

def test_get_portal_invoices(app, client, customer_user):
    """Test getting customer invoices"""
    with app.app_context():
        # Create invoice
        invoice = Invoice(
            customer_id=customer_user.customer_id,
            invoice_number='INV-001',
            status='sent',
            subtotal=100,
            total_amount=100,
            amount_due=100,
            invoice_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(invoice)
        db.session.commit()
        
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            '/api/v1/portal/invoices',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['invoice_number'] == 'INV-001'

def test_cannot_access_other_customer_invoice(app, client, customer_user, other_customer_user):
    """Test that customer cannot access another customer's invoice"""
    with app.app_context():
        # Create invoice for other customer
        invoice = Invoice(
            customer_id=other_customer_user.customer_id,
            invoice_number='INV-OTHER',
            status='sent',
            subtotal=100,
            total_amount=100,
            amount_due=100,
            invoice_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(invoice)
        db.session.commit()
        
        # Try to access with customer_user token
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            f'/api/v1/portal/invoices/{invoice.id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 404

def test_get_portal_payments(app, client, customer_user):
    """Test getting customer payment history"""
    with app.app_context():
        # Create invoice
        invoice = Invoice(
            customer_id=customer_user.customer_id,
            invoice_number='INV-001',
            status='paid',
            subtotal=100,
            total_amount=100,
            amount_due=0,
            amount_paid=100,
            invoice_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(invoice)
        db.session.flush()
        
        # Create payment
        payment = Payment(
            invoice_id=invoice.id,
            customer_id=customer_user.customer_id,
            payment_number='PAY-001',
            status='completed',
            amount=100,
            payment_date=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()
        
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            '/api/v1/portal/payments',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['payment_number'] == 'PAY-001'

def test_update_portal_profile(app, client, customer_user):
    """Test updating customer profile"""
    with app.app_context():
        token = create_access_token(identity=str(customer_user.id))
        response = client.patch(
            '/api/v1/portal/profile',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'first_name': 'Updated',
                'phone': '123-456-7890'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['user']['first_name'] == 'Updated'
        assert data['data']['customer']['phone'] == '123-456-7890'

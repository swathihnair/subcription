"""Tests for analytics endpoints - Module 4"""
import pytest
from app import create_app, db
from app.models import User, Role, Customer, Subscription, Invoice, Payment, Product, Plan
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        for role_name in ['admin', 'finance', 'customer']:
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
def admin_user(app):
    with app.app_context():
        admin_role = Role.query.filter_by(name='admin').first()
        user = User(email='admin@test.com', role_id=admin_role.id)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def customer_user(app):
    with app.app_context():
        customer = Customer(name='Test Customer', email='customer@test.com', status='active')
        db.session.add(customer)
        db.session.flush()
        
        customer_role = Role.query.filter_by(name='customer').first()
        user = User(email='customer@test.com', role_id=customer_role.id, customer_id=customer.id)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

def test_analytics_requires_permission(app, client, customer_user):
    """Test that analytics requires admin/finance permission"""
    with app.app_context():
        token = create_access_token(identity=str(customer_user.id))
        response = client.get(
            '/api/v1/analytics/overview',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 403

def test_get_analytics_overview(app, client, admin_user):
    """Test getting analytics overview"""
    with app.app_context():
        # Create test data
        customer = Customer(name='Test Customer', email='test@test.com', status='active')
        db.session.add(customer)
        db.session.flush()
        
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
        
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            subscription_number='SUB-001',
            status='active',
            start_date=datetime.utcnow(),
            monthly_recurring_revenue=100
        )
        db.session.add(subscription)
        db.session.commit()
        
        token = create_access_token(identity=str(admin_user.id))
        response = client.get(
            '/api/v1/analytics/overview',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['total_customers'] == 1
        assert data['data']['active_subscriptions'] == 1
        assert data['data']['monthly_recurring_revenue'] == 100.0

def test_get_mrr_analytics(app, client, admin_user):
    """Test getting MRR analytics"""
    with app.app_context():
        # Create test subscriptions
        customer = Customer(name='Test Customer', email='test@test.com', status='active')
        db.session.add(customer)
        db.session.flush()
        
        product = Product(name='Test Product', sku='TEST-001', base_price=100, status='active')
        db.session.add(product)
        db.session.flush()
        
        plan1 = Plan(product_id=product.id, name='Plan A', price=50, billing_cycle='monthly', status='active')
        plan2 = Plan(product_id=product.id, name='Plan B', price=100, billing_cycle='monthly', status='active')
        db.session.add_all([plan1, plan2])
        db.session.flush()
        
        sub1 = Subscription(
            customer_id=customer.id,
            plan_id=plan1.id,
            subscription_number='SUB-001',
            status='active',
            start_date=datetime.utcnow(),
            monthly_recurring_revenue=50
        )
        sub2 = Subscription(
            customer_id=customer.id,
            plan_id=plan2.id,
            subscription_number='SUB-002',
            status='active',
            start_date=datetime.utcnow(),
            monthly_recurring_revenue=100
        )
        db.session.add_all([sub1, sub2])
        db.session.commit()
        
        token = create_access_token(identity=str(admin_user.id))
        response = client.get(
            '/api/v1/analytics/mrr',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['current_mrr'] == 150.0
        assert data['data']['arr'] == 1800.0
        assert 'Plan A' in data['data']['by_plan']
        assert 'Plan B' in data['data']['by_plan']

def test_get_subscription_analytics(app, client, admin_user):
    """Test getting subscription analytics"""
    with app.app_context():
        customer = Customer(name='Test Customer', email='test@test.com', status='active')
        db.session.add(customer)
        db.session.flush()
        
        product = Product(name='Test Product', sku='TEST-001', base_price=100, status='active')
        db.session.add(product)
        db.session.flush()
        
        plan = Plan(product_id=product.id, name='Test Plan', price=100, billing_cycle='monthly', status='active')
        db.session.add(plan)
        db.session.flush()
        
        # Create active and cancelled subscriptions
        for i in range(3):
            sub = Subscription(
                customer_id=customer.id,
                plan_id=plan.id,
                subscription_number=f'SUB-00{i}',
                status='active',
                start_date=datetime.utcnow(),
                monthly_recurring_revenue=100
            )
            db.session.add(sub)
        
        cancelled_sub = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            subscription_number='SUB-CANCELLED',
            status='cancelled',
            start_date=datetime.utcnow() - timedelta(days=60),
            end_date=datetime.utcnow()
        )
        db.session.add(cancelled_sub)
        db.session.commit()
        
        token = create_access_token(identity=str(admin_user.id))
        response = client.get(
            '/api/v1/analytics/subscriptions',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['by_status']['active'] == 3
        assert data['data']['by_status']['cancelled'] == 1

def test_get_invoice_analytics(app, client, admin_user):
    """Test getting invoice analytics"""
    with app.app_context():
        customer = Customer(name='Test Customer', email='test@test.com', status='active')
        db.session.add(customer)
        db.session.flush()
        
        # Create invoices with different statuses
        invoice1 = Invoice(
            customer_id=customer.id,
            invoice_number='INV-001',
            status='paid',
            subtotal=100,
            total_amount=100,
            amount_due=0,
            amount_paid=100,
            invoice_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        invoice2 = Invoice(
            customer_id=customer.id,
            invoice_number='INV-002',
            status='overdue',
            subtotal=200,
            total_amount=200,
            amount_due=200,
            invoice_date=datetime.utcnow() - timedelta(days=60),
            due_date=datetime.utcnow() - timedelta(days=30)
        )
        db.session.add_all([invoice1, invoice2])
        db.session.commit()
        
        token = create_access_token(identity=str(admin_user.id))
        response = client.get(
            '/api/v1/analytics/invoices',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'paid' in data['data']['by_status']
        assert 'overdue' in data['data']['by_status']
        assert data['data']['overdue_amount'] == 200.0

def test_get_payment_analytics(app, client, admin_user):
    """Test getting payment analytics"""
    with app.app_context():
        customer = Customer(name='Test Customer', email='test@test.com', status='active')
        db.session.add(customer)
        db.session.flush()
        
        invoice = Invoice(
            customer_id=customer.id,
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
        
        payment = Payment(
            invoice_id=invoice.id,
            customer_id=customer.id,
            payment_number='PAY-001',
            status='completed',
            amount=100,
            payment_method='credit_card',
            payment_date=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()
        
        token = create_access_token(identity=str(admin_user.id))
        response = client.get(
            '/api/v1/analytics/payments',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'completed' in data['data']['by_status']
        assert 'credit_card' in data['data']['by_method']

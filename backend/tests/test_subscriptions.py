"""Tests for subscription API endpoints - Module 2"""
import pytest
from datetime import datetime, timedelta
from app.models import Customer, Product, Plan, Subscription
from decimal import Decimal


def test_get_subscriptions_success(client, auth_headers):
    """Test getting list of subscriptions"""
    response = client.get('/api/v1/subscriptions', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data
    assert 'pagination' in data


def test_create_subscription_success(client, auth_headers, db_session):
    """Test creating a new subscription"""
    # Create customer
    customer = Customer(name='Test Customer', email='sub@test.com', status='active')
    db_session.add(customer)
    
    # Create product and plan
    product = Product(name='Test Product', sku='TEST-001', base_price=Decimal('99.99'), status='active')
    db_session.add(product)
    db_session.flush()
    
    plan = Plan(
        product_id=product.id,
        name='Monthly Plan',
        price=Decimal('99.99'),
        billing_cycle='monthly',
        status='active'
    )
    db_session.add(plan)
    db_session.commit()
    
    payload = {
        'customer_id': str(customer.id),
        'plan_id': str(plan.id),
        'status': 'active'
    }
    
    response = client.post('/api/v1/subscriptions', json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['customer_id'] == str(customer.id)
    assert data['data']['plan_id'] == str(plan.id)
    assert data['data']['status'] == 'active'
    assert 'subscription_number' in data['data']


def test_create_subscription_missing_fields(client, auth_headers):
    """Test creating subscription with missing fields"""
    payload = {
        'customer_id': 'some-id'
        # Missing plan_id
    }
    response = client.post('/api/v1/subscriptions', json=payload, headers=auth_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'VALIDATION_ERROR'


def test_create_subscription_inactive_plan(client, auth_headers, db_session):
    """Test creating subscription with inactive plan"""
    customer = Customer(name='Test Customer', email='sub2@test.com', status='active')
    db_session.add(customer)
    
    product = Product(name='Test Product', sku='TEST-002', base_price=Decimal('99.99'), status='active')
    db_session.add(product)
    db_session.flush()
    
    plan = Plan(
        product_id=product.id,
        name='Inactive Plan',
        price=Decimal('99.99'),
        billing_cycle='monthly',
        status='inactive'
    )
    db_session.add(plan)
    db_session.commit()
    
    payload = {
        'customer_id': str(customer.id),
        'plan_id': str(plan.id)
    }
    
    response = client.post('/api/v1/subscriptions', json=payload, headers=auth_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data['error']['code'] == 'INVALID_STATE'


def test_create_duplicate_active_subscription(client, auth_headers, db_session):
    """Test preventing duplicate active subscriptions"""
    customer = Customer(name='Test Customer', email='sub3@test.com', status='active')
    db_session.add(customer)
    
    product = Product(name='Test Product', sku='TEST-003', base_price=Decimal('99.99'), status='active')
    db_session.add(product)
    db_session.flush()
    
    plan = Plan(
        product_id=product.id,
        name='Duplicate Plan',
        price=Decimal('99.99'),
        billing_cycle='monthly',
        status='active'
    )
    db_session.add(plan)
    db_session.flush()
    
    # Create first subscription
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        subscription_number='SUB-001',
        status='active',
        start_date=datetime.utcnow()
    )
    db_session.add(subscription)
    db_session.commit()
    
    # Try to create duplicate
    payload = {
        'customer_id': str(customer.id),
        'plan_id': str(plan.id)
    }
    
    response = client.post('/api/v1/subscriptions', json=payload, headers=auth_headers)
    assert response.status_code == 409
    data = response.get_json()
    assert data['error']['code'] == 'CONFLICT'


def test_pause_active_subscription(client, auth_headers, db_session):
    """Test pausing an active subscription"""
    customer = Customer(name='Pause Customer', email='pause@test.com', status='active')
    db_session.add(customer)
    
    product = Product(name='Test Product', sku='TEST-004', base_price=Decimal('99.99'), status='active')
    db_session.add(product)
    db_session.flush()
    
    plan = Plan(
        product_id=product.id,
        name='Pause Plan',
        price=Decimal('99.99'),
        billing_cycle='monthly',
        status='active'
    )
    db_session.add(plan)
    db_session.flush()
    
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        subscription_number='SUB-PAUSE',
        status='active',
        start_date=datetime.utcnow()
    )
    db_session.add(subscription)
    db_session.commit()
    
    response = client.post(f'/api/v1/subscriptions/{subscription.id}/pause', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['status'] == 'paused'


def test_resume_paused_subscription(client, auth_headers, db_session):
    """Test resuming a paused subscription"""
    customer = Customer(name='Resume Customer', email='resume@test.com', status='active')
    db_session.add(customer)
    
    product = Product(name='Test Product', sku='TEST-005', base_price=Decimal('99.99'), status='active')
    db_session.add(product)
    db_session.flush()
    
    plan = Plan(
        product_id=product.id,
        name='Resume Plan',
        price=Decimal('99.99'),
        billing_cycle='monthly',
        status='active'
    )
    db_session.add(plan)
    db_session.flush()
    
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        subscription_number='SUB-RESUME',
        status='paused',
        start_date=datetime.utcnow()
    )
    db_session.add(subscription)
    db_session.commit()
    
    response = client.post(f'/api/v1/subscriptions/{subscription.id}/resume', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['status'] == 'active'


def test_cancel_subscription(client, auth_headers, db_session):
    """Test cancelling a subscription"""
    customer = Customer(name='Cancel Customer', email='cancel@test.com', status='active')
    db_session.add(customer)
    
    product = Product(name='Test Product', sku='TEST-006', base_price=Decimal('99.99'), status='active')
    db_session.add(product)
    db_session.flush()
    
    plan = Plan(
        product_id=product.id,
        name='Cancel Plan',
        price=Decimal('99.99'),
        billing_cycle='monthly',
        status='active'
    )
    db_session.add(plan)
    db_session.flush()
    
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        subscription_number='SUB-CANCEL',
        status='active',
        start_date=datetime.utcnow(),
        next_billing_date=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(subscription)
    db_session.commit()
    
    payload = {'cancel_immediately': False}
    response = client.post(f'/api/v1/subscriptions/{subscription.id}/cancel', json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['status'] == 'cancelled'
    assert data['data']['end_date'] is not None


def test_get_subscription_by_id(client, auth_headers, db_session):
    """Test getting subscription by ID"""
    customer = Customer(name='Get Customer', email='get@test.com', status='active')
    db_session.add(customer)
    
    product = Product(name='Test Product', sku='TEST-007', base_price=Decimal('99.99'), status='active')
    db_session.add(product)
    db_session.flush()
    
    plan = Plan(
        product_id=product.id,
        name='Get Plan',
        price=Decimal('99.99'),
        billing_cycle='monthly',
        status='active'
    )
    db_session.add(plan)
    db_session.flush()
    
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        subscription_number='SUB-GET',
        status='active',
        start_date=datetime.utcnow()
    )
    db_session.add(subscription)
    db_session.commit()
    
    response = client.get(f'/api/v1/subscriptions/{subscription.id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['id'] == str(subscription.id)
    assert data['data']['subscription_number'] == 'SUB-GET'

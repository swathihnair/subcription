"""Tests for customer API endpoints - Module 2"""
import pytest
from app.models import Customer, User, Role


def test_get_customers_success(client, auth_headers):
    """Test getting list of customers"""
    response = client.get('/api/v1/customers', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data
    assert 'pagination' in data


def test_get_customers_forbidden(client):
    """Test getting customers without authentication"""
    response = client.get('/api/v1/customers')
    assert response.status_code == 401


def test_create_customer_success(client, auth_headers, db_session):
    """Test creating a new customer"""
    payload = {
        'name': 'Test Corporation',
        'email': 'test@corporation.com',
        'phone': '555-1234',
        'status': 'active'
    }
    response = client.post('/api/v1/customers', json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['name'] == 'Test Corporation'
    assert data['data']['email'] == 'test@corporation.com'


def test_create_customer_missing_fields(client, auth_headers):
    """Test creating customer with missing required fields"""
    payload = {
        'name': 'Test Corp'
        # Missing email
    }
    response = client.post('/api/v1/customers', json=payload, headers=auth_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'VALIDATION_ERROR'


def test_create_customer_duplicate_email(client, auth_headers, db_session):
    """Test creating customer with duplicate email"""
    # Create first customer
    customer = Customer(
        name='Existing Corp',
        email='duplicate@example.com',
        status='active'
    )
    db_session.add(customer)
    db_session.commit()
    
    # Try to create customer with same email
    payload = {
        'name': 'New Corp',
        'email': 'duplicate@example.com'
    }
    response = client.post('/api/v1/customers', json=payload, headers=auth_headers)
    assert response.status_code == 409
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'CONFLICT'


def test_get_customer_by_id(client, auth_headers, db_session):
    """Test getting single customer by ID"""
    customer = Customer(
        name='Test Customer',
        email='get@test.com',
        status='active'
    )
    db_session.add(customer)
    db_session.commit()
    
    response = client.get(f'/api/v1/customers/{customer.id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['id'] == str(customer.id)
    assert data['data']['name'] == 'Test Customer'


def test_get_customer_not_found(client, auth_headers):
    """Test getting non-existent customer"""
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(f'/api/v1/customers/{fake_id}', headers=auth_headers)
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'NOT_FOUND'


def test_update_customer(client, auth_headers, db_session):
    """Test updating a customer"""
    customer = Customer(
        name='Original Name',
        email='update@test.com',
        status='active'
    )
    db_session.add(customer)
    db_session.commit()
    
    payload = {
        'name': 'Updated Name',
        'phone': '555-9999'
    }
    response = client.patch(f'/api/v1/customers/{customer.id}', json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['name'] == 'Updated Name'
    assert data['data']['phone'] == '555-9999'


def test_deactivate_customer(client, auth_headers, db_session):
    """Test deactivating a customer"""
    customer = Customer(
        name='Active Customer',
        email='deactivate@test.com',
        status='active'
    )
    db_session.add(customer)
    db_session.commit()
    
    response = client.post(f'/api/v1/customers/{customer.id}/deactivate', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['status'] == 'inactive'


def test_search_customers(client, auth_headers, db_session):
    """Test searching customers"""
    customer1 = Customer(name='Acme Corp', email='acme@test.com', status='active')
    customer2 = Customer(name='Umbrella Inc', email='umbrella@test.com', status='active')
    db_session.add_all([customer1, customer2])
    db_session.commit()
    
    response = client.get('/api/v1/customers?search=Acme', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['data']) >= 1
    assert any(c['name'] == 'Acme Corp' for c in data['data'])


def test_filter_customers_by_status(client, auth_headers, db_session):
    """Test filtering customers by status"""
    customer1 = Customer(name='Active Corp', email='active@test.com', status='active')
    customer2 = Customer(name='Inactive Corp', email='inactive@test.com', status='inactive')
    db_session.add_all([customer1, customer2])
    db_session.commit()
    
    response = client.get('/api/v1/customers?status=active', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # All results should have active status
    assert all(c['status'] == 'active' for c in data['data'])

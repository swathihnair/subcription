"""Tests for authentication"""
import pytest
from app.models import User

def test_login_success(client, admin_user):
    """Test successful login"""
    response = client.post(
        '/api/v1/auth/login',
        json={'email': admin_user.email, 'password': 'testpass123'}
    )
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert 'access_token' in response.json['data']
    assert 'refresh_token' in response.json['data']
    assert response.json['data']['user']['email'] == admin_user.email

def test_login_invalid_email(client):
    """Test login with invalid email"""
    response = client.post(
        '/api/v1/auth/login',
        json={'email': 'notfound@test.com', 'password': 'anypassword'}
    )
    
    assert response.status_code == 401
    assert response.json['success'] is False
    assert response.json['error']['code'] == 'INVALID_CREDENTIALS'

def test_login_invalid_password(client, admin_user):
    """Test login with invalid password"""
    response = client.post(
        '/api/v1/auth/login',
        json={'email': admin_user.email, 'password': 'wrongpassword'}
    )
    
    assert response.status_code == 401
    assert response.json['success'] is False

def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post(
        '/api/v1/auth/login',
        json={'email': 'test@test.com'}
    )
    
    assert response.status_code == 400
    assert response.json['success'] is False
    assert response.json['error']['code'] == 'VALIDATION_ERROR'

def test_get_current_user(client, auth_headers):
    """Test get current user endpoint"""
    response = client.get(
        '/api/v1/auth/me',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['data']['email'] == 'admin@test.com'

def test_logout(client, auth_headers):
    """Test logout endpoint"""
    response = client.post(
        '/api/v1/auth/logout',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json['success'] is True

def test_protected_route_without_token(client):
    """Test accessing protected route without token"""
    response = client.get('/api/v1/auth/me')
    
    assert response.status_code == 401
    assert response.json['success'] is False

def test_password_hashing(admin_user):
    """Test password hashing"""
    assert admin_user.password_hash != 'testpass123'
    assert admin_user.check_password('testpass123')
    assert not admin_user.check_password('wrongpassword')

def test_password_validation(admin_user):
    """Test password validation"""
    with pytest.raises(ValueError):
        admin_user.set_password('short')
    
    with pytest.raises(ValueError):
        admin_user.set_password('')

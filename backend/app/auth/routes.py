"""Authentication routes"""
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.auth import auth_bp
from app.extensions import db
from app.models import User, Role
from datetime import datetime

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email and password are required',
                'details': {'fields': ['email', 'password']}
            }
        }), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password'
            }
        }), 401
    
    if not user.is_active:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ACCOUNT_DISABLED',
                'message': 'Your account has been disabled'
            }
        }), 403
    
    # Record login
    user.record_login()
    
    # Create tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'success': True,
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(include_email=True)
        },
        'message': 'Login successful'
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    # In a production app, you'd invalidate the token by adding it to a blacklist
    # For now, we just return success
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    
    return jsonify({
        'success': True,
        'data': {
            'access_token': access_token
        },
        'message': 'Token refreshed successfully'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found'
            }
        }), 404
    
    return jsonify({
        'success': True,
        'data': user.to_dict(include_email=True)
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint (admin-only or disabled)"""
    # This endpoint can be enabled/disabled based on application access model
    # For now, it's documented but protected
    
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email and password are required',
                'details': {'fields': ['email', 'password']}
            }
        }), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'error': {
                'code': 'EMAIL_EXISTS',
                'message': 'User with this email already exists'
            }
        }), 409
    
    # Get customer role (default for new registrations)
    customer_role = Role.query.filter_by(name='customer').first()
    if not customer_role:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'Unable to create user at this time'
            }
        }), 500
    
    try:
        user = User(
            email=data['email'],
            role_id=customer_role.id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(include_email=True),
            'message': 'User registered successfully'
        }), 201
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred during registration'
            }
        }), 500

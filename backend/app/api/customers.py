"""Customer API routes - Module 2"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Customer, User
from datetime import datetime
import uuid

@api_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """Get list of customers with filtering and pagination"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_customers') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access customers'
            }
        }), 403
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    status = request.args.get('status', None)
    search = request.args.get('search', None)
    sort_by = request.args.get('sortBy', 'created_at')
    sort_order = request.args.get('sortOrder', 'desc')
    
    # Build query
    query = Customer.query
    
    # Apply filters
    if status:
        query = query.filter(Customer.status == status)
    
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Customer.name.ilike(search_pattern),
                Customer.email.ilike(search_pattern)
            )
        )
    
    # Apply sorting
    if hasattr(Customer, sort_by):
        column = getattr(Customer, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    return jsonify({
        'success': True,
        'data': [customer.to_dict() for customer in pagination.items],
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': pagination.total,
            'totalPages': pagination.pages
        }
    }), 200

@api_bp.route('/customers/<customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    """Get single customer by ID"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_customers') and not user.has_permission('all'):
        # Customers can view their own data
        if not user.customer_id or str(user.customer_id) != customer_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access this customer'
                }
            }), 403
    
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid customer ID format'
            }
        }), 400
    
    customer = Customer.query.get(customer_uuid)
    
    if not customer:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Customer not found'
            }
        }), 404
    
    return jsonify({
        'success': True,
        'data': customer.to_dict()
    }), 200

@api_bp.route('/customers', methods=['POST'])
@jwt_required()
def create_customer():
    """Create a new customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_customers') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to create customers'
            }
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Name and email are required',
                'details': {'fields': ['name', 'email']}
            }
        }), 400
    
    # Check for duplicate email
    if Customer.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': 'A customer with this email already exists'
            }
        }), 409
    
    try:
        customer = Customer(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            billing_address=data.get('billing_address'),
            shipping_address=data.get('shipping_address'),
            status=data.get('status', 'active')
        )
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Customer created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while creating the customer'
            }
        }), 500

@api_bp.route('/customers/<customer_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_customer(customer_id):
    """Update a customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_customers') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to update customers'
            }
        }), 403
    
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid customer ID format'
            }
        }), 400
    
    customer = Customer.query.get(customer_uuid)
    
    if not customer:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Customer not found'
            }
        }), 404
    
    data = request.get_json()
    
    # Check for duplicate email (if email is being changed)
    if data.get('email') and data['email'] != customer.email:
        if Customer.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'CONFLICT',
                    'message': 'A customer with this email already exists'
                }
            }), 409
    
    try:
        # Update fields
        if 'name' in data:
            customer.name = data['name']
        if 'email' in data:
            customer.email = data['email']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'billing_address' in data:
            customer.billing_address = data['billing_address']
        if 'shipping_address' in data:
            customer.shipping_address = data['shipping_address']
        if 'status' in data:
            customer.status = data['status']
        
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Customer updated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while updating the customer'
            }
        }), 500

@api_bp.route('/customers/<customer_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_customer(customer_id):
    """Deactivate a customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_customers') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to deactivate customers'
            }
        }), 403
    
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid customer ID format'
            }
        }), 400
    
    customer = Customer.query.get(customer_uuid)
    
    if not customer:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Customer not found'
            }
        }), 404
    
    try:
        customer.status = 'inactive'
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Customer deactivated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while deactivating the customer'
            }
        }), 500

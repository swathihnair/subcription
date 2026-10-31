"""Product API routes - Module 2"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Product, User, Subscription
from datetime import datetime
from decimal import Decimal

@api_bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    """Get list of products with filtering and pagination"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access products'
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
    query = Product.query
    
    # Apply filters
    if status:
        query = query.filter(Product.status == status)
    
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_pattern),
                Product.sku.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )
    
    # Apply sorting
    if hasattr(Product, sort_by):
        column = getattr(Product, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    return jsonify({
        'success': True,
        'data': [product.to_dict() for product in pagination.items],
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': pagination.total,
            'totalPages': pagination.pages
        }
    }), 200

@api_bp.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """Get single product by ID with associated plans"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access products'
            }
        }), 403
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Product not found'
            }
        }), 404
    
    product_dict = product.to_dict()
    product_dict['plans'] = [plan.to_dict() for plan in product.plans]
    
    return jsonify({
        'success': True,
        'data': product_dict
    }), 200

@api_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    """Create a new product"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to create products'
            }
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'sku', 'base_price']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Missing required fields',
                'details': {'fields': missing_fields}
            }
        }), 400
    
    # Validate base_price
    try:
        base_price = Decimal(str(data['base_price']))
        if base_price < 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Base price must be non-negative'
                }
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid base price format'
            }
        }), 400
    
    # Check for duplicate SKU
    if Product.query.filter_by(sku=data['sku']).first():
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': 'A product with this SKU already exists'
            }
        }), 409
    
    try:
        product = Product(
            name=data['name'],
            sku=data['sku'],
            description=data.get('description'),
            base_price=base_price,
            status=data.get('status', 'active')
        )
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while creating the product'
            }
        }), 500

@api_bp.route('/products/<int:product_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_product(product_id):
    """Update a product"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to update products'
            }
        }), 403
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Product not found'
            }
        }), 404
    
    data = request.get_json()
    
    # Check for duplicate SKU (if SKU is being changed)
    if data.get('sku') and data['sku'] != product.sku:
        if Product.query.filter_by(sku=data['sku']).first():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'CONFLICT',
                    'message': 'A product with this SKU already exists'
                }
            }), 409
    
    # Validate base_price if provided
    if 'base_price' in data:
        try:
            base_price = Decimal(str(data['base_price']))
            if base_price < 0:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Base price must be non-negative'
                    }
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid base price format'
                }
            }), 400
    
    try:
        # Update fields
        if 'name' in data:
            product.name = data['name']
        if 'sku' in data:
            product.sku = data['sku']
        if 'description' in data:
            product.description = data['description']
        if 'base_price' in data:
            product.base_price = base_price
        if 'status' in data:
            product.status = data['status']
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product updated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while updating the product'
            }
        }), 500

@api_bp.route('/products/<int:product_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_product(product_id):
    """Deactivate a product - cannot delete if referenced by subscriptions"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to deactivate products'
            }
        }), 403
    
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Product not found'
            }
        }), 404
    
    try:
        product.status = 'discontinued'
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product deactivated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while deactivating the product'
            }
        }), 500

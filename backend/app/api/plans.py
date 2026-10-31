"""Plan API routes - Module 2"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Plan, Product, User, Subscription
from datetime import datetime
from decimal import Decimal
import uuid

VALID_BILLING_CYCLES = ['weekly', 'monthly', 'quarterly', 'annually']

@api_bp.route('/plans', methods=['GET'])
@jwt_required()
def get_plans():
    """Get list of plans with filtering and pagination"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access plans'
            }
        }), 403
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    status = request.args.get('status', None)
    product_id = request.args.get('product_id', None)
    sort_by = request.args.get('sortBy', 'created_at')
    sort_order = request.args.get('sortOrder', 'desc')
    
    # Build query
    query = Plan.query
    
    # Apply filters
    if status:
        query = query.filter(Plan.status == status)
    
    if product_id:
        try:
            product_uuid = uuid.UUID(product_id)
            query = query.filter(Plan.product_id == product_uuid)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid product ID format'
                }
            }), 400
    
    # Apply sorting
    if hasattr(Plan, sort_by):
        column = getattr(Plan, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    # Add product info to each plan
    results = []
    for plan in pagination.items:
        plan_dict = plan.to_dict()
        if plan.product:
            plan_dict['product'] = plan.product.to_dict()
        results.append(plan_dict)
    
    return jsonify({
        'success': True,
        'data': results,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': pagination.total,
            'totalPages': pagination.pages
        }
    }), 200

@api_bp.route('/plans/<plan_id>', methods=['GET'])
@jwt_required()
def get_plan(plan_id):
    """Get single plan by ID"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access plans'
            }
        }), 403
    
    try:
        plan_uuid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid plan ID format'
            }
        }), 400
    
    plan = Plan.query.get(plan_uuid)
    
    if not plan:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Plan not found'
            }
        }), 404
    
    plan_dict = plan.to_dict()
    if plan.product:
        plan_dict['product'] = plan.product.to_dict()
    
    return jsonify({
        'success': True,
        'data': plan_dict
    }), 200

@api_bp.route('/plans', methods=['POST'])
@jwt_required()
def create_plan():
    """Create a new plan"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to create plans'
            }
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['product_id', 'name', 'price', 'billing_cycle']
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
    
    # Validate product exists
    try:
        product_uuid = uuid.UUID(data['product_id'])
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid product ID format'
            }
        }), 400
    
    product = Product.query.get(product_uuid)
    if not product:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Product not found'
            }
        }), 404
    
    # Validate billing cycle
    if data['billing_cycle'] not in VALID_BILLING_CYCLES:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Invalid billing cycle. Must be one of: {", ".join(VALID_BILLING_CYCLES)}'
            }
        }), 400
    
    # Validate price
    try:
        price = Decimal(str(data['price']))
        if price < 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Price must be non-negative'
                }
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid price format'
            }
        }), 400
    
    # Validate setup_fee if provided
    setup_fee = Decimal('0')
    if data.get('setup_fee'):
        try:
            setup_fee = Decimal(str(data['setup_fee']))
            if setup_fee < 0:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Setup fee must be non-negative'
                    }
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid setup fee format'
                }
            }), 400
    
    try:
        plan = Plan(
            product_id=product_uuid,
            name=data['name'],
            description=data.get('description'),
            price=price,
            billing_cycle=data['billing_cycle'],
            setup_fee=setup_fee,
            status=data.get('status', 'active')
        )
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': plan.to_dict(),
            'message': 'Plan created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while creating the plan'
            }
        }), 500

@api_bp.route('/plans/<plan_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_plan(plan_id):
    """Update a plan"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to update plans'
            }
        }), 403
    
    try:
        plan_uuid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid plan ID format'
            }
        }), 400
    
    plan = Plan.query.get(plan_uuid)
    
    if not plan:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Plan not found'
            }
        }), 404
    
    data = request.get_json()
    
    # Validate billing cycle if provided
    if 'billing_cycle' in data and data['billing_cycle'] not in VALID_BILLING_CYCLES:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Invalid billing cycle. Must be one of: {", ".join(VALID_BILLING_CYCLES)}'
            }
        }), 400
    
    # Validate price if provided
    if 'price' in data:
        try:
            price = Decimal(str(data['price']))
            if price < 0:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Price must be non-negative'
                    }
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid price format'
                }
            }), 400
    
    # Validate setup_fee if provided
    if 'setup_fee' in data:
        try:
            setup_fee = Decimal(str(data['setup_fee']))
            if setup_fee < 0:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'Setup fee must be non-negative'
                    }
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid setup fee format'
                }
            }), 400
    
    try:
        # Update fields
        if 'name' in data:
            plan.name = data['name']
        if 'description' in data:
            plan.description = data['description']
        if 'price' in data:
            plan.price = price
        if 'billing_cycle' in data:
            plan.billing_cycle = data['billing_cycle']
        if 'setup_fee' in data:
            plan.setup_fee = setup_fee
        if 'status' in data:
            plan.status = data['status']
        
        plan.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': plan.to_dict(),
            'message': 'Plan updated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while updating the plan'
            }
        }), 500

@api_bp.route('/plans/<plan_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_plan(plan_id):
    """Deactivate a plan - cannot delete if referenced by subscriptions"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_products') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to deactivate plans'
            }
        }), 403
    
    try:
        plan_uuid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid plan ID format'
            }
        }), 400
    
    plan = Plan.query.get(plan_uuid)
    
    if not plan:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Plan not found'
            }
        }), 404
    
    # Check if plan is in use
    active_subscriptions = Subscription.query.filter_by(plan_id=plan_uuid).filter(
        Subscription.status.in_(['active', 'trialing'])
    ).count()
    
    if active_subscriptions > 0:
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': f'Cannot deactivate plan: {active_subscriptions} active subscription(s) exist'
            }
        }), 409
    
    try:
        plan.status = 'inactive'
        plan.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': plan.to_dict(),
            'message': 'Plan deactivated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while deactivating the plan'
            }
        }), 500

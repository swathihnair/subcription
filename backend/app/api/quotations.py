"""Quotation API routes - Module 2"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Quotation, Customer, Plan, User, Subscription
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

def generate_quote_number():
    """Generate unique quotation number"""
    from datetime import datetime
    import random
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    random_part = random.randint(1000, 9999)
    return f'QT-{timestamp}-{random_part}'

@api_bp.route('/quotations', methods=['GET'])
@jwt_required()
def get_quotations():
    """Get list of quotations with filtering and pagination"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_quotations') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access quotations'
            }
        }), 403
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    status = request.args.get('status', None)
    customer_id = request.args.get('customer_id', None)
    sort_by = request.args.get('sortBy', 'created_at')
    sort_order = request.args.get('sortOrder', 'desc')
    
    # Build query
    query = Quotation.query
    
    # Apply filters
    if status:
        query = query.filter(Quotation.status == status)
    
    if customer_id:
        try:
            customer_uuid = uuid.UUID(customer_id)
            query = query.filter(Quotation.customer_id == customer_uuid)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid customer ID format'
                }
            }), 400
    
    # Apply sorting
    if hasattr(Quotation, sort_by):
        column = getattr(Quotation, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    # Add related data
    results = []
    for quotation in pagination.items:
        quot_dict = quotation.to_dict()
        if quotation.customer:
            quot_dict['customer'] = quotation.customer.to_dict()
        if quotation.plan:
            quot_dict['plan'] = quotation.plan.to_dict()
        results.append(quot_dict)
    
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

@api_bp.route('/quotations/<quotation_id>', methods=['GET'])
@jwt_required()
def get_quotation(quotation_id):
    """Get single quotation by ID"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_quotations') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access quotations'
            }
        }), 403
    
    try:
        quotation_uuid = uuid.UUID(quotation_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid quotation ID format'
            }
        }), 400
    
    quotation = Quotation.query.get(quotation_uuid)
    
    if not quotation:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Quotation not found'
            }
        }), 404
    
    quot_dict = quotation.to_dict()
    if quotation.customer:
        quot_dict['customer'] = quotation.customer.to_dict()
    if quotation.plan:
        quot_dict['plan'] = quotation.plan.to_dict()
    
    return jsonify({
        'success': True,
        'data': quot_dict
    }), 200

@api_bp.route('/quotations', methods=['POST'])
@jwt_required()
def create_quotation():
    """Create a new quotation"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_quotations') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to create quotations'
            }
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['customer_id', 'plan_id', 'amount', 'total_amount']
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
    
    # Validate customer exists
    try:
        customer_uuid = uuid.UUID(data['customer_id'])
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
    
    # Validate plan exists
    try:
        plan_uuid = uuid.UUID(data['plan_id'])
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
    
    # Validate monetary values
    try:
        amount = Decimal(str(data['amount']))
        discount_amount = Decimal(str(data.get('discount_amount', 0)))
        total_amount = Decimal(str(data['total_amount']))
        
        if amount < 0 or discount_amount < 0 or total_amount < 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Monetary values must be non-negative'
                }
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid monetary value format'
            }
        }), 400
    
    # Calculate valid_until if not provided (default: 30 days)
    valid_until = None
    if data.get('valid_until'):
        try:
            valid_until = datetime.fromisoformat(data['valid_until'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid date format for valid_until'
                }
            }), 400
    else:
        valid_until = datetime.utcnow() + timedelta(days=30)
    
    try:
        # Generate unique quote number
        quote_number = generate_quote_number()
        while Quotation.query.filter_by(quote_number=quote_number).first():
            quote_number = generate_quote_number()
        
        quotation = Quotation(
            customer_id=customer_uuid,
            plan_id=plan_uuid,
            quote_number=quote_number,
            amount=amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            valid_until=valid_until,
            status='draft'
        )
        db.session.add(quotation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quotation.to_dict(),
            'message': 'Quotation created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while creating the quotation'
            }
        }), 500

@api_bp.route('/quotations/<quotation_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_quotation(quotation_id):
    """Update a quotation (only in draft or sent status)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_quotations') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to update quotations'
            }
        }), 403
    
    try:
        quotation_uuid = uuid.UUID(quotation_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid quotation ID format'
            }
        }), 400
    
    quotation = Quotation.query.get(quotation_uuid)
    
    if not quotation:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Quotation not found'
            }
        }), 404
    
    # Only allow editing draft or sent quotations
    if quotation.status not in ['draft', 'sent']:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': 'Cannot edit quotation in current status'
            }
        }), 400
    
    data = request.get_json()
    
    # Validate monetary values if provided
    if 'amount' in data or 'discount_amount' in data or 'total_amount' in data:
        try:
            if 'amount' in data:
                amount = Decimal(str(data['amount']))
                if amount < 0:
                    raise ValueError('Amount must be non-negative')
            if 'discount_amount' in data:
                discount_amount = Decimal(str(data['discount_amount']))
                if discount_amount < 0:
                    raise ValueError('Discount amount must be non-negative')
            if 'total_amount' in data:
                total_amount = Decimal(str(data['total_amount']))
                if total_amount < 0:
                    raise ValueError('Total amount must be non-negative')
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e)
                }
            }), 400
    
    try:
        # Update fields
        if 'amount' in data:
            quotation.amount = amount
        if 'discount_amount' in data:
            quotation.discount_amount = discount_amount
        if 'total_amount' in data:
            quotation.total_amount = total_amount
        if 'valid_until' in data:
            quotation.valid_until = datetime.fromisoformat(data['valid_until'].replace('Z', '+00:00'))
        
        quotation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quotation.to_dict(),
            'message': 'Quotation updated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while updating the quotation'
            }
        }), 500

@api_bp.route('/quotations/<quotation_id>/accept', methods=['POST'])
@jwt_required()
def accept_quotation(quotation_id):
    """Accept a quotation"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_quotations') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to accept quotations'
            }
        }), 403
    
    try:
        quotation_uuid = uuid.UUID(quotation_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid quotation ID format'
            }
        }), 400
    
    quotation = Quotation.query.get(quotation_uuid)
    
    if not quotation:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Quotation not found'
            }
        }), 404
    
    # Validate status
    if quotation.status == 'accepted':
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': 'Quotation is already accepted'
            }
        }), 400
    
    if quotation.status in ['rejected', 'expired']:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': f'Cannot accept {quotation.status} quotation'
            }
        }), 400
    
    # Check if expired
    if quotation.valid_until and quotation.valid_until < datetime.utcnow():
        quotation.status = 'expired'
        db.session.commit()
        return jsonify({
            'success': False,
            'error': {
                'code': 'EXPIRED',
                'message': 'Quotation has expired'
            }
        }), 400
    
    try:
        quotation.status = 'accepted'
        quotation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quotation.to_dict(),
            'message': 'Quotation accepted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while accepting the quotation'
            }
        }), 500

@api_bp.route('/quotations/<quotation_id>/reject', methods=['POST'])
@jwt_required()
def reject_quotation(quotation_id):
    """Reject a quotation"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_quotations') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to reject quotations'
            }
        }), 403
    
    try:
        quotation_uuid = uuid.UUID(quotation_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid quotation ID format'
            }
        }), 400
    
    quotation = Quotation.query.get(quotation_uuid)
    
    if not quotation:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Quotation not found'
            }
        }), 404
    
    # Validate status
    if quotation.status in ['accepted', 'rejected', 'expired']:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': f'Cannot reject {quotation.status} quotation'
            }
        }), 400
    
    try:
        quotation.status = 'rejected'
        quotation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': quotation.to_dict(),
            'message': 'Quotation rejected successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while rejecting the quotation'
            }
        }), 500

@api_bp.route('/quotations/<quotation_id>/convert-to-subscription', methods=['POST'])
@jwt_required()
def convert_quotation_to_subscription(quotation_id):
    """Convert accepted quotation to subscription"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_quotations') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to convert quotations'
            }
        }), 403
    
    try:
        quotation_uuid = uuid.UUID(quotation_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid quotation ID format'
            }
        }), 400
    
    quotation = Quotation.query.get(quotation_uuid)
    
    if not quotation:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Quotation not found'
            }
        }), 404
    
    # Validate status
    if quotation.status != 'accepted':
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': 'Only accepted quotations can be converted to subscriptions'
            }
        }), 400
    
    # Check if expired
    if quotation.valid_until and quotation.valid_until < datetime.utcnow():
        return jsonify({
            'success': False,
            'error': {
                'code': 'EXPIRED',
                'message': 'Quotation has expired and cannot be converted'
            }
        }), 400
    
    # Check if already converted (prevent duplicate subscriptions)
    existing_subscription = Subscription.query.filter(
        Subscription.customer_id == quotation.customer_id,
        Subscription.plan_id == quotation.plan_id,
        Subscription.status.in_(['active', 'trialing'])
    ).first()
    
    if existing_subscription:
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': 'Customer already has an active subscription for this plan'
            }
        }), 409
    
    try:
        from app.api.subscriptions import generate_subscription_number, calculate_billing_dates
        
        # Generate subscription number
        subscription_number = generate_subscription_number()
        
        # Calculate billing dates based on plan
        plan = quotation.plan
        start_date = datetime.utcnow()
        billing_dates = calculate_billing_dates(start_date, plan.billing_cycle)
        
        # Create subscription
        subscription = Subscription(
            customer_id=quotation.customer_id,
            plan_id=quotation.plan_id,
            subscription_number=subscription_number,
            status='active',
            start_date=start_date,
            next_billing_date=billing_dates['next_billing_date'],
            monthly_recurring_revenue=Decimal(str(plan.price)),  # Simplified calculation
            annual_contract_value=Decimal(str(plan.price)) * 12,  # Simplified calculation
            auto_renew=True
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': 'Quotation converted to subscription successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while converting the quotation'
            }
        }), 500

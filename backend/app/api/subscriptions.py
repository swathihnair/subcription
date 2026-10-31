"""Subscription API routes - Module 2"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Subscription, Customer, Plan, User
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import random

def generate_subscription_number():
    """Generate unique subscription number"""
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    random_part = random.randint(1000, 9999)
    return f'SUB-{timestamp}-{random_part}'

def calculate_billing_dates(start_date, billing_cycle):
    """Calculate next billing date based on billing cycle"""
    if billing_cycle == 'weekly':
        next_billing_date = start_date + timedelta(weeks=1)
    elif billing_cycle == 'monthly':
        next_billing_date = start_date + timedelta(days=30)
    elif billing_cycle == 'quarterly':
        next_billing_date = start_date + timedelta(days=90)
    elif billing_cycle == 'annually':
        next_billing_date = start_date + timedelta(days=365)
    else:
        next_billing_date = start_date + timedelta(days=30)  # default to monthly
    
    return {
        'current_period_start': start_date,
        'current_period_end': next_billing_date,
        'next_billing_date': next_billing_date
    }

VALID_SUBSCRIPTION_STATUSES = ['draft', 'trialing', 'active', 'paused', 'past_due', 'cancelled', 'expired']

@api_bp.route('/subscriptions', methods=['GET'])
@jwt_required()
def get_subscriptions():
    """Get list of subscriptions with filtering and pagination"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_subscriptions') and not user.has_permission('all'):
        # Customers can view their own subscriptions
        if not user.customer_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access subscriptions'
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
    query = Subscription.query
    
    # Customers can only see their own subscriptions
    if user.customer_id and not user.has_permission('manage_subscriptions'):
        query = query.filter(Subscription.customer_id == user.customer_id)
    
    # Apply filters
    if status:
        query = query.filter(Subscription.status == status)
    
    if customer_id:
        try:
            customer_uuid = uuid.UUID(customer_id)
            query = query.filter(Subscription.customer_id == customer_uuid)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid customer ID format'
                }
            }), 400
    
    # Apply sorting
    if hasattr(Subscription, sort_by):
        column = getattr(Subscription, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    # Add related data
    results = []
    for subscription in pagination.items:
        sub_dict = subscription.to_dict()
        if subscription.customer:
            sub_dict['customer'] = subscription.customer.to_dict()
        if subscription.plan:
            sub_dict['plan'] = subscription.plan.to_dict()
        results.append(sub_dict)
    
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

@api_bp.route('/subscriptions/<subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription(subscription_id):
    """Get single subscription by ID"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    try:
        subscription_uuid = uuid.UUID(subscription_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid subscription ID format'
            }
        }), 400
    
    subscription = Subscription.query.get(subscription_uuid)
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found'
            }
        }), 404
    
    # Check permission
    if not user.has_permission('manage_subscriptions') and not user.has_permission('all'):
        # Customers can only see their own subscriptions
        if not user.customer_id or subscription.customer_id != user.customer_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access this subscription'
                }
            }), 403
    
    sub_dict = subscription.to_dict()
    if subscription.customer:
        sub_dict['customer'] = subscription.customer.to_dict()
    if subscription.plan:
        sub_dict['plan'] = subscription.plan.to_dict()
    
    # Include invoices if user has permission
    if user.has_permission('view_invoices') or user.has_permission('all'):
        sub_dict['invoices'] = [invoice.to_dict() for invoice in subscription.invoices]
    
    return jsonify({
        'success': True,
        'data': sub_dict
    }), 200

@api_bp.route('/subscriptions', methods=['POST'])
@jwt_required()
def create_subscription():
    """Create a new subscription"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_subscriptions') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to create subscriptions'
            }
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['customer_id', 'plan_id']
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
    
    if plan.status != 'active':
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': 'Cannot create subscription for inactive plan'
            }
        }), 400
    
    # Check for duplicate active subscriptions
    existing = Subscription.query.filter_by(
        customer_id=customer_uuid,
        plan_id=plan_uuid
    ).filter(
        Subscription.status.in_(['active', 'trialing'])
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': 'Customer already has an active subscription for this plan'
            }
        }), 409
    
    try:
        # Generate subscription number
        subscription_number = generate_subscription_number()
        while Subscription.query.filter_by(subscription_number=subscription_number).first():
            subscription_number = generate_subscription_number()
        
        # Calculate dates
        start_date = datetime.utcnow()
        if data.get('start_date'):
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        
        billing_dates = calculate_billing_dates(start_date, plan.billing_cycle)
        
        # Calculate financial metrics
        mrr = Decimal(str(plan.price))
        if plan.billing_cycle == 'annually':
            mrr = Decimal(str(plan.price)) / 12
        elif plan.billing_cycle == 'quarterly':
            mrr = Decimal(str(plan.price)) / 3
        elif plan.billing_cycle == 'weekly':
            mrr = Decimal(str(plan.price)) * Decimal('4.33')  # Average weeks per month
        
        acv = mrr * 12
        
        subscription = Subscription(
            customer_id=customer_uuid,
            plan_id=plan_uuid,
            subscription_number=subscription_number,
            status=data.get('status', 'active'),
            start_date=start_date,
            next_billing_date=billing_dates['next_billing_date'],
            monthly_recurring_revenue=mrr,
            annual_contract_value=acv,
            auto_renew=data.get('auto_renew', True)
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': 'Subscription created successfully'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while creating the subscription'
            }
        }), 500

@api_bp.route('/subscriptions/<subscription_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_subscription(subscription_id):
    """Update a subscription"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_subscriptions') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to update subscriptions'
            }
        }), 403
    
    try:
        subscription_uuid = uuid.UUID(subscription_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid subscription ID format'
            }
        }), 400
    
    subscription = Subscription.query.get(subscription_uuid)
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found'
            }
        }), 404
    
    data = request.get_json()
    
    try:
        # Update fields
        if 'auto_renew' in data:
            subscription.auto_renew = data['auto_renew']
        if 'end_date' in data:
            if data['end_date']:
                subscription.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            else:
                subscription.end_date = None
        
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': 'Subscription updated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while updating the subscription'
            }
        }), 500

@api_bp.route('/subscriptions/<subscription_id>/pause', methods=['POST'])
@jwt_required()
def pause_subscription(subscription_id):
    """Pause an active subscription"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_subscriptions') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to pause subscriptions'
            }
        }), 403
    
    try:
        subscription_uuid = uuid.UUID(subscription_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid subscription ID format'
            }
        }), 400
    
    subscription = Subscription.query.get(subscription_uuid)
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found'
            }
        }), 404
    
    # Validate status
    if subscription.status != 'active':
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': 'Only active subscriptions can be paused'
            }
        }), 400
    
    try:
        subscription.status = 'paused'
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': 'Subscription paused successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while pausing the subscription'
            }
        }), 500

@api_bp.route('/subscriptions/<subscription_id>/resume', methods=['POST'])
@jwt_required()
def resume_subscription(subscription_id):
    """Resume a paused subscription"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_subscriptions') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to resume subscriptions'
            }
        }), 403
    
    try:
        subscription_uuid = uuid.UUID(subscription_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid subscription ID format'
            }
        }), 400
    
    subscription = Subscription.query.get(subscription_uuid)
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found'
            }
        }), 404
    
    # Validate status
    if subscription.status != 'paused':
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': 'Only paused subscriptions can be resumed'
            }
        }), 400
    
    try:
        subscription.status = 'active'
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': 'Subscription resumed successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while resuming the subscription'
            }
        }), 500

@api_bp.route('/subscriptions/<subscription_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription(subscription_id):
    """Cancel a subscription"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id).first()
    
    # Check permission
    if not user.has_permission('manage_subscriptions') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to cancel subscriptions'
            }
        }), 403
    
    try:
        subscription_uuid = uuid.UUID(subscription_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid subscription ID format'
            }
        }), 400
    
    subscription = Subscription.query.get(subscription_uuid)
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found'
            }
        }), 404
    
    # Validate status
    if subscription.status in ['cancelled', 'expired']:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_STATE',
                'message': f'Subscription is already {subscription.status}'
            }
        }), 400
    
    data = request.get_json() or {}
    cancel_immediately = data.get('cancel_immediately', False)
    
    try:
        if cancel_immediately:
            subscription.status = 'cancelled'
            subscription.end_date = datetime.utcnow()
        else:
            # Cancel at period end
            subscription.status = 'cancelled'
            subscription.end_date = subscription.next_billing_date or datetime.utcnow()
        
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        message = 'Subscription cancelled immediately' if cancel_immediately else 'Subscription scheduled for cancellation at period end'
        
        return jsonify({
            'success': True,
            'data': subscription.to_dict(),
            'message': message
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while cancelling the subscription'
            }
        }), 500

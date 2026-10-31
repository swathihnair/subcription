"""Renewals management API routes - Module 4"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import User, Subscription, Customer, Plan
from datetime import datetime, timedelta

def check_internal_permission(user):
    """Check if user has permission to access renewals"""
    if not user or not user.role:
        return False
    return user.role.name in ['admin', 'sales', 'finance']

@api_bp.route('/renewals', methods=['GET'])
@jwt_required()
def get_renewals():
    """Get subscriptions grouped by renewal status"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_internal_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only internal users can access renewals'
            }
        }), 403
    
    # Get filter parameters
    customer_id = request.args.get('customer_id', type=int)
    status = request.args.get('status')
    plan_id = request.args.get('plan_id', type=int)
    days_window = request.args.get('days', type=int, default=30)
    
    # Base query
    query = Subscription.query
    
    # Apply filters
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if status:
        query = query.filter_by(status=status)
    if plan_id:
        query = query.filter_by(plan_id=plan_id)
    
    subscriptions = query.all()
    
    # Group subscriptions by renewal status
    now = datetime.utcnow()
    renewals = {
        'due_soon': [],
        'due_later': [],
        'past_due': [],
        'scheduled_cancellation': [],
        'recently_renewed': []
    }
    
    for sub in subscriptions:
        sub_dict = sub.to_dict()
        
        # Add customer and plan details
        if sub.customer:
            sub_dict['customer'] = sub.customer.to_dict()
        if sub.plan:
            sub_dict['plan'] = sub.plan.to_dict()
        
        # Categorize by status and dates
        if sub.status == 'cancelled':
            if sub.end_date and sub.end_date > now:
                renewals['scheduled_cancellation'].append(sub_dict)
        elif sub.next_billing_date:
            days_until = (sub.next_billing_date - now).days
            
            if days_until < 0:
                renewals['past_due'].append(sub_dict)
            elif days_until <= 7:
                renewals['due_soon'].append(sub_dict)
            elif days_until <= days_window:
                renewals['due_later'].append(sub_dict)
        
        # Check if recently renewed (within last 7 days)
        if sub.updated_at:
            days_since_update = (now - sub.updated_at).days
            if days_since_update <= 7 and sub.status == 'active':
                renewals['recently_renewed'].append(sub_dict)
    
    return jsonify({
        'success': True,
        'data': renewals
    }), 200

@api_bp.route('/renewals/summary', methods=['GET'])
@jwt_required()
def get_renewals_summary():
    """Get summary counts of renewal statuses"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_internal_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only internal users can access renewals'
            }
        }), 403
    
    now = datetime.utcnow()
    seven_days = now + timedelta(days=7)
    thirty_days = now + timedelta(days=30)
    
    # Count subscriptions by renewal status
    active_subs = Subscription.query.filter_by(status='active').all()
    
    summary = {
        'due_within_7_days': 0,
        'due_within_30_days': 0,
        'past_due': 0,
        'scheduled_cancellation': 0,
        'total_active': len(active_subs)
    }
    
    for sub in active_subs:
        if sub.next_billing_date:
            if sub.next_billing_date < now:
                summary['past_due'] += 1
            elif sub.next_billing_date <= seven_days:
                summary['due_within_7_days'] += 1
            elif sub.next_billing_date <= thirty_days:
                summary['due_within_30_days'] += 1
    
    # Count scheduled cancellations
    summary['scheduled_cancellation'] = Subscription.query.filter(
        Subscription.status == 'cancelled',
        Subscription.end_date > now
    ).count()
    
    return jsonify({
        'success': True,
        'data': summary
    }), 200

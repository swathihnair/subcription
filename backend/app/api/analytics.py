"""Analytics and reporting API routes - Module 4"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import User, Customer, Subscription, Invoice, Payment, Plan
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal

def check_analytics_permission(user):
    """Check if user has permission to access analytics"""
    if not user or not user.role:
        return False
    return user.role.name in ['admin', 'finance']

@api_bp.route('/analytics/overview', methods=['GET'])
@jwt_required()
def get_analytics_overview():
    """Get dashboard overview metrics"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_analytics_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only admin and finance users can access analytics'
            }
        }), 403
    
    # Total customers
    total_customers = Customer.query.filter_by(status='active').count()
    
    # Active subscriptions
    active_subscriptions = Subscription.query.filter_by(status='active').count()
    
    # Calculate MRR from active subscriptions
    active_subs = Subscription.query.filter_by(status='active').all()
    total_mrr = Decimal('0')
    for sub in active_subs:
        if sub.monthly_recurring_revenue:
            total_mrr += sub.monthly_recurring_revenue
    
    # Calculate ARR (MRR * 12)
    total_arr = total_mrr * 12
    
    # Outstanding invoices
    outstanding_invoices = Invoice.query.filter(
        Invoice.status.in_(['sent', 'overdue']),
        Invoice.amount_due > 0
    ).count()
    
    # Overdue invoices
    overdue_invoices = Invoice.query.filter_by(status='overdue').count()
    
    # Total outstanding amount
    outstanding_result = db.session.query(
        func.sum(Invoice.amount_due)
    ).filter(
        Invoice.status.in_(['sent', 'overdue'])
    ).scalar()
    total_outstanding = float(outstanding_result) if outstanding_result else 0
    
    return jsonify({
        'success': True,
        'data': {
            'total_customers': total_customers,
            'active_subscriptions': active_subscriptions,
            'monthly_recurring_revenue': float(total_mrr),
            'annual_recurring_revenue': float(total_arr),
            'outstanding_invoices': outstanding_invoices,
            'overdue_invoices': overdue_invoices,
            'total_outstanding': total_outstanding
        }
    }), 200

@api_bp.route('/analytics/mrr', methods=['GET'])
@jwt_required()
def get_mrr_analytics():
    """Get MRR analytics over time"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_analytics_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only admin and finance users can access analytics'
            }
        }), 403
    
    # Get date range from query params
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get current MRR
    active_subs = Subscription.query.filter_by(status='active').all()
    current_mrr = sum(
        float(sub.monthly_recurring_revenue) if sub.monthly_recurring_revenue else 0
        for sub in active_subs
    )
    
    # Get MRR by plan
    mrr_by_plan = {}
    for sub in active_subs:
        if sub.plan:
            plan_name = sub.plan.name
            mrr = float(sub.monthly_recurring_revenue) if sub.monthly_recurring_revenue else 0
            mrr_by_plan[plan_name] = mrr_by_plan.get(plan_name, 0) + mrr
    
    return jsonify({
        'success': True,
        'data': {
            'current_mrr': current_mrr,
            'arr': current_mrr * 12,
            'by_plan': mrr_by_plan,
            'calculation_note': 'MRR calculated from active subscription monthly_recurring_revenue field'
        }
    }), 200

@api_bp.route('/analytics/subscriptions', methods=['GET'])
@jwt_required()
def get_subscription_analytics():
    """Get subscription analytics"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_analytics_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only admin and finance users can access analytics'
            }
        }), 403
    
    # Get date range
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Subscription counts by status
    status_counts = db.session.query(
        Subscription.status,
        func.count(Subscription.id)
    ).group_by(Subscription.status).all()
    
    by_status = {status: count for status, count in status_counts}
    
    # New subscriptions in date range
    new_subscriptions = Subscription.query.filter(
        Subscription.created_at >= start_date,
        Subscription.created_at <= end_date
    ).count()
    
    # Cancelled subscriptions in date range
    cancelled_subscriptions = Subscription.query.filter(
        Subscription.status == 'cancelled',
        Subscription.updated_at >= start_date,
        Subscription.updated_at <= end_date
    ).count()
    
    # Subscriptions by plan
    plan_counts = db.session.query(
        Plan.name,
        func.count(Subscription.id)
    ).join(Subscription).filter(
        Subscription.status == 'active'
    ).group_by(Plan.name).all()
    
    by_plan = {plan: count for plan, count in plan_counts}
    
    return jsonify({
        'success': True,
        'data': {
            'by_status': by_status,
            'new_subscriptions': new_subscriptions,
            'cancelled_subscriptions': cancelled_subscriptions,
            'by_plan': by_plan,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            }
        }
    }), 200

@api_bp.route('/analytics/invoices', methods=['GET'])
@jwt_required()
def get_invoice_analytics():
    """Get invoice analytics"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_analytics_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only admin and finance users can access analytics'
            }
        }), 403
    
    # Invoice counts by status
    status_counts = db.session.query(
        Invoice.status,
        func.count(Invoice.id),
        func.sum(Invoice.total_amount)
    ).group_by(Invoice.status).all()
    
    by_status = {}
    for status, count, total in status_counts:
        by_status[status] = {
            'count': count,
            'total_amount': float(total) if total else 0
        }
    
    # Outstanding amounts
    outstanding = db.session.query(
        func.sum(Invoice.amount_due)
    ).filter(
        Invoice.status.in_(['sent', 'overdue'])
    ).scalar()
    
    # Overdue amounts
    overdue = db.session.query(
        func.sum(Invoice.amount_due)
    ).filter_by(status='overdue').scalar()
    
    return jsonify({
        'success': True,
        'data': {
            'by_status': by_status,
            'outstanding_amount': float(outstanding) if outstanding else 0,
            'overdue_amount': float(overdue) if overdue else 0
        }
    }), 200

@api_bp.route('/analytics/payments', methods=['GET'])
@jwt_required()
def get_payment_analytics():
    """Get payment analytics"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_analytics_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only admin and finance users can access analytics'
            }
        }), 403
    
    # Get date range
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Payment counts and totals by status
    status_stats = db.session.query(
        Payment.status,
        func.count(Payment.id),
        func.sum(Payment.amount)
    ).group_by(Payment.status).all()
    
    by_status = {}
    for status, count, total in status_stats:
        by_status[status] = {
            'count': count,
            'total_amount': float(total) if total else 0
        }
    
    # Payments in date range
    payments_in_range = db.session.query(
        func.count(Payment.id),
        func.sum(Payment.amount)
    ).filter(
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
        Payment.status == 'completed'
    ).first()
    
    # Payments by method
    method_stats = db.session.query(
        Payment.payment_method,
        func.count(Payment.id),
        func.sum(Payment.amount)
    ).filter_by(status='completed').group_by(Payment.payment_method).all()
    
    by_method = {}
    for method, count, total in method_stats:
        method_name = method if method else 'unspecified'
        by_method[method_name] = {
            'count': count,
            'total_amount': float(total) if total else 0
        }
    
    return jsonify({
        'success': True,
        'data': {
            'by_status': by_status,
            'by_method': by_method,
            'in_date_range': {
                'count': payments_in_range[0] if payments_in_range else 0,
                'total_amount': float(payments_in_range[1]) if payments_in_range and payments_in_range[1] else 0,
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    }), 200

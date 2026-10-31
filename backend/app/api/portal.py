"""Customer portal API routes - Module 4"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import User, Customer, Subscription, Invoice, Payment

@api_bp.route('/portal/me', methods=['GET'])
@jwt_required()
def get_portal_profile():
    """Get current customer profile for portal"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user or not user.customer_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only customer users can access portal'
            }
        }), 403
    
    customer = Customer.query.get(user.customer_id)
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
        'data': {
            'user': user.to_dict(include_email=True),
            'customer': customer.to_dict()
        }
    }), 200

@api_bp.route('/portal/subscriptions', methods=['GET'])
@jwt_required()
def get_portal_subscriptions():
    """Get subscriptions for logged-in customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user or not user.customer_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only customer users can access portal'
            }
        }), 403
    
    subscriptions = Subscription.query.filter_by(customer_id=user.customer_id).all()
    
    return jsonify({
        'success': True,
        'data': [sub.to_dict() for sub in subscriptions]
    }), 200

@api_bp.route('/portal/subscriptions/<int:subscription_id>', methods=['GET'])
@jwt_required()
def get_portal_subscription(subscription_id):
    """Get specific subscription for logged-in customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user or not user.customer_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only customer users can access portal'
            }
        }), 403
    
    subscription = Subscription.query.filter_by(
        id=subscription_id,
        customer_id=user.customer_id
    ).first()
    
    if not subscription:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Subscription not found'
            }
        }), 404
    
    # Include plan details
    result = subscription.to_dict()
    if subscription.plan:
        result['plan'] = subscription.plan.to_dict()
    
    return jsonify({
        'success': True,
        'data': result
    }), 200

@api_bp.route('/portal/invoices', methods=['GET'])
@jwt_required()
def get_portal_invoices():
    """Get invoices for logged-in customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user or not user.customer_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only customer users can access portal'
            }
        }), 403
    
    invoices = Invoice.query.filter_by(customer_id=user.customer_id).order_by(
        Invoice.invoice_date.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': [inv.to_dict() for inv in invoices]
    }), 200

@api_bp.route('/portal/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_portal_invoice(invoice_id):
    """Get specific invoice for logged-in customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user or not user.customer_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only customer users can access portal'
            }
        }), 403
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        customer_id=user.customer_id
    ).first()
    
    if not invoice:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Invoice not found'
            }
        }), 404
    
    # Include line items
    result = invoice.to_dict()
    result['line_items'] = [item.to_dict() for item in invoice.line_items]
    
    return jsonify({
        'success': True,
        'data': result
    }), 200

@api_bp.route('/portal/payments', methods=['GET'])
@jwt_required()
def get_portal_payments():
    """Get payment history for logged-in customer"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user or not user.customer_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only customer users can access portal'
            }
        }), 403
    
    payments = Payment.query.filter_by(customer_id=user.customer_id).order_by(
        Payment.payment_date.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': [payment.to_dict() for payment in payments]
    }), 200

@api_bp.route('/portal/profile', methods=['PATCH'])
@jwt_required()
def update_portal_profile():
    """Update customer profile information"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user or not user.customer_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only customer users can access portal'
            }
        }), 403
    
    data = request.get_json()
    
    # Update user fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    # Update customer fields
    customer = Customer.query.get(user.customer_id)
    if 'phone' in data:
        customer.phone = data['phone']
    if 'billing_address' in data:
        customer.billing_address = data['billing_address']
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(include_email=True),
                'customer': customer.to_dict()
            },
            'message': 'Profile updated successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'Failed to update profile'
            }
        }), 500

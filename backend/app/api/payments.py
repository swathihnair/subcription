"""Payment API routes - Module 3"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Payment, Invoice, User
from app.services import PaymentService
from datetime import datetime
from decimal import Decimal
import uuid


@api_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    """Get list of payments with filtering and pagination"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access payments'
            }
        }), 403
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    status = request.args.get('status', None)
    customer_id = request.args.get('customer_id', None)
    invoice_id = request.args.get('invoice_id', None)
    payment_method = request.args.get('payment_method', None)
    from_date = request.args.get('from_date', None)
    to_date = request.args.get('to_date', None)
    
    # Build filters dict
    filters = {}
    
    if customer_id:
        try:
            filters['customer_id'] = uuid.UUID(customer_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid customer ID format'
                }
            }), 400
    
    if invoice_id:
        try:
            filters['invoice_id'] = uuid.UUID(invoice_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid invoice ID format'
                }
            }), 400
    
    if status:
        filters['status'] = status
    
    if payment_method:
        filters['payment_method'] = payment_method
    
    if from_date:
        try:
            filters['from_date'] = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_DATE',
                    'message': 'Invalid from_date format'
                }
            }), 400
    
    if to_date:
        try:
            filters['to_date'] = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_DATE',
                    'message': 'Invalid to_date format'
                }
            }), 400
    
    # Get payments using service
    payments, total = PaymentService.list_payments(filters, page, page_size)
    
    # Convert to dict
    results = []
    for payment in payments:
        payment_dict = payment.to_dict()
        if payment.customer:
            payment_dict['customer'] = payment.customer.to_dict()
        if payment.invoice:
            payment_dict['invoice'] = {
                'id': str(payment.invoice.id),
                'invoice_number': payment.invoice.invoice_number
            }
        results.append(payment_dict)
    
    total_pages = (total + page_size - 1) // page_size
    
    return jsonify({
        'success': True,
        'data': results,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': total,
            'totalPages': total_pages
        }
    }), 200


@api_bp.route('/payments/<payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """Get single payment by ID"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access payments'
            }
        }), 403
    
    try:
        payment_uuid = uuid.UUID(payment_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid payment ID format'
            }
        }), 400
    
    payment = Payment.query.get(payment_uuid)
    
    if not payment:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Payment not found'
            }
        }), 404
    
    payment_dict = payment.to_dict()
    if payment.customer:
        payment_dict['customer'] = payment.customer.to_dict()
    if payment.invoice:
        payment_dict['invoice'] = payment.invoice.to_dict()
    
    return jsonify({
        'success': True,
        'data': payment_dict
    }), 200


@api_bp.route('/payments', methods=['POST'])
@jwt_required()
def record_payment():
    """Record a new payment"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission - require finance or admin role
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to record payments'
            }
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['invoice_id', 'amount', 'payment_date', 'payment_method']
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
    
    # Validate invoice exists
    try:
        invoice_uuid = uuid.UUID(data['invoice_id'])
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid invoice ID format'
            }
        }), 400
    
    invoice = Invoice.query.get(invoice_uuid)
    if not invoice:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Invoice not found'
            }
        }), 404
    
    # Validate amount
    try:
        amount = Decimal(str(data['amount']))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, TypeError) as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Invalid amount: {str(e)}'
            }
        }), 400
    
    # Parse payment date
    try:
        payment_date = datetime.fromisoformat(data['payment_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_DATE',
                'message': 'Invalid payment_date format'
            }
        }), 400
    
    payment_method = data['payment_method']
    external_transaction_id = data.get('external_transaction_id', None)
    notes = data.get('notes', None)
    
    try:
        payment = PaymentService.record_payment(
            invoice_id=invoice_uuid,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            external_transaction_id=external_transaction_id,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'data': payment.to_dict(),
            'message': 'Payment recorded successfully'
        }), 201
    
    except ValueError as e:
        error_msg = str(e)
        # Determine appropriate error code
        if 'duplicate' in error_msg.lower() or 'already exists' in error_msg.lower():
            error_code = 'CONFLICT'
            status_code = 409
        elif 'void' in error_msg.lower() or 'customer mismatch' in error_msg.lower() or 'overpayment' in error_msg.lower():
            error_code = 'INVALID_STATE'
            status_code = 400
        else:
            error_code = 'VALIDATION_ERROR'
            status_code = 400
        
        return jsonify({
            'success': False,
            'error': {
                'code': error_code,
                'message': error_msg
            }
        }), status_code
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while recording the payment'
            }
        }), 500


@api_bp.route('/payments/<payment_id>/reverse', methods=['POST'])
@jwt_required()
def reverse_payment(payment_id):
    """Reverse a payment"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to reverse payments'
            }
        }), 403
    
    try:
        payment_uuid = uuid.UUID(payment_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid payment ID format'
            }
        }), 400
    
    data = request.get_json() or {}
    reason = data.get('reason', 'Reversed by user')
    
    try:
        payment = PaymentService.reverse_payment(payment_uuid, reason)
        
        return jsonify({
            'success': True,
            'data': payment.to_dict(),
            'message': 'Payment reversed successfully'
        }), 200
    
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': error_msg
                }
            }), 404
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_STATE',
                    'message': error_msg
                }
            }), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'An error occurred while reversing the payment'
            }
        }), 500

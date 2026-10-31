"""Invoice API routes - Module 3"""
from flask import request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Invoice, InvoiceLineItem, Payment, Customer, User
from app.services import InvoiceService, PDFGenerator
from datetime import datetime
from decimal import Decimal
import uuid


@api_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    """Get list of invoices with filtering and pagination"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('view_invoices') and not user.has_permission('all'):
        # Customers can view their own invoices
        if not user.customer_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access invoices'
                }
            }), 403
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    status = request.args.get('status', None)
    customer_id = request.args.get('customer_id', None)
    subscription_id = request.args.get('subscription_id', None)
    from_date = request.args.get('from_date', None)
    to_date = request.args.get('to_date', None)
    
    # Build filters dict
    filters = {}
    
    # Customers can only see their own invoices
    if user.customer_id and not user.has_permission('view_invoices'):
        filters['customer_id'] = user.customer_id
    elif customer_id:
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
    
    if status:
        filters['status'] = status
    
    if subscription_id:
        try:
            filters['subscription_id'] = uuid.UUID(subscription_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid subscription ID format'
                }
            }), 400
    
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
    
    # Get invoices using service
    invoices, total = InvoiceService.list_invoices(filters, page, page_size)
    
    # Convert to dict
    results = []
    for invoice in invoices:
        invoice_dict = invoice.to_dict()
        if invoice.customer:
            invoice_dict['customer'] = invoice.customer.to_dict()
        results.append(invoice_dict)
    
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


@api_bp.route('/invoices/<invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    """Get single invoice by ID with line items"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid invoice ID format'
            }
        }), 400
    
    try:
        invoice = InvoiceService.get_invoice_with_details(invoice_uuid)
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    
    # Check permission
    if not user.has_permission('view_invoices') and not user.has_permission('all'):
        # Customers can only see their own invoices
        if not user.customer_id or invoice.customer_id != user.customer_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access this invoice'
                }
            }), 403
    
    invoice_dict = invoice.to_dict()
    if invoice.customer:
        invoice_dict['customer'] = invoice.customer.to_dict()
    if invoice.subscription:
        invoice_dict['subscription'] = invoice.subscription.to_dict()
    
    # Include line items
    invoice_dict['line_items'] = [item.to_dict() for item in invoice.line_items]
    
    return jsonify({
        'success': True,
        'data': invoice_dict
    }), 200


@api_bp.route('/invoices', methods=['POST'])
@jwt_required()
def create_invoice():
    """Create a new invoice"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission - require finance or admin role
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to create invoices'
            }
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['customer_id', 'invoice_date', 'due_date', 'line_items']
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
    
    # Validate line items
    if not isinstance(data['line_items'], list) or len(data['line_items']) == 0:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'At least one line item is required'
            }
        }), 400
    
    # Parse dates
    try:
        invoice_date = datetime.fromisoformat(data['invoice_date'].replace('Z', '+00:00'))
        due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_DATE',
                'message': 'Invalid date format'
            }
        }), 400
    
    # Convert line items to Decimal
    line_items_data = []
    for item in data['line_items']:
        try:
            line_items_data.append({
                'description': item.get('description', ''),
                'quantity': Decimal(str(item.get('quantity', 1))),
                'unit_price': Decimal(str(item['unit_price'])),
                'tax_rate': Decimal(str(item.get('tax_rate', 0))),
                'discount_amount': Decimal(str(item.get('discount_amount', 0)))
            })
        except (KeyError, ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'Invalid line item data: {str(e)}'
                }
            }), 400
    
    # Optional fields
    subscription_id = None
    if data.get('subscription_id'):
        try:
            subscription_id = uuid.UUID(data['subscription_id'])
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid subscription ID format'
                }
            }), 400
    
    billing_period_start = None
    billing_period_end = None
    if data.get('billing_period_start'):
        try:
            billing_period_start = datetime.fromisoformat(data['billing_period_start'].replace('Z', '+00:00'))
        except ValueError:
            pass
    
    if data.get('billing_period_end'):
        try:
            billing_period_end = datetime.fromisoformat(data['billing_period_end'].replace('Z', '+00:00'))
        except ValueError:
            pass
    
    invoice_type = data.get('invoice_type', 'manual')
    currency = data.get('currency', 'USD')
    
    try:
        invoice = InvoiceService.create_invoice(
            customer_id=customer_uuid,
            invoice_date=invoice_date,
            due_date=due_date,
            line_items_data=line_items_data,
            subscription_id=subscription_id,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            invoice_type=invoice_type,
            currency=currency
        )
        
        invoice_dict = invoice.to_dict()
        invoice_dict['line_items'] = [item.to_dict() for item in invoice.line_items]
        
        return jsonify({
            'success': True,
            'data': invoice_dict,
            'message': 'Invoice created successfully'
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
                'message': 'An error occurred while creating the invoice'
            }
        }), 500


@api_bp.route('/invoices/<invoice_id>/issue', methods=['POST'])
@jwt_required()
def issue_invoice(invoice_id):
    """Issue an invoice (draft → open)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to issue invoices'
            }
        }), 403
    
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid invoice ID format'
            }
        }), 400
    
    try:
        invoice = InvoiceService.issue_invoice(invoice_uuid)
        
        return jsonify({
            'success': True,
            'data': invoice.to_dict(),
            'message': 'Invoice issued successfully'
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
                'message': 'An error occurred while issuing the invoice'
            }
        }), 500


@api_bp.route('/invoices/<invoice_id>/void', methods=['POST'])
@jwt_required()
def void_invoice(invoice_id):
    """Void an invoice"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to void invoices'
            }
        }), 403
    
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid invoice ID format'
            }
        }), 400
    
    data = request.get_json() or {}
    reason = data.get('reason', 'Voided by user')
    
    try:
        invoice = InvoiceService.void_invoice(invoice_uuid, reason)
        
        return jsonify({
            'success': True,
            'data': invoice.to_dict(),
            'message': 'Invoice voided successfully'
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
                'message': 'An error occurred while voiding the invoice'
            }
        }), 500


@api_bp.route('/invoices/<invoice_id>/payments', methods=['GET'])
@jwt_required()
def get_invoice_payments(invoice_id):
    """Get payment history for an invoice"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid invoice ID format'
            }
        }), 400
    
    # Get invoice to check permissions
    invoice = Invoice.query.get(invoice_uuid)
    if not invoice:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Invoice not found'
            }
        }), 404
    
    # Check permission
    if not user.has_permission('view_invoices') and not user.has_permission('all'):
        # Customers can only see their own invoice payments
        if not user.customer_id or invoice.customer_id != user.customer_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access this invoice'
                }
            }), 403
    
    # Get payments
    from app.services import PaymentService
    payments = PaymentService.get_payment_history(invoice_uuid)
    
    return jsonify({
        'success': True,
        'data': [payment.to_dict() for payment in payments]
    }), 200



@api_bp.route('/invoices/<invoice_id>/pdf', methods=['GET'])
@jwt_required()
def download_invoice_pdf(invoice_id):
    """Download invoice as PDF"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid invoice ID format'
            }
        }), 400
    
    # Get invoice to check permissions
    invoice = Invoice.query.get(invoice_uuid)
    if not invoice:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Invoice not found'
            }
        }), 404
    
    # Check permission
    if not user.has_permission('view_invoices') and not user.has_permission('all'):
        # Customers can only download their own invoices
        if not user.customer_id or invoice.customer_id != user.customer_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access this invoice'
                }
            }), 403
    
    try:
        # Generate PDF
        pdf_buffer = PDFGenerator.generate_invoice_pdf(invoice_uuid)
        
        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'invoice_{invoice.invoice_number}.pdf'
        )
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': f'An error occurred while generating PDF: {str(e)}'
            }
        }), 500

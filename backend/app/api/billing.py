"""Billing and Finance API routes - Module 3"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import BillingJob, Invoice, Payment, User
from app.services import BillingEngine, InvoiceService
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func
import uuid


@api_bp.route('/billing/run', methods=['POST'])
@jwt_required()
def run_billing():
    """Trigger manual billing run"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission - require finance or admin role
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to run billing'
            }
        }), 403
    
    data = request.get_json() or {}
    
    # Optional as_of_date parameter
    as_of_date = None
    if data.get('as_of_date'):
        try:
            as_of_date = datetime.fromisoformat(data['as_of_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_DATE',
                    'message': 'Invalid as_of_date format'
                }
            }), 400
    
    try:
        result = BillingEngine.run_billing(as_of_date)
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': result.job_id,
                'subscriptions_processed': result.subscriptions_processed,
                'invoices_created': result.invoices_created,
                'failures_count': len(result.failures),
                'failures': result.failures
            },
            'message': f'Billing completed: {result.invoices_created} invoices created from {result.subscriptions_processed} subscriptions'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': f'An error occurred while running billing: {str(e)}'
            }
        }), 500


@api_bp.route('/billing/jobs', methods=['GET'])
@jwt_required()
def get_billing_jobs():
    """Get billing job history with pagination"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to view billing jobs'
            }
        }), 403
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    status = request.args.get('status', None)
    
    # Build query
    query = BillingJob.query
    
    if status:
        query = query.filter(BillingJob.status == status)
    
    # Order by most recent first
    query = query.order_by(BillingJob.started_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    results = [job.to_dict() for job in pagination.items]
    
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


@api_bp.route('/billing/jobs/<job_id>', methods=['GET'])
@jwt_required()
def get_billing_job(job_id):
    """Get billing job details"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('manage_payments') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to view billing jobs'
            }
        }), 403
    
    try:
        job_id_int = int(job_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_ID',
                'message': 'Invalid job ID format'
            }
        }), 400
    
    job = BillingJob.query.get(job_id_int)
    
    if not job:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Billing job not found'
            }
        }), 404
    
    return jsonify({
        'success': True,
        'data': job.to_dict()
    }), 200


@api_bp.route('/finance/summary', methods=['GET'])
@jwt_required()
def get_finance_summary():
    """Get financial summary (total invoices, paid, outstanding, overdue)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('view_analytics') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to view financial summary'
            }
        }), 403
    
    # Calculate totals
    # Total invoices (not void)
    total_invoices = db.session.query(
        func.count(Invoice.id)
    ).filter(
        Invoice.status != 'void'
    ).scalar() or 0
    
    # Total amount invoiced
    total_invoiced = db.session.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.status != 'void'
    ).scalar() or Decimal('0')
    
    # Total paid
    total_paid = db.session.query(
        func.sum(Invoice.amount_paid)
    ).filter(
        Invoice.status != 'void'
    ).scalar() or Decimal('0')
    
    # Total outstanding (invoices not fully paid and not void)
    total_outstanding = db.session.query(
        func.sum(Invoice.amount_due)
    ).filter(
        Invoice.status.in_(['open', 'partially_paid', 'overdue'])
    ).scalar() or Decimal('0')
    
    # Total overdue
    total_overdue = db.session.query(
        func.sum(Invoice.amount_due)
    ).filter(
        Invoice.status == 'overdue'
    ).scalar() or Decimal('0')
    
    # Count by status
    status_counts = {}
    status_results = db.session.query(
        Invoice.status,
        func.count(Invoice.id),
        func.sum(Invoice.amount_due)
    ).filter(
        Invoice.status != 'void'
    ).group_by(Invoice.status).all()
    
    for status, count, amount_due in status_results:
        status_counts[status] = {
            'count': count,
            'amount_due': float(amount_due or 0)
        }
    
    return jsonify({
        'success': True,
        'data': {
            'total_invoices': total_invoices,
            'total_invoiced': float(total_invoiced),
            'total_paid': float(total_paid),
            'total_outstanding': float(total_outstanding),
            'total_overdue': float(total_overdue),
            'by_status': status_counts
        }
    }), 200


@api_bp.route('/finance/outstanding-balances', methods=['GET'])
@jwt_required()
def get_outstanding_balances():
    """Get outstanding balances per customer"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check permission
    if not user.has_permission('view_analytics') and not user.has_permission('all'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to view outstanding balances'
            }
        }), 403
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    customer_id = request.args.get('customer_id', None)
    
    # Build query - group invoices by customer
    from app.models import Customer
    
    query = db.session.query(
        Customer.id,
        Customer.name,
        Customer.email,
        func.sum(Invoice.amount_due).label('total_outstanding'),
        func.count(Invoice.id).label('invoice_count')
    ).join(
        Invoice, Invoice.customer_id == Customer.id
    ).filter(
        Invoice.status.in_(['open', 'partially_paid', 'overdue'])
    ).group_by(
        Customer.id, Customer.name, Customer.email
    )
    
    # Filter by customer if provided
    if customer_id:
        try:
            customer_uuid = uuid.UUID(customer_id)
            query = query.filter(Customer.id == customer_uuid)
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ID',
                    'message': 'Invalid customer ID format'
                }
            }), 400
    
    # Order by highest outstanding first
    query = query.order_by(func.sum(Invoice.amount_due).desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.limit(page_size).offset(offset).all()
    
    data = []
    for customer_id, customer_name, email, total_outstanding, invoice_count in results:
        data.append({
            'customer_id': str(customer_id),
            'company_name': customer_name,
            'email': email,
            'total_outstanding': float(total_outstanding or 0),
            'invoice_count': invoice_count
        })
    
    total_pages = (total + page_size - 1) // page_size
    
    return jsonify({
        'success': True,
        'data': data,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': total,
            'totalPages': total_pages
        }
    }), 200

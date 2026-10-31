"""Audit log API routes - Module 4"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import User, AuditLog

def check_audit_permission(user):
    """Check if user has permission to access audit logs"""
    if not user or not user.role:
        return False
    return user.role.name in ['admin']

@api_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs with filtering"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not check_audit_permission(user):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Only admin users can access audit logs'
            }
        }), 403
    
    # Get filter parameters
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id', type=int)
    action = request.args.get('action')
    user_filter = request.args.get('user_id', type=int)
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 50))
    
    # Build query
    query = AuditLog.query
    
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    if action:
        query = query.filter_by(action=action)
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    # Order by most recent first
    query = query.order_by(AuditLog.created_at.desc())
    
    # Paginate
    total = query.count()
    logs = query.limit(page_size).offset((page - 1) * page_size).all()
    
    # Convert to dict and add user info
    result = []
    for log in logs:
        log_dict = log.to_dict()
        if log.user:
            log_dict['user'] = {
                'id': str(log.user.id),
                'email': log.user.email,
                'name': f"{log.user.first_name or ''} {log.user.last_name or ''}".strip()
            }
        result.append(log_dict)
    
    return jsonify({
        'success': True,
        'data': result,
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': total,
            'totalPages': (total + page_size - 1) // page_size
        }
    }), 200

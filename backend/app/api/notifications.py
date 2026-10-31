"""Notifications API routes - Module 4"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.extensions import db
from app.models import Notification, User
from datetime import datetime

@api_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for current user"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found'
            }
        }), 404
    
    # Get query parameters
    type_filter = request.args.get('type')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    
    # Build query based on user role
    if user.customer_id:
        # Customer users see notifications for their customer
        query = Notification.query.filter_by(customer_id=user.customer_id)
    else:
        # Internal users see notifications for their user account
        query = Notification.query.filter_by(user_id=user.id)
    
    # Apply type filter
    if type_filter:
        query = query.filter_by(type=type_filter)
    
    # Order and paginate
    query = query.order_by(Notification.created_at.desc())
    total = query.count()
    notifications = query.limit(page_size).offset((page - 1) * page_size).all()
    
    return jsonify({
        'success': True,
        'data': [notification.to_dict() for notification in notifications],
        'pagination': {
            'page': page,
            'pageSize': page_size,
            'total': total,
            'totalPages': (total + page_size - 1) // page_size
        }
    }), 200

@api_bp.route('/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get count of unread notifications"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found'
            }
        }), 404
    
    # Count based on user role
    if user.customer_id:
        count = Notification.query.filter_by(
            customer_id=user.customer_id,
            is_read=False
        ).count()
    else:
        count = Notification.query.filter_by(
            user_id=user.id,
            is_read=False
        ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'count': count
        }
    }), 200

@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found'
            }
        }), 404
    
    # Find notification and verify ownership
    if user.customer_id:
        notification = Notification.query.filter_by(
            id=notification_id,
            customer_id=user.customer_id
        ).first()
    else:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user.id
        ).first()
    
    if not notification:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Notification not found'
            }
        }), 404
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'data': notification.to_dict(),
            'message': 'Notification marked as read'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'Failed to mark notification as read'
            }
        }), 500

@api_bp.route('/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_read():
    """Mark all notifications as read"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found'
            }
        }), 404
    
    # Get unread notifications
    if user.customer_id:
        notifications = Notification.query.filter_by(
            customer_id=user.customer_id,
            is_read=False
        ).all()
    else:
        notifications = Notification.query.filter_by(
            user_id=user.id,
            is_read=False
        ).all()
    
    # Mark all as read
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Marked {len(notifications)} notifications as read'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYSTEM_ERROR',
                'message': 'Failed to mark notifications as read'
            }
        }), 500

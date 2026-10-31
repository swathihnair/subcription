"""Audit logging service - Module 4"""
from app.extensions import db
from app.models import AuditLog
from flask import request
import os

class AuditService:
    """Service for audit logging"""
    
    # Action constants
    ACTION_CREATED = 'created'
    ACTION_UPDATED = 'updated'
    ACTION_DELETED = 'deleted'
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_STATUS_CHANGED = 'status_changed'
    
    @staticmethod
    def is_enabled():
        """Check if audit logging is enabled"""
        return os.getenv('ENABLE_AUDIT_LOGGING', 'True').lower() == 'true'
    
    @staticmethod
    def log(user_id, action, entity_type, entity_id=None, old_values=None, new_values=None):
        """Create an audit log entry"""
        if not AuditService.is_enabled():
            return None
        
        # Get request context if available
        ip_address = None
        user_agent = None
        
        try:
            if request:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')[:500]
        except:
            pass
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(audit_log)
        
        try:
            db.session.commit()
            return audit_log
        except Exception as e:
            db.session.rollback()
            print(f"Audit log failed: {str(e)}")
            return None
    
    @staticmethod
    def log_login(user):
        """Log user login"""
        return AuditService.log(
            user_id=user.id,
            action=AuditService.ACTION_LOGIN,
            entity_type='User',
            entity_id=user.id
        )
    
    @staticmethod
    def log_logout(user):
        """Log user logout"""
        return AuditService.log(
            user_id=user.id,
            action=AuditService.ACTION_LOGOUT,
            entity_type='User',
            entity_id=user.id
        )
    
    @staticmethod
    def log_created(user_id, entity_type, entity_id, new_values=None):
        """Log entity creation"""
        return AuditService.log(
            user_id=user_id,
            action=AuditService.ACTION_CREATED,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=new_values
        )
    
    @staticmethod
    def log_updated(user_id, entity_type, entity_id, old_values=None, new_values=None):
        """Log entity update"""
        return AuditService.log(
            user_id=user_id,
            action=AuditService.ACTION_UPDATED,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values
        )
    
    @staticmethod
    def log_deleted(user_id, entity_type, entity_id, old_values=None):
        """Log entity deletion"""
        return AuditService.log(
            user_id=user_id,
            action=AuditService.ACTION_DELETED,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values
        )
    
    @staticmethod
    def log_status_change(user_id, entity_type, entity_id, old_status, new_status):
        """Log status change"""
        return AuditService.log(
            user_id=user_id,
            action=AuditService.ACTION_STATUS_CHANGED,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values={'status': old_status},
            new_values={'status': new_status}
        )

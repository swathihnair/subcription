"""Audit and notification models - Module 4 owner"""
from app.extensions import db
from datetime import datetime

class AuditLog(db.Model):
    """Audit log model - Module 4 owner"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    action = db.Column(db.String(100), nullable=False)  # created, updated, deleted, login, logout
    entity_type = db.Column(db.String(100), nullable=False)  # User, Customer, Invoice, etc.
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Change tracking
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    
    # IP and user agent
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    # Timestamp
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
        }

class Notification(db.Model):
    """Notification model - Module 4 owner"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    type = db.Column(db.String(100), nullable=False)  # invoice_due, payment_received, subscription_expiring, etc.
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    
    # Channel
    channel = db.Column(db.String(50), default='in_app')  # in_app, email, sms
    
    # External reference
    external_id = db.Column(db.String(255))  # For email provider tracking
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    sent_at = db.Column(db.DateTime(timezone=True))
    read_at = db.Column(db.DateTime(timezone=True))
    
    def __repr__(self):
        return f'<Notification {self.type}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id) if self.customer_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'type': self.type,
            'subject': self.subject,
            'message': self.message,
            'is_read': self.is_read,
            'is_sent': self.is_sent,
            'channel': self.channel,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
        }

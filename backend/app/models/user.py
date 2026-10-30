"""User and Role models"""
from app.extensions import db
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    """User role model"""
    __tablename__ = 'roles'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
        }

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Foreign Keys
    role_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=False)
    customer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime(timezone=True))
    
    # Relationships
    customer = db.relationship('Customer', backref='users')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, foreign_keys='AuditLog.user_id')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Hash and set password"""
        if not password or len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role"""
        # Permission mapping by role
        role_permissions = {
            'admin': ['all'],
            'finance': ['view_invoices', 'manage_payments', 'view_analytics'],
            'sales': ['manage_customers', 'manage_products', 'manage_subscriptions'],
            'customer': ['view_own_subscriptions', 'view_own_invoices']
        }
        
        if not self.role:
            return False
        
        permissions = role_permissions.get(self.role.name, [])
        return 'all' in permissions or permission in permissions
    
    def record_login(self):
        """Record user login timestamp"""
        self.last_login_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_email=False):
        """Convert to dictionary"""
        result = {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'role': self.role.to_dict() if self.role else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_email:
            result['email'] = self.email
        return result

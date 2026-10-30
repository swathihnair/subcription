"""Core business models: Customer, Product, Plan, Quotation, Subscription"""
from app.extensions import db
from datetime import datetime
import uuid

class Customer(db.Model):
    """Customer model - Module 2 owner"""
    __tablename__ = 'customers'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='active', nullable=False)  # active, inactive, churned
    
    # Contact information
    phone = db.Column(db.String(20))
    billing_address = db.Column(db.Text)
    shipping_address = db.Column(db.Text)
    
    # Financial tracking
    total_contract_value = db.Column(db.Numeric(15, 2), default=0)
    annual_recurring_revenue = db.Column(db.Numeric(15, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='customer', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='customer', lazy=True, cascade='all, delete-orphan')
    quotations = db.relationship('Quotation', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Customer {self.name}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'status': self.status,
            'phone': self.phone,
            'total_contract_value': float(self.total_contract_value) if self.total_contract_value else 0,
            'annual_recurring_revenue': float(self.annual_recurring_revenue) if self.annual_recurring_revenue else 0,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class Product(db.Model):
    """Product model - Module 2 owner"""
    __tablename__ = 'products'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='active', nullable=False)  # active, discontinued, draft
    
    # Pricing
    base_price = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plans = db.relationship('Plan', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.sku}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'sku': self.sku,
            'description': self.description,
            'status': self.status,
            'base_price': float(self.base_price),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class Plan(db.Model):
    """Plan model - Module 2 owner"""
    __tablename__ = 'plans'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('products.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='active', nullable=False)
    
    # Pricing
    price = db.Column(db.Numeric(15, 2), nullable=False)
    billing_cycle = db.Column(db.String(20), nullable=False)  # monthly, quarterly, annually
    setup_fee = db.Column(db.Numeric(15, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='plan', lazy=True)
    quotations = db.relationship('Quotation', backref='plan', lazy=True)
    
    def __repr__(self):
        return f'<Plan {self.name}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'product_id': str(self.product_id),
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'price': float(self.price),
            'billing_cycle': self.billing_cycle,
            'setup_fee': float(self.setup_fee) if self.setup_fee else 0,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class Quotation(db.Model):
    """Quotation model - Module 2 owner"""
    __tablename__ = 'quotations'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=False)
    plan_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('plans.id'), nullable=False)
    
    quote_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='draft', nullable=False)  # draft, sent, accepted, rejected, expired
    
    # Pricing
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(15, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Timeline
    valid_until = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Quotation {self.quote_number}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'plan_id': str(self.plan_id),
            'quote_number': self.quote_number,
            'status': self.status,
            'amount': float(self.amount),
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'total_amount': float(self.total_amount),
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class Subscription(db.Model):
    """Subscription model - Module 2/3 owner (Module 2 leads)"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=False)
    plan_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('plans.id'), nullable=False)
    
    subscription_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='active', nullable=False)  # active, suspended, cancelled, churned
    
    # Financial tracking
    monthly_recurring_revenue = db.Column(db.Numeric(15, 2), default=0)
    annual_contract_value = db.Column(db.Numeric(15, 2), default=0)
    
    # Dates
    start_date = db.Column(db.DateTime(timezone=True), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True))
    next_billing_date = db.Column(db.DateTime(timezone=True))
    auto_renew = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='subscription', lazy=True)
    
    def __repr__(self):
        return f'<Subscription {self.subscription_number}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'plan_id': str(self.plan_id),
            'subscription_number': self.subscription_number,
            'status': self.status,
            'monthly_recurring_revenue': float(self.monthly_recurring_revenue) if self.monthly_recurring_revenue else 0,
            'annual_contract_value': float(self.annual_contract_value) if self.annual_contract_value else 0,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
            'auto_renew': self.auto_renew,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

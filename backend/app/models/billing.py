"""Billing models: Invoice, Payment - Module 3 owner"""
from app.extensions import db
from datetime import datetime
import uuid

class Invoice(db.Model):
    """Invoice model - Module 3 owner"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=False)
    subscription_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('subscriptions.id'), nullable=True)
    
    invoice_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='draft', nullable=False)  # draft, sent, viewed, partially_paid, paid, overdue, cancelled
    
    # Financial
    subtotal = db.Column(db.Numeric(15, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(15, 2), default=0)
    amount_due = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Dates
    invoice_date = db.Column(db.DateTime(timezone=True), nullable=False)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    sent_date = db.Column(db.DateTime(timezone=True))
    
    # Additional info
    notes = db.Column(db.Text)
    memo = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    line_items = db.relationship('InvoiceLineItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy=True)
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'subscription_id': str(self.subscription_id) if self.subscription_id else None,
            'invoice_number': self.invoice_number,
            'status': self.status,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'total_amount': float(self.total_amount),
            'amount_paid': float(self.amount_paid) if self.amount_paid else 0,
            'amount_due': float(self.amount_due),
            'invoice_date': self.invoice_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class InvoiceLineItem(db.Model):
    """Invoice line item model - Module 3 owner"""
    __tablename__ = 'invoice_line_items'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('invoices.id'), nullable=False)
    
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit_price = db.Column(db.Numeric(15, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0)  # percentage
    
    # Calculated fields
    line_total = db.Column(db.Numeric(15, 2), nullable=False)
    tax_total = db.Column(db.Numeric(15, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InvoiceLineItem {self.id}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'invoice_id': str(self.invoice_id),
            'description': self.description,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'tax_rate': float(self.tax_rate) if self.tax_rate else 0,
            'line_total': float(self.line_total),
            'tax_total': float(self.tax_total) if self.tax_total else 0,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class Payment(db.Model):
    """Payment model - Module 3 owner"""
    __tablename__ = 'payments'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('invoices.id'), nullable=False)
    customer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('customers.id'), nullable=False)
    
    payment_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, processing, completed, failed, refunded
    
    # Financial
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_method = db.Column(db.String(50))  # credit_card, bank_transfer, check, other
    
    # External references
    external_transaction_id = db.Column(db.String(255))  # For Stripe or other payment provider
    
    # Dates
    payment_date = db.Column(db.DateTime(timezone=True), nullable=False)
    processed_at = db.Column(db.DateTime(timezone=True))
    
    # Additional info
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.payment_number}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'invoice_id': str(self.invoice_id),
            'customer_id': str(self.customer_id),
            'payment_number': self.payment_number,
            'status': self.status,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'external_transaction_id': self.external_transaction_id,
            'payment_date': self.payment_date.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

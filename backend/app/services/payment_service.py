"""Payment service for recording and managing payments"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from app.extensions import db
from app.models.billing import Payment, Invoice


class PaymentService:
    """Service for payment recording and reconciliation"""
    
    @staticmethod
    def generate_payment_number() -> str:
        """
        Generate unique payment number in format: PAY-YYYYMMDD-XXXXX
        
        Returns:
            Unique payment number string
        """
        date_str = datetime.utcnow().strftime('%Y%m%d')
        
        # Find highest payment number for today
        prefix = f'PAY-{date_str}-'
        last_payment = Payment.query.filter(
            Payment.payment_number.like(f'{prefix}%')
        ).order_by(Payment.payment_number.desc()).first()
        
        if last_payment:
            # Extract sequence number and increment
            last_num = int(last_payment.payment_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f'{prefix}{next_num:05d}'
    
    @staticmethod
    def record_payment(
        invoice_id: int,
        amount: Decimal,
        payment_date: datetime,
        payment_method: str,
        external_transaction_id: Optional[str] = None,
        notes: Optional[str] = None,
        status: str = 'completed'
    ) -> Payment:
        """
        Record a payment and update invoice balance.
        
        Args:
            invoice_id: Invoice ID to apply payment to
            amount: Payment amount
            payment_date: Date of payment
            payment_method: Payment method (credit_card, bank_transfer, check, cash, other)
            external_transaction_id: Optional external provider transaction ID
            notes: Optional payment notes
            status: Payment status (default: completed)
            
        Returns:
            Created Payment object
            
        Raises:
            ValueError: If validation fails or invoice not found
        """
        # Validate invoice exists
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Validate customer matches
        customer_id = invoice.customer_id
        
        # Check invoice status
        if invoice.status == 'void':
            raise ValueError("Cannot apply payment to voided invoice")
        
        # Validate amount
        if amount <= 0:
            raise ValueError(f"Payment amount must be positive: {amount}")
        
        # Check for overpayment
        if amount > invoice.amount_due:
            raise ValueError(
                f"Payment amount ({amount}) exceeds invoice balance ({invoice.amount_due})"
            )
        
        # Check for duplicate external transaction ID
        if external_transaction_id:
            existing_payment = Payment.query.filter_by(
                external_transaction_id=external_transaction_id
            ).first()
            if existing_payment:
                # Idempotent: return existing payment
                return existing_payment
        
        # Generate payment number
        payment_number = PaymentService.generate_payment_number()
        
        try:
            # Create payment
            payment = Payment(
                invoice_id=invoice_id,
                customer_id=customer_id,
                payment_number=payment_number,
                status=status,
                amount=amount,
                payment_method=payment_method,
                external_transaction_id=external_transaction_id,
                payment_date=payment_date,
                processed_at=datetime.utcnow() if status == 'completed' else None,
                notes=notes
            )
            
            db.session.add(payment)
            
            # Update invoice if payment is completed
            if status == 'completed':
                PaymentService._update_invoice_balance(invoice, amount)
            
            db.session.commit()
            return payment
            
        except Exception as e:
            db.session.rollback()
            raise
    
    @staticmethod
    def _update_invoice_balance(invoice: Invoice, payment_amount: Decimal):
        """
        Update invoice balance after payment.
        
        Args:
            invoice: Invoice object to update
            payment_amount: Amount being paid
        """
        # Update amount_paid
        invoice.amount_paid = (invoice.amount_paid or Decimal('0')) + payment_amount
        
        # Recalculate amount_due
        invoice.amount_due = invoice.total_amount - invoice.amount_paid
        
        # Round to avoid floating point issues
        invoice.amount_due = invoice.amount_due.quantize(Decimal('0.01'))
        
        # Update status based on balance
        if invoice.amount_due == 0:
            invoice.status = 'paid'
        elif invoice.amount_due < invoice.total_amount:
            invoice.status = 'partially_paid'
    
    @staticmethod
    def reverse_payment(payment_id: int, reason: str) -> Payment:
        """
        Reverse a payment (update status to 'reversed').
        
        Args:
            payment_id: Payment ID to reverse
            reason: Reason for reversal
            
        Returns:
            Updated Payment object
            
        Raises:
            ValueError: If payment not found or already reversed
        """
        payment = Payment.query.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        if payment.status == 'reversed':
            raise ValueError("Payment is already reversed")
        
        if payment.status != 'completed':
            raise ValueError(f"Can only reverse completed payments. Current status: {payment.status}")
        
        try:
            # Update payment status
            payment.status = 'reversed'
            if payment.notes:
                payment.notes += f"\n\nReversed: {reason}"
            else:
                payment.notes = f"Reversed: {reason}"
            
            # Reverse invoice balance
            invoice = Invoice.query.get(payment.invoice_id)
            if invoice:
                invoice.amount_paid = (invoice.amount_paid or Decimal('0')) - payment.amount
                invoice.amount_due = invoice.total_amount - invoice.amount_paid
                invoice.amount_due = invoice.amount_due.quantize(Decimal('0.01'))
                
                # Update invoice status
                if invoice.amount_due == invoice.total_amount:
                    invoice.status = 'open'
                elif invoice.amount_due > 0:
                    invoice.status = 'partially_paid'
            
            db.session.commit()
            return payment
            
        except Exception as e:
            db.session.rollback()
            raise
    
    @staticmethod
    def get_payment_history(invoice_id: int) -> List[Payment]:
        """
        Get all payments for an invoice.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            List of Payment objects ordered by payment_date desc
        """
        payments = Payment.query.filter_by(
            invoice_id=invoice_id
        ).order_by(Payment.payment_date.desc()).all()
        
        return payments
    
    @staticmethod
    def list_payments(
        customer_id: Optional[int] = None,
        invoice_id: Optional[int] = None,
        status: Optional[str] = None,
        payment_method: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List payments with optional filters and pagination.
        
        Args:
            customer_id: Optional filter by customer
            invoice_id: Optional filter by invoice
            status: Optional filter by status
            payment_method: Optional filter by payment method
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Dict with 'payments' list and 'pagination' info
        """
        query = Payment.query
        
        if customer_id:
            query = query.filter(Payment.customer_id == customer_id)
        
        if invoice_id:
            query = query.filter(Payment.invoice_id == invoice_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        
        # Order by payment_date descending
        query = query.order_by(Payment.payment_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        return {
            'payments': pagination.items,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

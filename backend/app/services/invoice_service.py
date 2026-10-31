"""Invoice service for managing invoices and line items"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from app.extensions import db
from app.models.billing import Invoice, InvoiceLineItem
from app.services.financial_calculator import FinancialCalculator


class InvoiceService:
    """Service for invoice CRUD operations and management"""
    
    @staticmethod
    def generate_invoice_number() -> str:
        """
        Generate unique invoice number in format: INV-YYYYMMDD-XXXXX
        
        Returns:
            Unique invoice number string
        """
        date_str = datetime.utcnow().strftime('%Y%m%d')
        
        # Find highest invoice number for today
        prefix = f'INV-{date_str}-'
        last_invoice = Invoice.query.filter(
            Invoice.invoice_number.like(f'{prefix}%')
        ).order_by(Invoice.invoice_number.desc()).first()
        
        if last_invoice:
            # Extract sequence number and increment
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f'{prefix}{next_num:05d}'
    
    @staticmethod
    def create_invoice(
        customer_id: int,
        invoice_date: datetime,
        due_date: datetime,
        line_items_data: List[Dict[str, Any]],
        subscription_id: Optional[int] = None,
        billing_period_start: Optional[datetime] = None,
        billing_period_end: Optional[datetime] = None,
        invoice_type: str = 'one_time',
        currency: str = 'USD',
        discount_amount: Decimal = Decimal('0'),
        notes: Optional[str] = None,
        memo: Optional[str] = None
    ) -> Invoice:
        """
        Create a new invoice with line items.
        
        Args:
            customer_id: Customer ID
            invoice_date: Invoice issue date
            due_date: Payment due date
            line_items_data: List of line item dicts with description, quantity, unit_price, tax_rate, discount_amount
            subscription_id: Optional subscription ID for recurring invoices
            billing_period_start: Optional billing period start (for recurring)
            billing_period_end: Optional billing period end (for recurring)
            invoice_type: 'recurring' or 'one_time'
            currency: Currency code (default USD)
            discount_amount: Invoice-level discount
            notes: Internal notes
            memo: Customer-visible memo
            
        Returns:
            Created Invoice object
            
        Raises:
            ValueError: If validation fails or totals don't reconcile
        """
        # Validate inputs
        if not line_items_data:
            raise ValueError("Invoice must have at least one line item")
        
        # Generate invoice number
        invoice_number = InvoiceService.generate_invoice_number()
        
        # Calculate line items
        line_items = []
        for item_data in line_items_data:
            quantity = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(item_data['unit_price']))
            tax_rate = Decimal(str(item_data.get('tax_rate', 0)))
            item_discount = Decimal(str(item_data.get('discount_amount', 0)))
            
            # Validate amounts
            if quantity <= 0:
                raise ValueError(f"Quantity must be positive: {quantity}")
            if unit_price < 0:
                raise ValueError(f"Unit price cannot be negative: {unit_price}")
            
            # Calculate line total and tax
            line_total = FinancialCalculator.calculate_line_total(
                quantity, unit_price, item_discount
            )
            tax_total = FinancialCalculator.calculate_line_tax(line_total, tax_rate)
            
            line_items.append({
                'description': item_data['description'],
                'quantity': quantity,
                'unit_price': unit_price,
                'tax_rate': tax_rate,
                'discount_amount': item_discount,
                'discount_type': item_data.get('discount_type'),
                'line_total': line_total,
                'tax_total': tax_total
            })
        
        # Calculate invoice totals
        totals = FinancialCalculator.calculate_invoice_totals(line_items)
        
        # Apply invoice-level discount
        total_amount = totals.total_amount - discount_amount
        total_amount = total_amount.quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
        
        # Validate discount doesn't exceed subtotal
        if discount_amount > totals.subtotal:
            raise ValueError(
                f"Discount amount ({discount_amount}) cannot exceed subtotal ({totals.subtotal})"
            )
        
        # Create invoice
        invoice = Invoice(
            customer_id=customer_id,
            subscription_id=subscription_id,
            invoice_number=invoice_number,
            status='draft',
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            invoice_type=invoice_type,
            currency=currency,
            subtotal=totals.subtotal,
            tax_amount=totals.total_tax,
            discount_amount=discount_amount,
            total_amount=total_amount,
            amount_paid=Decimal('0'),
            amount_due=total_amount,
            invoice_date=invoice_date,
            due_date=due_date,
            notes=notes,
            memo=memo
        )
        
        try:
            db.session.add(invoice)
            db.session.flush()  # Get invoice ID
            
            # Create line items
            for item_data in line_items:
                line_item = InvoiceLineItem(
                    invoice_id=invoice.id,
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    tax_rate=item_data['tax_rate'],
                    discount_amount=item_data['discount_amount'],
                    discount_type=item_data['discount_type'],
                    line_total=item_data['line_total'],
                    tax_total=item_data['tax_total']
                )
                db.session.add(line_item)
            
            # Validate totals before commit
            invoice_dict = {
                'subtotal': invoice.subtotal,
                'tax_amount': invoice.tax_amount,
                'discount_amount': invoice.discount_amount,
                'total_amount': invoice.total_amount,
                'amount_paid': invoice.amount_paid,
                'amount_due': invoice.amount_due,
                'line_items': line_items
            }
            
            if not FinancialCalculator.validate_totals(invoice_dict):
                raise ValueError("Invoice totals do not reconcile correctly")
            
            db.session.commit()
            return invoice
            
        except Exception as e:
            db.session.rollback()
            raise
    
    @staticmethod
    def issue_invoice(invoice_id: int) -> Invoice:
        """
        Issue a draft invoice (change status to 'open').
        
        Args:
            invoice_id: Invoice ID to issue
            
        Returns:
            Updated Invoice object
            
        Raises:
            ValueError: If invoice is not in draft status
        """
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        if invoice.status != 'draft':
            raise ValueError(f"Can only issue draft invoices. Current status: {invoice.status}")
        
        invoice.status = 'open'
        invoice.sent_date = datetime.utcnow()
        
        db.session.commit()
        return invoice
    
    @staticmethod
    def void_invoice(invoice_id: int, reason: str) -> Invoice:
        """
        Void an invoice (change status to 'void').
        
        Args:
            invoice_id: Invoice ID to void
            reason: Reason for voiding
            
        Returns:
            Updated Invoice object
        """
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        if invoice.status == 'void':
            raise ValueError("Invoice is already voided")
        
        invoice.status = 'void'
        if invoice.notes:
            invoice.notes += f"\n\nVoided: {reason}"
        else:
            invoice.notes = f"Voided: {reason}"
        
        db.session.commit()
        return invoice
    
    @staticmethod
    def update_overdue_invoices() -> int:
        """
        Update invoice statuses to 'overdue' for unpaid invoices past due_date.
        
        Returns:
            Count of invoices marked overdue
        """
        now = datetime.utcnow()
        
        overdue_invoices = Invoice.query.filter(
            Invoice.status.in_(['open', 'partially_paid']),
            Invoice.due_date < now,
            Invoice.amount_due > 0
        ).all()
        
        count = 0
        for invoice in overdue_invoices:
            invoice.status = 'overdue'
            count += 1
        
        if count > 0:
            db.session.commit()
        
        return count
    
    @staticmethod
    def get_invoice_with_details(invoice_id: int) -> Optional[Invoice]:
        """
        Fetch invoice with line items eager loaded.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice object with line_items loaded, or None if not found
        """
        from sqlalchemy.orm import joinedload
        
        invoice = Invoice.query.options(
            joinedload(Invoice.line_items),
            joinedload(Invoice.payments)
        ).get(invoice_id)
        
        return invoice
    
    @staticmethod
    def list_invoices(
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List invoices with optional filters and pagination.
        
        Args:
            customer_id: Optional filter by customer
            status: Optional filter by status
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Dict with 'invoices' list and 'pagination' info
        """
        query = Invoice.query
        
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        
        if status:
            query = query.filter(Invoice.status == status)
        
        # Order by invoice_date descending
        query = query.order_by(Invoice.invoice_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        return {
            'invoices': pagination.items,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

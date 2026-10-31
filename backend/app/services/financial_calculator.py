"""Financial calculator service for precise monetary calculations"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, NamedTuple


class InvoiceTotals(NamedTuple):
    """Container for calculated invoice totals"""
    subtotal: Decimal
    total_tax: Decimal
    total_amount: Decimal


class FinancialCalculator:
    """
    Service for performing financial calculations with proper precision.
    
    Uses Decimal arithmetic to ensure accurate monetary calculations
    and consistent rounding.
    """
    
    # Configuration
    DECIMAL_PLACES = 2
    ROUNDING_MODE = ROUND_HALF_UP
    
    @staticmethod
    def calculate_line_total(
        quantity: Decimal,
        unit_price: Decimal,
        discount_amount: Decimal = Decimal('0')
    ) -> Decimal:
        """
        Calculate line item total before tax.
        
        Formula: (quantity * unit_price) - discount_amount
        
        Args:
            quantity: Number of units
            unit_price: Price per unit
            discount_amount: Discount to subtract from gross
            
        Returns:
            Line total rounded to DECIMAL_PLACES
        """
        gross = quantity * unit_price
        line_total = gross - discount_amount
        return line_total.quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
    
    @staticmethod
    def calculate_line_tax(
        line_total: Decimal,
        tax_rate: Decimal
    ) -> Decimal:
        """
        Calculate tax amount for a line item.
        
        Formula: line_total * (tax_rate / 100)
        
        Args:
            line_total: Line total after discount
            tax_rate: Tax rate as percentage (e.g., 8.5 for 8.5%)
            
        Returns:
            Tax amount rounded to DECIMAL_PLACES
        """
        tax_amount = line_total * (tax_rate / Decimal('100'))
        return tax_amount.quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
    
    @staticmethod
    def calculate_invoice_totals(line_items: List[dict]) -> InvoiceTotals:
        """
        Calculate invoice subtotal, total tax, and total amount.
        
        Args:
            line_items: List of line item dicts with 'line_total' and 'tax_total'
            
        Returns:
            InvoiceTotals with subtotal, total_tax, and total_amount
        """
        subtotal = sum(
            Decimal(str(item.get('line_total', 0))) 
            for item in line_items
        )
        
        total_tax = sum(
            Decimal(str(item.get('tax_total', 0))) 
            for item in line_items
        )
        
        total_amount = subtotal + total_tax
        
        # Round all totals
        subtotal = subtotal.quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
        total_tax = total_tax.quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
        total_amount = total_amount.quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
        
        return InvoiceTotals(
            subtotal=subtotal,
            total_tax=total_tax,
            total_amount=total_amount
        )
    
    @staticmethod
    def validate_totals(invoice: dict) -> bool:
        """
        Validate that invoice totals are correctly calculated.
        
        Checks:
        - subtotal == sum of line_totals
        - tax_amount == sum of line tax_totals
        - total_amount == subtotal - discount_amount + tax_amount
        - amount_due == total_amount - amount_paid
        
        Args:
            invoice: Invoice dict with totals and line_items
            
        Returns:
            True if all totals reconcile correctly, False otherwise
        """
        line_items = invoice.get('line_items', [])
        
        # Calculate expected subtotal
        expected_subtotal = sum(
            Decimal(str(item.get('line_total', 0)))
            for item in line_items
        ).quantize(Decimal('0.01'), rounding=FinancialCalculator.ROUNDING_MODE)
        
        # Calculate expected tax
        expected_tax = sum(
            Decimal(str(item.get('tax_total', 0)))
            for item in line_items
        ).quantize(Decimal('0.01'), rounding=FinancialCalculator.ROUNDING_MODE)
        
        # Get invoice values
        subtotal = Decimal(str(invoice.get('subtotal', 0)))
        tax_amount = Decimal(str(invoice.get('tax_amount', 0)))
        discount_amount = Decimal(str(invoice.get('discount_amount', 0)))
        total_amount = Decimal(str(invoice.get('total_amount', 0)))
        amount_paid = Decimal(str(invoice.get('amount_paid', 0)))
        amount_due = Decimal(str(invoice.get('amount_due', 0)))
        
        # Check subtotal
        if subtotal != expected_subtotal:
            return False
        
        # Check tax
        if tax_amount != expected_tax:
            return False
        
        # Check total amount
        expected_total = (subtotal - discount_amount + tax_amount).quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
        if total_amount != expected_total:
            return False
        
        # Check amount due
        expected_due = (total_amount - amount_paid).quantize(
            Decimal('0.01'),
            rounding=FinancialCalculator.ROUNDING_MODE
        )
        if amount_due != expected_due:
            return False
        
        return True

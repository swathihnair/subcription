"""Billing engine for processing recurring subscriptions"""
from datetime import datetime
from decimal import Decimal
from typing import Tuple, List, Optional, Dict, Any
from dateutil.relativedelta import relativedelta
import json

from app.extensions import db
from app.models.core import Subscription, Plan
from app.models.billing import Invoice, BillingJob
from app.services.invoice_service import InvoiceService


class InvoiceResult:
    """Result of processing a single subscription"""
    def __init__(self, success: bool, invoice_id: Optional[int] = None, error: Optional[str] = None, skipped: bool = False):
        self.success = success
        self.invoice_id = invoice_id
        self.error = error
        self.skipped = skipped


class BillingJobResult:
    """Result of a billing job execution"""
    def __init__(self, job_id: int, subscriptions_processed: int, invoices_created: int, failures: List[Dict]):
        self.job_id = job_id
        self.subscriptions_processed = subscriptions_processed
        self.invoices_created = invoices_created
        self.failures = failures


class BillingEngine:
    """Service for processing subscriptions and generating recurring invoices"""
    
    @staticmethod
    def calculate_billing_period(
        next_billing_date: datetime,
        billing_cycle: str
    ) -> Tuple[datetime, datetime]:
        """
        Calculate billing period start and end dates.
        
        Handles month-end dates consistently and leap years correctly.
        
        Args:
            next_billing_date: The subscription's next billing date
            billing_cycle: 'monthly', 'quarterly', or 'yearly'
            
        Returns:
            Tuple of (billing_period_start, billing_period_end)
            
        Raises:
            ValueError: If billing_cycle is invalid
        """
        billing_period_start = next_billing_date
        
        if billing_cycle == 'monthly':
            # Add 1 month
            billing_period_end = next_billing_date + relativedelta(months=1)
        elif billing_cycle == 'quarterly':
            # Add 3 months
            billing_period_end = next_billing_date + relativedelta(months=3)
        elif billing_cycle == 'yearly':
            # Add 1 year
            billing_period_end = next_billing_date + relativedelta(years=1)
        else:
            raise ValueError(f"Invalid billing cycle: {billing_cycle}. Must be monthly, quarterly, or yearly")
        
        return billing_period_start, billing_period_end
    
    @staticmethod
    def calculate_next_billing_date(
        current_billing_date: datetime,
        billing_cycle: str
    ) -> datetime:
        """
        Calculate the next billing date after current billing date.
        
        Args:
            current_billing_date: Current billing date
            billing_cycle: 'monthly', 'quarterly', or 'yearly'
            
        Returns:
            Next billing date
        """
        if billing_cycle == 'monthly':
            return current_billing_date + relativedelta(months=1)
        elif billing_cycle == 'quarterly':
            return current_billing_date + relativedelta(months=3)
        elif billing_cycle == 'yearly':
            return current_billing_date + relativedelta(years=1)
        else:
            raise ValueError(f"Invalid billing cycle: {billing_cycle}")
    
    @staticmethod
    def get_eligible_subscriptions(as_of_date: Optional[datetime] = None) -> List[Subscription]:
        """
        Query subscriptions eligible for billing.
        
        Args:
            as_of_date: Date to check eligibility against (defaults to now)
            
        Returns:
            List of eligible subscriptions
        """
        if as_of_date is None:
            as_of_date = datetime.utcnow()
        
        # Query subscriptions that are:
        # - status = 'active'
        # - next_billing_date <= as_of_date
        # - next_billing_date is not None
        eligible_subscriptions = Subscription.query.filter(
            Subscription.status == 'active',
            Subscription.next_billing_date.isnot(None),
            Subscription.next_billing_date <= as_of_date
        ).all()
        
        return eligible_subscriptions
    
    @staticmethod
    def check_for_existing_invoice(
        subscription_id: int,
        billing_period_start: datetime,
        billing_period_end: datetime
    ) -> Optional[Invoice]:
        """
        Check if invoice already exists for this subscription and billing period.
        
        Args:
            subscription_id: Subscription ID
            billing_period_start: Billing period start date
            billing_period_end: Billing period end date
            
        Returns:
            Existing Invoice if found, None otherwise
        """
        existing_invoice = Invoice.query.filter(
            Invoice.subscription_id == subscription_id,
            Invoice.billing_period_start == billing_period_start,
            Invoice.billing_period_end == billing_period_end,
            Invoice.invoice_type == 'recurring'
        ).first()
        
        return existing_invoice
    
    @staticmethod
    def process_subscription(subscription: Subscription) -> InvoiceResult:
        """
        Process a single subscription and create invoice if needed.
        
        Args:
            subscription: The subscription to bill
            
        Returns:
            InvoiceResult with success/error info
        """
        try:
            # Get plan details
            plan = Plan.query.get(subscription.plan_id)
            if not plan:
                return InvoiceResult(
                    success=False,
                    error=f"Plan {subscription.plan_id} not found"
                )
            
            # Calculate billing period
            billing_period_start, billing_period_end = BillingEngine.calculate_billing_period(
                subscription.next_billing_date,
                plan.billing_cycle
            )
            
            # Check for existing invoice (duplicate prevention)
            existing_invoice = BillingEngine.check_for_existing_invoice(
                subscription.id,
                billing_period_start,
                billing_period_end
            )
            
            if existing_invoice:
                # Already billed, skip (idempotent)
                return InvoiceResult(
                    success=True,
                    invoice_id=existing_invoice.id,
                    skipped=True
                )
            
            # Create invoice line items from plan
            # Preserve plan price as historical snapshot
            line_items_data = [{
                'description': f"{plan.name} - {plan.billing_cycle} subscription",
                'quantity': Decimal('1'),
                'unit_price': plan.price,
                'tax_rate': Decimal('0'),  # Tax can be configured per customer/region
                'discount_amount': Decimal('0')
            }]
            
            # Set invoice dates
            invoice_date = datetime.utcnow()
            # Due date is 30 days from invoice date (configurable)
            due_date = invoice_date + relativedelta(days=30)
            
            # Create invoice
            invoice = InvoiceService.create_invoice(
                customer_id=subscription.customer_id,
                invoice_date=invoice_date,
                due_date=due_date,
                line_items_data=line_items_data,
                subscription_id=subscription.id,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                invoice_type='recurring',
                currency='USD'
            )
            
            # Update subscription next_billing_date
            subscription.next_billing_date = BillingEngine.calculate_next_billing_date(
                subscription.next_billing_date,
                plan.billing_cycle
            )
            db.session.commit()
            
            return InvoiceResult(
                success=True,
                invoice_id=invoice.id
            )
            
        except Exception as e:
            db.session.rollback()
            return InvoiceResult(
                success=False,
                error=str(e)
            )
    
    @staticmethod
    def run_billing(as_of_date: Optional[datetime] = None) -> BillingJobResult:
        """
        Execute billing run for all eligible subscriptions.
        
        Args:
            as_of_date: Date to use for eligibility (defaults to now)
            
        Returns:
            BillingJobResult with counts and errors
        """
        if as_of_date is None:
            as_of_date = datetime.utcnow()
        
        # Create billing job record
        billing_job = BillingJob(
            status='running',
            started_at=as_of_date,
            subscriptions_processed=0,
            invoices_created=0,
            failures_count=0,
            error_log=None
        )
        db.session.add(billing_job)
        db.session.commit()
        
        try:
            # Get eligible subscriptions
            eligible_subscriptions = BillingEngine.get_eligible_subscriptions(as_of_date)
            
            subscriptions_processed = 0
            invoices_created = 0
            failures = []
            
            for subscription in eligible_subscriptions:
                result = BillingEngine.process_subscription(subscription)
                subscriptions_processed += 1
                
                if result.success:
                    if not result.skipped:
                        invoices_created += 1
                else:
                    failures.append({
                        'subscription_id': subscription.id,
                        'subscription_number': subscription.subscription_number,
                        'error': result.error
                    })
            
            # Update billing job record
            billing_job.status = 'completed'
            billing_job.completed_at = datetime.utcnow()
            billing_job.subscriptions_processed = subscriptions_processed
            billing_job.invoices_created = invoices_created
            billing_job.failures_count = len(failures)
            
            if failures:
                billing_job.error_log = json.dumps(failures)
            
            db.session.commit()
            
            return BillingJobResult(
                job_id=billing_job.id,
                subscriptions_processed=subscriptions_processed,
                invoices_created=invoices_created,
                failures=failures
            )
            
        except Exception as e:
            # Mark job as failed
            billing_job.status = 'failed'
            billing_job.completed_at = datetime.utcnow()
            billing_job.error_log = json.dumps([{'error': str(e)}])
            db.session.commit()
            raise

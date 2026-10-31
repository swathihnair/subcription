"""Notification service for creating and sending notifications - Module 4"""
from app.extensions import db
from app.models import Notification, Customer, User
from datetime import datetime
import os

class NotificationService:
    """Service for managing notifications"""
    
    # Notification type constants
    SUBSCRIPTION_CREATED = 'subscription_created'
    SUBSCRIPTION_ACTIVATED = 'subscription_activated'
    RENEWAL_APPROACHING = 'renewal_approaching'
    INVOICE_ISSUED = 'invoice_issued'
    INVOICE_DUE_SOON = 'invoice_due_soon'
    INVOICE_OVERDUE = 'invoice_overdue'
    PAYMENT_RECORDED = 'payment_recorded'
    SUBSCRIPTION_CANCELLED = 'subscription_cancelled'
    
    @staticmethod
    def create_notification(notification_type, subject, message, customer_id=None, user_id=None, channel='in_app'):
        """Create a new notification"""
        notification = Notification(
            type=notification_type,
            subject=subject,
            message=message,
            customer_id=customer_id,
            user_id=user_id,
            channel=channel,
            is_read=False,
            is_sent=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    @staticmethod
    def send_email(notification):
        """Send notification via email (placeholder for actual email implementation)"""
        # Check if email is configured
        email_enabled = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
        
        if not email_enabled:
            # Email not configured, keep as in-app only
            return False
        
        # TODO: Implement actual email sending using configured email service
        # Example: SendGrid, AWS SES, or SMTP
        # This is a placeholder that should be implemented when email is configured
        
        try:
            # Mark as sent
            notification.is_sent = True
            notification.sent_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            # Log error but don't fail
            print(f"Email send failed: {str(e)}")
            return False
    
    @staticmethod
    def notify_subscription_created(subscription):
        """Notify customer about subscription creation"""
        customer = subscription.customer
        if not customer:
            return None
        
        subject = "Your subscription has been created"
        message = f"Your subscription {subscription.subscription_number} for {subscription.plan.name if subscription.plan else 'a plan'} has been created."
        
        return NotificationService.create_notification(
            NotificationService.SUBSCRIPTION_CREATED,
            subject,
            message,
            customer_id=customer.id
        )
    
    @staticmethod
    def notify_renewal_approaching(subscription, days_until):
        """Notify customer about upcoming renewal"""
        customer = subscription.customer
        if not customer:
            return None
        
        subject = f"Subscription renewal in {days_until} days"
        message = f"Your subscription {subscription.subscription_number} will renew on {subscription.next_billing_date.strftime('%Y-%m-%d') if subscription.next_billing_date else 'soon'}."
        
        return NotificationService.create_notification(
            NotificationService.RENEWAL_APPROACHING,
            subject,
            message,
            customer_id=customer.id
        )
    
    @staticmethod
    def notify_invoice_issued(invoice):
        """Notify customer about new invoice"""
        customer = invoice.customer
        if not customer:
            return None
        
        subject = f"Invoice {invoice.invoice_number} issued"
        message = f"A new invoice {invoice.invoice_number} for ${float(invoice.total_amount):.2f} has been issued. Due date: {invoice.due_date.strftime('%Y-%m-%d')}."
        
        return NotificationService.create_notification(
            NotificationService.INVOICE_ISSUED,
            subject,
            message,
            customer_id=customer.id
        )
    
    @staticmethod
    def notify_invoice_due_soon(invoice, days_until):
        """Notify customer about invoice due soon"""
        customer = invoice.customer
        if not customer:
            return None
        
        subject = f"Invoice {invoice.invoice_number} due in {days_until} days"
        message = f"Invoice {invoice.invoice_number} for ${float(invoice.amount_due):.2f} is due on {invoice.due_date.strftime('%Y-%m-%d')}."
        
        return NotificationService.create_notification(
            NotificationService.INVOICE_DUE_SOON,
            subject,
            message,
            customer_id=customer.id
        )
    
    @staticmethod
    def notify_invoice_overdue(invoice):
        """Notify customer about overdue invoice"""
        customer = invoice.customer
        if not customer:
            return None
        
        subject = f"Invoice {invoice.invoice_number} is overdue"
        message = f"Invoice {invoice.invoice_number} for ${float(invoice.amount_due):.2f} is now overdue. Please submit payment as soon as possible."
        
        return NotificationService.create_notification(
            NotificationService.INVOICE_OVERDUE,
            subject,
            message,
            customer_id=customer.id
        )
    
    @staticmethod
    def notify_payment_recorded(payment):
        """Notify customer about payment received"""
        customer = payment.customer if hasattr(payment, 'customer') else None
        if not customer:
            customer = Customer.query.get(payment.customer_id)
        if not customer:
            return None
        
        subject = f"Payment received - {payment.payment_number}"
        message = f"Your payment of ${float(payment.amount):.2f} has been received and processed."
        
        return NotificationService.create_notification(
            NotificationService.PAYMENT_RECORDED,
            subject,
            message,
            customer_id=customer.id
        )
    
    @staticmethod
    def notify_subscription_cancelled(subscription):
        """Notify customer about subscription cancellation"""
        customer = subscription.customer
        if not customer:
            return None
        
        subject = f"Subscription {subscription.subscription_number} cancelled"
        message = f"Your subscription {subscription.subscription_number} has been cancelled."
        if subscription.end_date:
            message += f" It will remain active until {subscription.end_date.strftime('%Y-%m-%d')}."
        
        return NotificationService.create_notification(
            NotificationService.SUBSCRIPTION_CANCELLED,
            subject,
            message,
            customer_id=customer.id
        )

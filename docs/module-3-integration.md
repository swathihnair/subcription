# Module 3 Integration Guide

This document describes how Module 3 (Billing, Invoices & Finance) integrates with other modules.

## Overview

Module 3 provides billing, invoicing, payment tracking, and financial reporting capabilities. It integrates with:
- **Module 2 (Subscriptions)** - Generates recurring invoices
- **Module 4 (Analytics)** - Provides financial data for reporting

## Integration with Module 2: Subscriptions

### Data Dependencies

Module 3 **reads** from Module 2:

| Model | Fields Used | Purpose |
|-------|-------------|---------|
| `Subscription` | `id`, `customer_id`, `plan_id`, `status`, `next_billing_date` | Identify subscriptions to bill |
| `Plan` | `id`, `name`, `price`, `billing_cycle` | Create invoice line items with pricing |
| `Customer` | `id`, `company_name`, `email`, `billing_address` | Invoice customer information |

### Data Flow: Recurring Billing

```
┌─────────────────┐
│  Subscription   │
│  status: active │
│  next_billing_  │
│  date: today    │
└────────┬────────┘
         │
         ├─ BillingEngine queries eligible subscriptions
         │
         ▼
┌─────────────────┐
│  Create Invoice │
│  - Fetch Plan   │
│  - Create Line  │
│    Items        │
│  - Snapshot     │
│    Price        │
└────────┬────────┘
         │
         ├─ Invoice created with billing_period
         │
         ▼
┌─────────────────┐
│ Update Sub      │
│ next_billing_   │
│ date = +1 cycle │
└─────────────────┘
```

### Subscription Model Requirements

**Required fields for billing:**
- `next_billing_date` (datetime) - When to bill next
- `status` (string) - Must be 'active' to bill
- `customer_id` (UUID) - Links to customer
- `plan_id` (UUID) - Links to plan for pricing

**Status handling:**
- `active` - Will be billed
- `paused` - Skipped (not billed)
- `cancelled` - Skipped (not billed)
- `trial` - Skipped (not billed)

### Billing Date Updates

**Module 3 WRITES to Module 2:**

When an invoice is created, Module 3 updates:
```python
subscription.next_billing_date = calculate_next_billing_date(
    subscription.next_billing_date,
    plan.billing_cycle
)
```

**Important:** This is the **only** write operation from Module 3 to Module 2.

### Integration Points

#### 1. Invoice Creation from Subscription

```python
# Module 3: BillingEngine.process_subscription()

# Read from Module 2
subscription = Subscription.query.get(subscription_id)
plan = Plan.query.get(subscription.plan_id)

# Create invoice
invoice = InvoiceService.create_invoice(
    customer_id=subscription.customer_id,
    subscription_id=subscription.id,
    billing_period_start=period_start,
    billing_period_end=period_end,
    line_items_data=[{
        'description': f"{plan.name} - {plan.billing_cycle}",
        'quantity': 1,
        'unit_price': plan.price  # Historical snapshot
    }]
)

# Update Module 2
subscription.next_billing_date = next_date
db.session.commit()
```

#### 2. Manual Invoice Creation

Invoices can be created manually without a subscription:

```python
# No subscription reference
invoice = InvoiceService.create_invoice(
    customer_id=customer_id,
    subscription_id=None,  # Manual invoice
    line_items_data=[...]
)
```

#### 3. Subscription Cancellation Impact

When a subscription is cancelled in Module 2:
- Existing invoices remain unchanged
- No new invoices will be created (status != 'active')
- Outstanding invoices still need payment

### API Integration Examples

#### Check Subscription Invoices

```python
# In Module 2: Get subscription with invoices
GET /api/v1/subscriptions/{id}

# Response includes invoices from Module 3
{
  "subscription": {
    "id": "...",
    "status": "active",
    "invoices": [
      {
        "id": "...",
        "invoice_number": "INV-...",
        "total_amount": 100.00,
        "status": "paid"
      }
    ]
  }
}
```

#### Filter Invoices by Subscription

```python
# In Module 3: Get invoices for subscription
GET /api/v1/invoices?subscription_id={id}
```

---

## Integration with Module 4: Analytics

### Data Provided to Analytics

Module 3 exposes financial data for reporting:

| Endpoint | Data Provided |
|----------|---------------|
| `/finance/summary` | Total invoiced, paid, outstanding, overdue |
| `/finance/outstanding-balances` | Per-customer outstanding amounts |
| `/invoices` | Detailed invoice data with filters |
| `/payments` | Payment history with filters |

### Available Metrics

#### Revenue Metrics
- **Total Invoiced:** Sum of all non-void invoice `total_amount`
- **Total Paid:** Sum of all invoice `amount_paid`
- **Total Outstanding:** Sum of invoice `amount_due` where status = open/partially_paid/overdue

#### Performance Metrics
- **Collection Rate:** `total_paid / total_invoiced`
- **Overdue Rate:** `total_overdue / total_outstanding`
- **Average Invoice Value:** `total_invoiced / invoice_count`

#### Customer Metrics
- **Outstanding per Customer:** Group by customer, sum `amount_due`
- **Payment History:** Count and sum payments per customer

### API Integration Examples

#### Financial Dashboard

```python
# Get financial summary
GET /api/v1/finance/summary

{
  "total_invoiced": 100000.00,
  "total_paid": 95000.00,
  "total_outstanding": 5000.00,
  "total_overdue": 1200.00,
  "by_status": {
    "paid": {"count": 150, "amount_due": 0},
    "open": {"count": 20, "amount_due": 3800},
    "overdue": {"count": 5, "amount_due": 1200}
  }
}
```

#### Revenue Over Time

```python
# Get invoices within date range
GET /api/v1/invoices?from_date=2026-10-01&to_date=2026-10-31

# Aggregate by month/week for charts
# Group by invoice_date, sum total_amount
```

#### Customer Payment Analysis

```python
# Get outstanding balances
GET /api/v1/finance/outstanding-balances

# Get payment history for customer
GET /api/v1/payments?customer_id={id}
```

### Data Models for Analytics

#### Invoice Model

```python
{
  "id": "uuid",
  "invoice_number": "INV-...",
  "customer_id": "uuid",
  "subscription_id": "uuid or null",
  "invoice_date": "datetime",
  "due_date": "datetime",
  "billing_period_start": "datetime or null",
  "billing_period_end": "datetime or null",
  "status": "draft|open|partially_paid|paid|overdue|void",
  "subtotal_amount": "decimal",
  "tax_amount": "decimal",
  "total_amount": "decimal",
  "amount_paid": "decimal",
  "amount_due": "decimal",
  "currency": "string",
  "invoice_type": "recurring|manual"
}
```

#### Payment Model

```python
{
  "id": "uuid",
  "payment_number": "PAY-...",
  "customer_id": "uuid",
  "invoice_id": "uuid",
  "amount": "decimal",
  "payment_date": "datetime",
  "payment_method": "string",
  "status": "pending|completed|failed|reversed"
}
```

---

## Database Relationships

### Foreign Keys

```sql
-- Module 3 references Module 2
invoices.customer_id → customers.id
invoices.subscription_id → subscriptions.id (nullable)
payments.customer_id → customers.id
payments.invoice_id → invoices.id

-- Module 3 internal relationships
invoice_line_items.invoice_id → invoices.id
payments.invoice_id → invoices.id
```

### Cascade Behavior

**Important:** Deleting entities in Module 2 affects Module 3:

| Action | Impact on Module 3 | Recommendation |
|--------|-------------------|----------------|
| Delete Customer | **Blocks** if invoices exist | Soft-delete or void invoices first |
| Delete Subscription | Sets `invoice.subscription_id = NULL` | Safe (historical data preserved) |
| Delete Plan | **No impact** (prices are snapshotted) | Safe |

---

## Event-Driven Integration (Future)

For real-time integration, consider event-driven architecture:

### Subscription Events → Billing

```python
# Module 2 publishes events
@event.publish('subscription.activated')
def activate_subscription(subscription):
    # Set initial next_billing_date
    pass

@event.publish('subscription.paused')
def pause_subscription(subscription):
    # No action needed (billing checks status)
    pass

@event.publish('subscription.cancelled')
def cancel_subscription(subscription):
    # No action needed (billing checks status)
    pass
```

### Billing Events → Analytics

```python
# Module 3 publishes events
@event.publish('invoice.created')
def invoice_created(invoice):
    # Analytics can cache/aggregate data
    pass

@event.publish('payment.recorded')
def payment_recorded(payment):
    # Analytics updates revenue metrics
    pass
```

---

## Migration Considerations

### Adding Module 3 to Existing System

If Module 2 is already deployed:

1. **Install Module 3** (models, migrations, services)
2. **Run migrations** to create invoice/payment tables
3. **Set initial `next_billing_date`** on existing subscriptions:
   ```python
   for subscription in Subscription.query.filter_by(status='active'):
       if not subscription.next_billing_date:
           subscription.next_billing_date = subscription.start_date + billing_cycle
   ```
4. **Test billing run** manually: `POST /api/v1/billing/run`
5. **Enable scheduler** once verified

### Data Consistency

**Before enabling billing:**
- Verify all subscriptions have `next_billing_date`
- Verify all plans have valid `price` and `billing_cycle`
- Verify all customers have valid billing information

---

## API Security

### Cross-Module Authorization

Users need appropriate permissions:

| User Role | Module 2 Access | Module 3 Access |
|-----------|----------------|----------------|
| `admin` | All operations | All operations |
| `finance` | View subscriptions | Manage invoices/payments |
| `sales` | Manage subscriptions | View invoices (customer scope) |
| `customer` | View own subscriptions | View own invoices |

### Example: Customer Access

```python
# Customer can view own subscription
GET /api/v1/subscriptions/{id}  # ✓ if owned

# Customer can view invoices for that subscription
GET /api/v1/invoices?subscription_id={id}  # ✓ if owned

# Customer cannot create invoices
POST /api/v1/invoices  # ✗ 403 Forbidden
```

---

## Testing Integration

### Integration Test Example

```python
def test_billing_creates_invoice_and_updates_subscription():
    # Setup: Create subscription (Module 2)
    subscription = create_test_subscription(
        status='active',
        next_billing_date=datetime.utcnow()
    )
    
    # Execute: Run billing (Module 3)
    result = BillingEngine.run_billing()
    
    # Assert: Invoice created
    invoices = Invoice.query.filter_by(subscription_id=subscription.id).all()
    assert len(invoices) == 1
    assert invoices[0].status == 'draft'
    
    # Assert: Subscription updated
    subscription = Subscription.query.get(subscription.id)
    assert subscription.next_billing_date > datetime.utcnow()
```

---

## Support

For integration issues:
- Review database foreign key constraints
- Check application logs for cross-module queries
- Verify permissions for cross-module API calls
- Test manually before enabling scheduled billing

---

## Summary

### Module 2 → Module 3 (Reads)
- Subscriptions, Plans, Customers (for billing)

### Module 3 → Module 2 (Writes)
- Updates `subscription.next_billing_date` only

### Module 3 → Module 4 (Provides)
- Financial metrics and reporting data

### Key Integration Points
1. **Billing Engine:** Reads subscriptions, creates invoices, updates billing dates
2. **Invoice Service:** Can link to subscriptions or be standalone
3. **Finance API:** Provides aggregated data for analytics

# Module 4 Setup and Testing Guide

## Quick Start

### Prerequisites

Module 4 requires Modules 1, 2, and 3 to be functional for full integration.

### Backend Setup

1. Ensure backend dependencies are installed:
```bash
cd backend
pip install -r requirements.txt
```

2. Run database migrations (if not already done):
```bash
flask db upgrade
```

3. Set environment variables in `.env`:
```env
ENABLE_AUDIT_LOGGING=True
EMAIL_ENABLED=False  # Set to True when email service is configured
```

4. Start the backend:
```bash
flask run
```

Backend runs on `http://localhost:5000`

### Frontend Setup

1. Ensure frontend dependencies are installed:
```bash
cd frontend
npm install
```

2. Start the frontend:
```bash
npm run dev
```

Frontend runs on `http://localhost:5173`

## Testing Module 4

### Running Backend Tests

```bash
cd backend

# Run all Module 4 tests
pytest tests/test_portal.py tests/test_notifications.py tests/test_analytics.py -v

# Run specific test file
pytest tests/test_portal.py -v

# Run with coverage
pytest tests/test_portal.py tests/test_notifications.py tests/test_analytics.py --cov=app/api --cov=app/services -v
```

### Manual Testing

#### 1. Test Customer Portal

**Create a customer user:**
```bash
cd backend
flask shell
```

```python
from app import db
from app.models import User, Role, Customer

# Create customer
customer = Customer(
    name='Test Customer Inc',
    email='customer@test.com',
    status='active',
    phone='555-1234'
)
db.session.add(customer)
db.session.flush()

# Create customer user
customer_role = Role.query.filter_by(name='customer').first()
user = User(
    email='customer@test.com',
    first_name='John',
    last_name='Doe',
    role_id=customer_role.id,
    customer_id=customer.id
)
user.set_password('password123')
db.session.add(user)
db.session.commit()
exit()
```

**Test portal access:**
1. Login at `http://localhost:5173/login` with:
   - Email: `customer@test.com`
   - Password: `password123`
2. Navigate to `/portal`
3. Verify you can see customer dashboard
4. Check subscriptions, invoices, and payments (if data exists)

#### 2. Test Analytics Dashboard

**Create admin user (if not exists):**
```python
from app import db
from app.models import User, Role

admin_role = Role.query.filter_by(name='admin').first()
admin = User(
    email='admin@test.com',
    first_name='Admin',
    last_name='User',
    role_id=admin_role.id
)
admin.set_password('admin123')
db.session.add(admin)
db.session.commit()
```

**Test analytics:**
1. Login as admin user
2. Navigate to `/analytics`
3. Verify metrics display:
   - Total customers
   - Active subscriptions
   - MRR/ARR
   - Outstanding invoices
4. Check charts are rendering
5. Verify data matches database state

#### 3. Test Notifications

**Create test notifications:**
```python
from app.services.notification_service import NotificationService

# For customer user
NotificationService.create_notification(
    NotificationService.INVOICE_ISSUED,
    'Test Invoice Issued',
    'Your invoice #INV-001 has been issued for $100.00',
    customer_id=customer.id
)

NotificationService.create_notification(
    NotificationService.PAYMENT_RECORDED,
    'Payment Received',
    'Your payment of $100.00 has been received',
    customer_id=customer.id
)
db.session.commit()
```

**Test notification functionality:**
1. Login as customer user
2. Navigate to `/notifications`
3. Verify notifications are displayed
4. Click "Mark as Read" on a notification
5. Verify unread count decreases
6. Click "Mark All as Read"
7. Filter notifications by type

#### 4. Test Renewals Management

**Create test subscription with renewal date:**
```python
from app.models import Subscription, Product, Plan
from datetime import datetime, timedelta

# Create product and plan if needed
product = Product(
    name='Test Product',
    sku='TEST-001',
    base_price=100,
    status='active'
)
db.session.add(product)
db.session.flush()

plan = Plan(
    product_id=product.id,
    name='Monthly Plan',
    price=100,
    billing_cycle='monthly',
    status='active'
)
db.session.add(plan)
db.session.flush()

# Create subscription due soon
subscription = Subscription(
    customer_id=customer.id,
    plan_id=plan.id,
    subscription_number='SUB-TEST-001',
    status='active',
    start_date=datetime.utcnow(),
    next_billing_date=datetime.utcnow() + timedelta(days=5),
    monthly_recurring_revenue=100,
    auto_renew=True
)
db.session.add(subscription)
db.session.commit()
```

**Test renewals page:**
1. Login as admin, sales, or finance user
2. Navigate to `/renewals`
3. Verify summary cards show counts
4. Check "Due Soon" tab shows the test subscription
5. Switch between tabs
6. Verify subscription details are accurate

#### 5. Test Audit Logs

**Create audit log entries:**
```python
from app.services.audit_service import AuditService

# Log some events
AuditService.log_login(admin)
AuditService.log_created(
    admin.id,
    'Customer',
    customer.id,
    {'name': customer.name, 'email': customer.email}
)
```

**Test audit log viewing:**
1. Login as admin user
2. Navigate to API endpoint or create audit viewer page
3. Filter by entity type, action, user
4. Verify logs show proper information

### API Testing with curl

**Test Portal Endpoints:**
```bash
# Login to get token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@test.com","password":"password123"}'

# Use token in subsequent requests
TOKEN="your-access-token-here"

# Get portal profile
curl http://localhost:5000/api/v1/portal/me \
  -H "Authorization: Bearer $TOKEN"

# Get subscriptions
curl http://localhost:5000/api/v1/portal/subscriptions \
  -H "Authorization: Bearer $TOKEN"

# Get notifications
curl http://localhost:5000/api/v1/notifications \
  -H "Authorization: Bearer $TOKEN"
```

**Test Analytics Endpoints (admin token required):**
```bash
# Login as admin
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'

ADMIN_TOKEN="your-admin-token-here"

# Get analytics overview
curl http://localhost:5000/api/v1/analytics/overview \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get MRR analytics
curl http://localhost:5000/api/v1/analytics/mrr \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get renewals
curl http://localhost:5000/api/v1/renewals \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Creating Test Data

### Complete Test Data Script

```python
from app import create_app, db
from app.models import User, Role, Customer, Product, Plan, Subscription, Invoice, Payment
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta
from decimal import Decimal

app = create_app()
with app.app_context():
    # Create customer
    customer = Customer(
        name='Acme Corporation',
        email='acme@example.com',
        status='active',
        phone='555-0100',
        billing_address='123 Main St, City, State 12345'
    )
    db.session.add(customer)
    db.session.flush()
    
    # Create customer user
    customer_role = Role.query.filter_by(name='customer').first()
    customer_user = User(
        email='john@acme.com',
        first_name='John',
        last_name='Doe',
        role_id=customer_role.id,
        customer_id=customer.id
    )
    customer_user.set_password('password123')
    db.session.add(customer_user)
    
    # Create products and plans
    product1 = Product(name='SaaS Platform', sku='SAAS-001', base_price=99, status='active')
    product2 = Product(name='Enterprise Suite', sku='ENT-001', base_price=499, status='active')
    db.session.add_all([product1, product2])
    db.session.flush()
    
    plan1 = Plan(
        product_id=product1.id,
        name='Basic Monthly',
        price=99,
        billing_cycle='monthly',
        status='active'
    )
    plan2 = Plan(
        product_id=product2.id,
        name='Enterprise Annual',
        price=4990,
        billing_cycle='annually',
        status='active'
    )
    db.session.add_all([plan1, plan2])
    db.session.flush()
    
    # Create subscriptions
    sub1 = Subscription(
        customer_id=customer.id,
        plan_id=plan1.id,
        subscription_number='SUB-2024-001',
        status='active',
        start_date=datetime.utcnow() - timedelta(days=20),
        next_billing_date=datetime.utcnow() + timedelta(days=10),
        monthly_recurring_revenue=99,
        annual_contract_value=1188,
        auto_renew=True
    )
    
    sub2 = Subscription(
        customer_id=customer.id,
        plan_id=plan2.id,
        subscription_number='SUB-2024-002',
        status='active',
        start_date=datetime.utcnow() - timedelta(days=60),
        next_billing_date=datetime.utcnow() + timedelta(days=305),
        monthly_recurring_revenue=416,
        annual_contract_value=4990,
        auto_renew=True
    )
    db.session.add_all([sub1, sub2])
    db.session.flush()
    
    # Create invoices
    inv1 = Invoice(
        customer_id=customer.id,
        subscription_id=sub1.id,
        invoice_number='INV-2024-001',
        status='paid',
        subtotal=99,
        total_amount=99,
        amount_paid=99,
        amount_due=0,
        invoice_date=datetime.utcnow() - timedelta(days=20),
        due_date=datetime.utcnow() - timedelta(days=10)
    )
    
    inv2 = Invoice(
        customer_id=customer.id,
        subscription_id=sub1.id,
        invoice_number='INV-2024-002',
        status='sent',
        subtotal=99,
        total_amount=99,
        amount_due=99,
        invoice_date=datetime.utcnow() - timedelta(days=5),
        due_date=datetime.utcnow() + timedelta(days=25)
    )
    db.session.add_all([inv1, inv2])
    db.session.flush()
    
    # Create payment
    payment = Payment(
        invoice_id=inv1.id,
        customer_id=customer.id,
        payment_number='PAY-2024-001',
        status='completed',
        amount=99,
        payment_method='credit_card',
        payment_date=datetime.utcnow() - timedelta(days=15)
    )
    db.session.add(payment)
    
    # Create notifications
    NotificationService.notify_subscription_created(sub1)
    NotificationService.notify_invoice_issued(inv2)
    NotificationService.notify_payment_recorded(payment)
    
    db.session.commit()
    print("✓ Test data created successfully!")
```

## Troubleshooting

### Issue: 403 Forbidden on portal endpoints
**Solution:** Ensure the user has a customer_id set and is using the customer role.

### Issue: Analytics shows 0 for all metrics
**Solution:** Create test data using the script above. Module 4 reads from existing data.

### Issue: Notifications not appearing
**Solution:** Notifications must be created via NotificationService. Check that customer_id or user_id matches the logged-in user.

### Issue: Charts not rendering
**Solution:** Ensure recharts is installed: `npm install recharts`

### Issue: MRR calculation seems wrong
**Solution:** Verify that subscriptions have monthly_recurring_revenue set correctly. This should be normalized to monthly values regardless of billing cycle.

## Performance Considerations

1. **Pagination:** All list endpoints support pagination. Use page and pageSize parameters.
2. **Caching:** Consider adding query result caching for analytics endpoints in production.
3. **Indexes:** Ensure database indexes exist on frequently queried fields (customer_id, status, created_at).
4. **Date Filters:** Use date range filters for analytics to limit data scanned.

## Security Checklist

- [ ] Customer users can only access their own portal data
- [ ] Attempting to access another customer's subscription returns 404
- [ ] Attempting to access another customer's invoice returns 404
- [ ] Analytics requires admin or finance role
- [ ] Renewals requires admin, sales, or finance role
- [ ] Audit logs require admin role only
- [ ] JWT token is required for all endpoints
- [ ] Notifications are filtered by user ownership

## Next Steps After Setup

1. Integrate notification triggers in Module 2 (subscription events)
2. Integrate notification triggers in Module 3 (invoice/payment events)
3. Configure email service for email notifications
4. Add scheduled jobs for renewal reminders
5. Add invoice PDF generation
6. Implement subscription self-service actions
7. Add historical MRR tracking
8. Set up monitoring and alerting for production

## Support

For issues or questions about Module 4:
1. Check this documentation
2. Review `docs/module-4-completion-status.md`
3. Check API contracts in `docs/api-contracts.md`
4. Review test files for usage examples
5. Contact module owner (Module 4 developer)

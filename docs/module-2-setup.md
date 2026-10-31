# Module 2: Product and Subscription Management - Setup Guide

## Quick Start

### Backend Setup

1. **Activate virtual environment** (if not already activated):
   ```bash
   cd backend
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations** (if not already run):
   ```bash
   flask db upgrade
   ```

4. **Start the backend server**:
   ```bash
   flask run
   ```
   Server will run on `http://localhost:5000`

### Frontend Setup

1. **Install dependencies** (if not already installed):
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```
   Frontend will run on `http://localhost:5173`

## Testing Module 2

### Backend Tests

Run all Module 2 tests:
```bash
cd backend
pytest tests/test_customers.py tests/test_subscriptions.py -v
```

Run with coverage:
```bash
pytest tests/test_customers.py tests/test_subscriptions.py --cov=app.api --cov-report=html
```

Run specific test:
```bash
pytest tests/test_customers.py::test_create_customer_success -v
```

### Manual API Testing

#### 1. Login to get access token:
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@local.dev",
    "password": "password123"
  }'
```

Save the `access_token` from the response.

#### 2. Create a Customer:
```bash
curl -X POST http://localhost:5000/api/v1/customers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Acme Corporation",
    "email": "contact@acme.com",
    "phone": "555-1234"
  }'
```

#### 3. Create a Product:
```bash
curl -X POST http://localhost:5000/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Premium Software",
    "sku": "PREM-001",
    "description": "Premium subscription software",
    "base_price": 99.99
  }'
```

#### 4. Create a Plan:
```bash
curl -X POST http://localhost:5000/api/v1/plans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "product_id": "PRODUCT_ID_FROM_STEP_3",
    "name": "Monthly Plan",
    "price": 99.99,
    "billing_cycle": "monthly",
    "setup_fee": 0
  }'
```

#### 5. Create a Subscription:
```bash
curl -X POST http://localhost:5000/api/v1/subscriptions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "customer_id": "CUSTOMER_ID_FROM_STEP_2",
    "plan_id": "PLAN_ID_FROM_STEP_4"
  }'
```

#### 6. Pause a Subscription:
```bash
curl -X POST http://localhost:5000/api/v1/subscriptions/SUBSCRIPTION_ID/pause \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Frontend Manual Testing

1. **Login**:
   - Navigate to `http://localhost:5173/login`
   - Use credentials: `admin@local.dev` / `password123`

2. **View Products**:
   - Navigate to `http://localhost:5173/products`
   - Test search, filtering, and pagination
   - Test product creation (if form implemented)
   - Test product deactivation

3. **View Subscriptions**:
   - Navigate to `http://localhost:5173/subscriptions`
   - Test filtering by status
   - Test pause/resume/cancel actions

## Development Workflow

### Creating a New Customer

```python
from app.models import Customer
from app.extensions import db

customer = Customer(
    name="Test Corporation",
    email="test@corp.com",
    phone="555-9999",
    status="active"
)
db.session.add(customer)
db.session.commit()
```

### Creating a Product with Plan

```python
from app.models import Product, Plan
from app.extensions import db
from decimal import Decimal

product = Product(
    name="Enterprise Software",
    sku="ENT-001",
    description="Enterprise subscription",
    base_price=Decimal("299.99"),
    status="active"
)
db.session.add(product)
db.session.flush()

plan = Plan(
    product_id=product.id,
    name="Annual Plan",
    price=Decimal("2999.99"),
    billing_cycle="annually",
    setup_fee=Decimal("500.00"),
    status="active"
)
db.session.add(plan)
db.session.commit()
```

### Creating a Subscription

```python
from app.models import Subscription
from app.extensions import db
from datetime import datetime, timedelta
from decimal import Decimal

subscription = Subscription(
    customer_id=customer.id,
    plan_id=plan.id,
    subscription_number="SUB-20241201-1234",
    status="active",
    start_date=datetime.utcnow(),
    next_billing_date=datetime.utcnow() + timedelta(days=30),
    monthly_recurring_revenue=Decimal("299.99"),
    annual_contract_value=Decimal("3599.88"),
    auto_renew=True
)
db.session.add(subscription)
db.session.commit()
```

### Creating and Converting a Quotation

```python
from app.models import Quotation
from app.extensions import db
from datetime import datetime, timedelta
from decimal import Decimal

# Create quotation
quotation = Quotation(
    customer_id=customer.id,
    plan_id=plan.id,
    quote_number="QT-20241201-5678",
    amount=Decimal("2999.99"),
    discount_amount=Decimal("500.00"),
    total_amount=Decimal("2499.99"),
    valid_until=datetime.utcnow() + timedelta(days=30),
    status="draft"
)
db.session.add(quotation)
db.session.commit()

# Accept quotation
quotation.status = "accepted"
db.session.commit()

# Convert to subscription via API:
# POST /api/v1/quotations/{quotation.id}/convert-to-subscription
```

## Common Issues

### 1. Authentication Errors (401)

**Problem**: API returns 401 Unauthorized

**Solution**:
- Ensure you're sending the Bearer token in the Authorization header
- Check if token has expired (default: 1 hour)
- Use the refresh token endpoint if needed: `POST /api/v1/auth/refresh`

### 2. Validation Errors (400)

**Problem**: Required fields missing or invalid

**Solution**:
- Check the error response `details.fields` for missing fields
- Ensure monetary values are valid numbers
- Ensure billing_cycle is one of: weekly, monthly, quarterly, annually

### 3. Duplicate SKU (409)

**Problem**: Cannot create product with existing SKU

**Solution**:
- Use a unique SKU for each product
- Check existing products: `GET /api/v1/products?search=SKU`

### 4. Cannot Deactivate Plan (409)

**Problem**: Plan has active subscriptions

**Solution**:
- Check subscriptions: `GET /api/v1/subscriptions?plan_id=PLAN_ID`
- Cancel or complete all active subscriptions first
- Then deactivate the plan

### 5. Cannot Convert Quotation (400)

**Problem**: Quotation not in correct status

**Solution**:
- Ensure quotation status is "accepted"
- Check expiration date hasn't passed
- Ensure no duplicate active subscription exists

## Database Queries for Debugging

### Check Customers
```sql
SELECT id, name, email, status, created_at 
FROM customers 
ORDER BY created_at DESC 
LIMIT 10;
```

### Check Active Subscriptions
```sql
SELECT s.subscription_number, c.name as customer, p.name as plan, s.status, s.next_billing_date
FROM subscriptions s
JOIN customers c ON s.customer_id = c.id
JOIN plans p ON s.plan_id = p.id
WHERE s.status = 'active'
ORDER BY s.created_at DESC;
```

### Check MRR by Customer
```sql
SELECT c.name, SUM(s.monthly_recurring_revenue) as total_mrr
FROM subscriptions s
JOIN customers c ON s.customer_id = c.id
WHERE s.status IN ('active', 'trialing')
GROUP BY c.id, c.name
ORDER BY total_mrr DESC;
```

### Check Quotations Ready for Conversion
```sql
SELECT q.quote_number, c.name, q.total_amount, q.valid_until
FROM quotations q
JOIN customers c ON q.customer_id = c.id
WHERE q.status = 'accepted'
  AND q.valid_until > NOW()
ORDER BY q.created_at DESC;
```

## API Response Examples

### Success Response
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Acme Corporation",
    "email": "contact@acme.com",
    "status": "active",
    "created_at": "2024-12-01T10:30:00Z"
  },
  "message": "Customer created successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required fields",
    "details": {
      "fields": ["email", "name"]
    }
  }
}
```

### Paginated Response
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 156,
    "totalPages": 8
  }
}
```

## Performance Tips

1. **Use Pagination**: Always use pagination for list endpoints
2. **Filter Early**: Apply status filters to reduce dataset size
3. **Index Usage**: Database indexes exist on:
   - customer email
   - product SKU
   - subscription number
   - quotation number
   - status fields

4. **Avoid N+1 Queries**: API includes related data to minimize queries

## Security Checklist

- ✅ All endpoints require authentication
- ✅ Role-based permissions enforced
- ✅ Input validation on all fields
- ✅ SQL injection prevention (ORM usage)
- ✅ No secrets in code or commits
- ✅ CORS configured properly
- ✅ Error messages don't leak sensitive info

## Support

For questions or issues:
1. Check this setup guide
2. Review `docs/module-2-completion-status.md`
3. Check `docs/api-contracts.md` for API details
4. Contact Module 2 developer or team lead

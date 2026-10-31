# Module 3: Deployment Checklist

Use this checklist to ensure Module 3 (Billing, Invoices & Finance) is deployed correctly.

## Pre-Deployment

### Code Deployment
- [ ] All Module 3 code merged to main branch
- [ ] Code reviewed and approved
- [ ] All tests passing (unit tests for services)
- [ ] No linting/syntax errors

### Database
- [ ] Migration files reviewed
- [ ] Migration tested in staging environment
- [ ] Database backup completed
- [ ] Rollback plan documented

### Dependencies
- [ ] `requirements.txt` updated with new dependencies:
  - [ ] `reportlab` (PDF generation)
  - [ ] `APScheduler` (scheduled jobs)
  - [ ] `python-dateutil` (date calculations)
- [ ] Dependencies installed in target environment
- [ ] Python version compatible (3.7+)

### Configuration
- [ ] Environment variables documented
- [ ] `.env.example` updated with new variables
- [ ] Secrets/credentials secured (if any)

---

## Deployment Steps

### 1. Database Migration

**⚠️ CRITICAL: Run migrations BEFORE code deployment**

```bash
# Backup database first
pg_dump subscriptiq_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
cd backend
flask db upgrade

# Verify tables created
flask shell
>>> from app.models.billing import Invoice, Payment, BillingJob
>>> Invoice.query.count()  # Should return 0 (new table)
```

**Verify:**
- [ ] `invoices` table exists
- [ ] `invoice_line_items` table exists
- [ ] `payments` table exists
- [ ] `billing_jobs` table exists
- [ ] Indexes created (check `pg_indexes` table)
- [ ] Foreign key constraints exist

### 2. Deploy Code

```bash
# Pull latest code
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Restart application
systemctl restart subscriptiq
# or
docker-compose restart backend
```

**Verify:**
- [ ] Application starts without errors
- [ ] Logs show successful initialization
- [ ] Health check endpoint responds: `GET /api/v1/health`

### 3. Configure Scheduler

**Decide on scheduler strategy:**

#### Option A: Dedicated Scheduler Instance (Recommended)

Deploy one instance with scheduler enabled:

```bash
# Scheduler instance
ENABLE_SCHEDULER=true
BILLING_CRON=0 0 * * *
OVERDUE_CHECK_CRON=0 1 * * *

# All other instances
ENABLE_SCHEDULER=false
```

#### Option B: External Cron (Alternative)

Disable built-in scheduler and use external cron:

```bash
# All instances
ENABLE_SCHEDULER=false

# Add to system cron
0 0 * * * curl -X POST https://api.example.com/api/v1/billing/run \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Verify:**
- [ ] Only ONE instance has `ENABLE_SCHEDULER=true`
- [ ] Scheduler logs appear in application logs
- [ ] APScheduler jobs table created

### 4. Verify API Endpoints

Test all new endpoints:

```bash
# Test invoice creation
curl -X POST https://api.example.com/api/v1/invoices \
  -H "Authorization: Bearer $FINANCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "...",
    "invoice_date": "2026-10-31T00:00:00Z",
    "due_date": "2026-11-30T00:00:00Z",
    "line_items": [{"description": "Test", "quantity": 1, "unit_price": 100, "tax_rate": 10}]
  }'

# Test invoice listing
curl https://api.example.com/api/v1/invoices \
  -H "Authorization: Bearer $FINANCE_TOKEN"

# Test payment recording
curl -X POST https://api.example.com/api/v1/payments \
  -H "Authorization: Bearer $FINANCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "...",
    "amount": 110.00,
    "payment_date": "2026-10-31T12:00:00Z",
    "payment_method": "credit_card"
  }'

# Test financial summary
curl https://api.example.com/api/v1/finance/summary \
  -H "Authorization: Bearer $FINANCE_TOKEN"

# Test PDF generation
curl https://api.example.com/api/v1/invoices/{id}/pdf \
  -H "Authorization: Bearer $FINANCE_TOKEN" \
  -o test_invoice.pdf
```

**Verify:**
- [ ] All endpoints return expected responses
- [ ] Authorization working correctly (403 for unauthorized)
- [ ] Data validation working (400 for invalid data)
- [ ] PDF downloads successfully

---

## Post-Deployment

### 5. Test Billing Workflow

**Manual test of complete billing flow:**

```bash
# 1. Ensure test subscription exists with next_billing_date = today
# 2. Trigger manual billing run
curl -X POST https://api.example.com/api/v1/billing/run \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. Verify invoice created
curl https://api.example.com/api/v1/invoices?subscription_id={test_subscription_id} \
  -H "Authorization: Bearer $FINANCE_TOKEN"

# 4. Verify subscription next_billing_date updated
curl https://api.example.com/api/v1/subscriptions/{test_subscription_id} \
  -H "Authorization: Bearer $SALES_TOKEN"

# 5. Issue invoice
curl -X POST https://api.example.com/api/v1/invoices/{invoice_id}/issue \
  -H "Authorization: Bearer $FINANCE_TOKEN"

# 6. Record payment
curl -X POST https://api.example.com/api/v1/payments \
  -H "Authorization: Bearer $FINANCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "{invoice_id}",
    "amount": 110.00,
    "payment_date": "2026-10-31T12:00:00Z",
    "payment_method": "credit_card"
  }'

# 7. Verify invoice status = paid
curl https://api.example.com/api/v1/invoices/{invoice_id} \
  -H "Authorization: Bearer $FINANCE_TOKEN"
```

**Verify:**
- [ ] Invoice created with correct line items
- [ ] Subscription `next_billing_date` incremented
- [ ] Invoice status transitions: draft → open → paid
- [ ] Payment updates invoice balances correctly
- [ ] Financial summary reflects changes

### 6. Monitor First Scheduled Run

**Wait for first scheduled billing run (typically midnight):**

```bash
# Check billing job history
curl https://api.example.com/api/v1/billing/jobs \
  -H "Authorization: Bearer $FINANCE_TOKEN"

# Review application logs
tail -f logs/subscriptiq.log | grep -i billing
```

**Verify:**
- [ ] Billing job executed at scheduled time
- [ ] Correct number of subscriptions processed
- [ ] Invoices created successfully
- [ ] No errors in job logs
- [ ] `BillingJob` record created with status=completed

### 7. Set Up Monitoring

**Configure alerts for:**
- [ ] Billing job failures
- [ ] Billing job not running for >24 hours
- [ ] High failure rate (>5%)
- [ ] Payment processing errors
- [ ] PDF generation failures

**Monitor metrics:**
- [ ] Billing job execution time
- [ ] Number of invoices created per run
- [ ] Invoice payment rates
- [ ] Outstanding balance trends

---

## Rollback Plan

If issues occur, follow rollback procedure:

### 1. Disable Scheduler (Immediate)
```bash
# On all instances
ENABLE_SCHEDULER=false
systemctl restart subscriptiq
```

### 2. Database Rollback (If necessary)
```bash
# Stop application
systemctl stop subscriptiq

# Restore database backup
pg_restore -d subscriptiq_db backup_YYYYMMDD_HHMMSS.sql

# Rollback migrations
flask db downgrade

# Restart application
systemctl start subscriptiq
```

### 3. Code Rollback
```bash
# Revert to previous version
git checkout <previous_release_tag>

# Reinstall dependencies
pip install -r requirements.txt

# Restart application
systemctl restart subscriptiq
```

---

## Verification Checklist

### Functional Tests
- [ ] Invoice creation works
- [ ] Invoice listing with filters works
- [ ] Invoice status transitions work
- [ ] Payment recording works
- [ ] Payment updates invoice correctly
- [ ] PDF generation works
- [ ] Billing run creates invoices
- [ ] Billing run updates subscriptions
- [ ] Overdue check updates invoice status
- [ ] Financial summary calculates correctly
- [ ] Outstanding balances report works

### Security Tests
- [ ] Unauthorized users cannot access endpoints (403)
- [ ] Customers can only see own invoices
- [ ] Finance role required for payment operations
- [ ] Admin role has full access
- [ ] JWT authentication required

### Performance Tests
- [ ] Billing run completes in acceptable time
- [ ] Invoice queries perform well with pagination
- [ ] PDF generation completes in <5 seconds
- [ ] Database indexes used by queries

### Integration Tests
- [ ] Module 2 subscriptions read correctly
- [ ] Module 2 next_billing_date updated correctly
- [ ] Invoice references subscription correctly
- [ ] Customer data populated in invoices

---

## Documentation

### User Documentation
- [ ] API endpoints documented
- [ ] Request/response examples provided
- [ ] Error codes documented
- [ ] Role permissions documented

### Operations Documentation
- [ ] Deployment procedure documented
- [ ] Scheduler configuration documented
- [ ] Monitoring setup documented
- [ ] Troubleshooting guide provided

### Integration Documentation
- [ ] Module 2 integration documented
- [ ] Module 4 data access documented
- [ ] Database relationships documented

---

## Sign-Off

- [ ] Technical lead approval
- [ ] QA testing completed
- [ ] Security review completed
- [ ] Operations team notified
- [ ] Documentation updated
- [ ] Deployment successful
- [ ] Post-deployment verification completed

**Deployed by:** _______________  
**Date:** _______________  
**Version:** _______________  

---

## Support Contacts

- **Technical Issues:** [email/slack]
- **Database Issues:** [DBA contact]
- **Billing Questions:** [finance team contact]
- **On-Call:** [on-call schedule]

---

## Additional Notes

Record any deployment-specific notes, issues encountered, or deviations from standard procedure:

```
[Add notes here]
```

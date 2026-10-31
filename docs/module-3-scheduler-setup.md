# Scheduler Configuration - Module 3

This document describes how to configure and deploy the scheduler for recurring billing and invoice management tasks.

## Overview

The scheduler uses **APScheduler** to run recurring jobs:
1. **Billing Job** - Processes active subscriptions and generates invoices
2. **Overdue Check Job** - Updates invoice statuses to overdue when past due date

## Environment Variables

### Required Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENABLE_SCHEDULER` | Enable/disable scheduler | `false` | `true` |
| `BILLING_CRON` | Cron expression for billing job | `0 0 * * *` | `0 0 * * *` (midnight daily) |
| `OVERDUE_CHECK_CRON` | Cron expression for overdue check | `0 1 * * *` | `0 1 * * *` (1 AM daily) |

### Cron Expression Format

Format: `minute hour day month day_of_week`

Examples:
- `0 0 * * *` - Every day at midnight
- `0 */6 * * *` - Every 6 hours
- `0 2 * * 1` - Every Monday at 2 AM
- `30 4 1 * *` - 4:30 AM on the 1st of every month

### Example .env Configuration

```bash
# Scheduler Configuration
ENABLE_SCHEDULER=true
BILLING_CRON=0 0 * * *
OVERDUE_CHECK_CRON=0 1 * * *
```

## Production Deployment

### Critical: Single Scheduler Instance

**⚠️ IMPORTANT:** Only **ONE** application instance should run the scheduler in production.

Running multiple schedulers will cause:
- Duplicate invoice generation
- Race conditions
- Database conflicts
- Double-billing customers

### Deployment Strategies

#### Strategy 1: Dedicated Scheduler Instance

Deploy one instance specifically for the scheduler:

**Scheduler Instance:**
```bash
ENABLE_SCHEDULER=true
BILLING_CRON=0 0 * * *
OVERDUE_CHECK_CRON=0 1 * * *
```

**Web/API Instances:**
```bash
ENABLE_SCHEDULER=false
```

#### Strategy 2: Leader Election (Advanced)

For high-availability setups, implement leader election:
- Use Redis or database-based locking
- Only the leader instance runs scheduler
- Automatic failover if leader goes down

#### Strategy 3: External Cron Job

Instead of using the built-in scheduler, use external cron jobs to trigger billing:

```bash
# Run billing via API endpoint
0 0 * * * curl -X POST https://api.example.com/api/v1/billing/run \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Scheduler Jobs

### 1. Billing Job

**Purpose:** Process active subscriptions and generate recurring invoices

**Schedule:** Configurable via `BILLING_CRON` (default: daily at midnight)

**What it does:**
1. Queries subscriptions where `next_billing_date <= current_date`
2. Filters for `status = 'active'`
3. For each subscription:
   - Calculates billing period
   - Checks for existing invoice (idempotent)
   - Creates invoice with line items from plan
   - Updates `subscription.next_billing_date`
4. Creates `BillingJob` record with results

**Manual Trigger:**
```bash
POST /api/v1/billing/run
Authorization: Bearer <admin_token>
```

**Monitoring:**
- Check billing job history: `GET /api/v1/billing/jobs`
- Review error logs in `BillingJob.error_log`
- Monitor application logs for scheduler activity

### 2. Overdue Check Job

**Purpose:** Update invoice statuses to overdue when past due date

**Schedule:** Configurable via `OVERDUE_CHECK_CRON` (default: daily at 1 AM)

**What it does:**
1. Queries invoices where `status IN ('open', 'partially_paid')`
2. Filters where `due_date < current_date`
3. Updates `status = 'overdue'`

**Manual Trigger:**
Called automatically by scheduler; no direct API endpoint

## Verification

### Check Scheduler Status

1. **View Logs:**
```bash
# Look for scheduler initialization messages
tail -f logs/subscriptiq.log | grep -i scheduler
```

Expected output:
```
Scheduler started successfully
Billing job scheduled: 0 0 * * *
Overdue check scheduled: 0 1 * * *
```

2. **Check Billing Job History:**
```bash
GET /api/v1/billing/jobs
```

Should show recent billing jobs with status and results.

3. **Test Manual Billing Run:**
```bash
POST /api/v1/billing/run
Authorization: Bearer <admin_token>
```

Should complete successfully and return job results.

## Troubleshooting

### Scheduler Not Starting

**Problem:** No scheduler logs appear

**Solutions:**
1. Verify `ENABLE_SCHEDULER=true` in environment
2. Check application startup logs for errors
3. Ensure APScheduler is installed: `pip show APScheduler`
4. Check database connectivity (job store uses database)

### Duplicate Invoices

**Problem:** Multiple invoices created for same subscription/period

**Solutions:**
1. **Immediately:** Set `ENABLE_SCHEDULER=false` on all but one instance
2. Check for multiple running instances with scheduler enabled
3. Review billing job history for duplicate runs
4. Database unique constraint should prevent duplicates (verify constraint exists)

### Jobs Not Running

**Problem:** Scheduler starts but jobs don't execute

**Solutions:**
1. Verify cron expressions are valid
2. Check scheduler logs for job execution attempts
3. Ensure timezone is set correctly (UTC)
4. Check for job exceptions in error logs
5. Verify database job store is accessible

### Failed Billing Runs

**Problem:** Billing job completes but has failures

**Solutions:**
1. Check `BillingJob.error_log` for specific errors
2. Common issues:
   - Plan not found → Subscription references deleted plan
   - Customer not found → Data integrity issue
   - Database timeout → Too many subscriptions, consider batching
3. Failed subscriptions are skipped; review and retry manually

## Monitoring Recommendations

### Application Monitoring

1. **Track Billing Job Metrics:**
   - Execution duration
   - Success/failure rate
   - Number of invoices created
   - Number of failures

2. **Set Up Alerts:**
   - Billing job not running for > 24 hours
   - Billing job failure rate > 5%
   - Scheduler not initialized on startup

3. **Database Monitoring:**
   - Monitor `apscheduler_jobs` table
   - Track invoice creation rate
   - Monitor database locks during billing

### Log Monitoring

Key log messages to monitor:

```
INFO: Scheduler started successfully
INFO: Starting scheduled billing job
INFO: Billing job completed: X invoices created from Y subscriptions
WARNING: Billing job had Z failures
ERROR: Billing job failed: <error>
```

## Performance Considerations

### Large-Scale Deployments

If processing thousands of subscriptions:

1. **Batch Processing:**
   - Process subscriptions in batches
   - Add delays between batches to reduce load

2. **Increase Job Timeout:**
   - Configure APScheduler `misfire_grace_time`
   - Default: 300 seconds (5 minutes)

3. **Optimize Queries:**
   - Ensure indexes exist on:
     - `subscription.next_billing_date`
     - `subscription.status`
     - `invoice.billing_period_start/end`

4. **Consider Separate Worker:**
   - Use Celery or similar for async processing
   - Scheduler triggers job, worker processes subscriptions

## Database Requirements

### Job Store

APScheduler stores job state in database:

```sql
CREATE TABLE apscheduler_jobs (
    id VARCHAR(191) PRIMARY KEY,
    next_run_time FLOAT,
    job_state BLOB NOT NULL
);

CREATE INDEX ix_apscheduler_jobs_next_run_time 
ON apscheduler_jobs (next_run_time);
```

This table is created automatically by APScheduler.

### Cleanup

Old job records are automatically cleaned up by APScheduler. No manual maintenance required.

## Migration from Manual Billing

If migrating from manual billing to scheduled billing:

1. **Test in staging first**
2. **Verify all subscriptions have valid `next_billing_date`**
3. **Run manual billing once to confirm** (`POST /billing/run`)
4. **Enable scheduler** (`ENABLE_SCHEDULER=true`)
5. **Monitor first few scheduled runs closely**

## Support

For issues or questions:
- Check application logs: `logs/subscriptiq.log`
- Review billing job history: `/api/v1/billing/jobs`
- Contact system administrator

---

## Quick Reference

### Enable Scheduler
```bash
ENABLE_SCHEDULER=true
```

### Disable Scheduler
```bash
ENABLE_SCHEDULER=false
```

### Change Billing Schedule
```bash
BILLING_CRON=0 2 * * *  # 2 AM daily
```

### Manual Billing Run
```bash
curl -X POST https://api.example.com/api/v1/billing/run \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

### Check Job History
```bash
curl https://api.example.com/api/v1/billing/jobs \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

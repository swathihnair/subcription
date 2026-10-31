"""Scheduler service for recurring jobs"""
import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from flask import Flask

from app.extensions import db
from app.services.billing_engine import BillingEngine
from app.services.invoice_service import InvoiceService


logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled jobs"""
    
    _scheduler = None
    _initialized = False
    
    @staticmethod
    def initialize_scheduler(app: Flask) -> bool:
        """
        Initialize the scheduler.
        
        Only initializes if ENABLE_SCHEDULER environment variable is set to 'true'.
        This ensures only one instance runs the scheduler in production.
        
        Args:
            app: Flask application instance
            
        Returns:
            True if scheduler was initialized, False otherwise
        """
        # Check if scheduler should run
        enable_scheduler = os.getenv('ENABLE_SCHEDULER', 'false').lower() == 'true'
        
        if not enable_scheduler:
            logger.info('Scheduler disabled (ENABLE_SCHEDULER=false)')
            return False
        
        if SchedulerService._initialized:
            logger.warning('Scheduler already initialized')
            return False
        
        try:
            # Configure job store
            jobstores = {
                'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])
            }
            
            # Configure executors
            executors = {
                'default': ThreadPoolExecutor(max_workers=3)
            }
            
            # Job defaults
            job_defaults = {
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance of each job at a time
                'misfire_grace_time': 300  # 5 minutes grace period for missed jobs
            }
            
            # Create scheduler
            SchedulerService._scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )
            
            # Add billing job
            billing_cron = os.getenv('BILLING_CRON', '0 0 * * *')  # Default: midnight daily
            SchedulerService._add_billing_job(billing_cron)
            
            # Add overdue invoice update job
            overdue_cron = os.getenv('OVERDUE_CHECK_CRON', '0 1 * * *')  # Default: 1 AM daily
            SchedulerService._add_overdue_check_job(overdue_cron)
            
            # Start scheduler
            SchedulerService._scheduler.start()
            SchedulerService._initialized = True
            
            logger.info(f'Scheduler started successfully')
            logger.info(f'Billing job scheduled: {billing_cron}')
            logger.info(f'Overdue check scheduled: {overdue_cron}')
            
            return True
            
        except Exception as e:
            logger.error(f'Failed to initialize scheduler: {str(e)}')
            return False
    
    @staticmethod
    def _add_billing_job(cron_expression: str):
        """
        Add scheduled billing job.
        
        Parses cron expression and schedules the job.
        Format: minute hour day month day_of_week
        """
        # Parse cron expression (simple format: minute hour day month day_of_week)
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")
        
        minute, hour, day, month, day_of_week = parts
        
        SchedulerService._scheduler.add_job(
            func=SchedulerService._run_billing_job,
            trigger='cron',
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id='billing_job',
            name='Recurring Billing Job',
            replace_existing=True
        )
    
    @staticmethod
    def _add_overdue_check_job(cron_expression: str):
        """
        Add scheduled overdue invoice check job.
        """
        # Parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")
        
        minute, hour, day, month, day_of_week = parts
        
        SchedulerService._scheduler.add_job(
            func=SchedulerService._run_overdue_check_job,
            trigger='cron',
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id='overdue_check_job',
            name='Overdue Invoice Check Job',
            replace_existing=True
        )
    
    @staticmethod
    def _run_billing_job():
        """
        Execute billing job.
        
        This function is called by the scheduler.
        """
        logger.info('Starting scheduled billing job')
        
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                result = BillingEngine.run_billing()
                logger.info(
                    f'Billing job completed: {result.invoices_created} invoices created '
                    f'from {result.subscriptions_processed} subscriptions'
                )
                
                if result.failures:
                    logger.warning(f'Billing job had {len(result.failures)} failures')
                    for failure in result.failures:
                        logger.error(f'Failed subscription {failure.get("subscription_id")}: {failure.get("error")}')
        
        except Exception as e:
            logger.error(f'Billing job failed: {str(e)}')
            raise
    
    @staticmethod
    def _run_overdue_check_job():
        """
        Execute overdue invoice check job.
        
        This function is called by the scheduler.
        """
        logger.info('Starting overdue invoice check job')
        
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                count = InvoiceService.update_overdue_invoices()
                logger.info(f'Overdue check completed: {count} invoices marked as overdue')
        
        except Exception as e:
            logger.error(f'Overdue check job failed: {str(e)}')
            raise
    
    @staticmethod
    def shutdown():
        """Shutdown the scheduler gracefully"""
        if SchedulerService._scheduler:
            logger.info('Shutting down scheduler')
            SchedulerService._scheduler.shutdown()
            SchedulerService._initialized = False
    
    @staticmethod
    def get_jobs():
        """Get list of scheduled jobs"""
        if SchedulerService._scheduler:
            return SchedulerService._scheduler.get_jobs()
        return []

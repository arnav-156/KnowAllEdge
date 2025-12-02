"""
Data Retention Scheduler
Automatically runs data retention cleanup jobs

Usage:
    # Run once (testing)
    python scheduler.py --once

    # Run as daemon (production)
    python scheduler.py

    # Dry run (see what would be deleted)
    python scheduler.py --dry-run
"""

import argparse
import time
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from data_retention import cleanup_expired_data, get_retention_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_retention.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_cleanup_job(dry_run=False):
    """Run data retention cleanup for all categories"""
    logger.info("=" * 70)
    logger.info(f"Starting data retention cleanup (dry_run={dry_run})")
    logger.info("=" * 70)
    
    try:
        # Run cleanup for all categories
        results = cleanup_expired_data(dry_run=dry_run)
        
        # Log results
        total_deleted = 0
        total_anonymized = 0
        
        for category, result in results.items():
            status = result.get('status')
            deleted = result.get('deleted', 0)
            anonymized = result.get('anonymized', 0)
            
            total_deleted += deleted
            total_anonymized += anonymized
            
            if status == 'success':
                logger.info(f"✅ {category}: deleted={deleted}, anonymized={anonymized}")
            elif status == 'dry_run':
                would_delete = result.get('would_delete', 0)
                logger.info(f"🔍 {category}: would delete {would_delete} records")
            else:
                logger.warning(f"⚠️ {category}: {status}")
        
        if not dry_run:
            logger.info(f"✅ Cleanup complete: {total_deleted} deleted, {total_anonymized} anonymized")
        else:
            logger.info(f"🔍 Dry run complete")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}", exc_info=True)
    
    logger.info("=" * 70)


def print_retention_policy():
    """Print current retention policy"""
    print("\n" + get_retention_report())


def main():
    parser = argparse.ArgumentParser(description='Data Retention Scheduler')
    parser.add_argument('--once', action='store_true', help='Run cleanup once and exit')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no actual deletion)')
    parser.add_argument('--show-policy', action='store_true', help='Show retention policy and exit')
    args = parser.parse_args()
    
    # Show policy and exit
    if args.show_policy:
        print_retention_policy()
        return
    
    # Run once and exit
    if args.once:
        logger.info("Running cleanup once...")
        run_cleanup_job(dry_run=args.dry_run)
        logger.info("✅ Cleanup complete. Exiting.")
        return
    
    # Run as scheduled daemon
    logger.info("Starting data retention scheduler...")
    logger.info("Cleanup will run daily at 2:00 AM UTC")
    logger.info("Press Ctrl+C to stop")
    
    scheduler = BlockingScheduler()
    
    # Schedule cleanup job for 2 AM daily
    scheduler.add_job(
        func=lambda: run_cleanup_job(dry_run=args.dry_run),
        trigger=CronTrigger(hour=2, minute=0),
        id='data_retention_cleanup',
        name='Data Retention Cleanup',
        replace_existing=True
    )
    
    # Also run immediately on startup
    logger.info("Running initial cleanup...")
    run_cleanup_job(dry_run=args.dry_run)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()


if __name__ == "__main__":
    main()

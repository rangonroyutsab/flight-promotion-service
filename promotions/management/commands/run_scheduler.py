"""
Django management command that starts a blocking APScheduler process.

This replaces the old cron-based scheduler (docker/scheduler/crontab).
APScheduler runs in-process, inherits all Django settings and environment
variables natively, and does not require root privileges.
"""
import logging

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs the APScheduler blocking scheduler for background promotion jobs."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)

        def generate_promotions_job():
            logger.info("APScheduler: triggering generate_flight_promotions job...")
            call_command("generate_flight_promotions", scheduled=True)

        # Equivalent to cron "0 0 * * *" — runs daily at midnight in settings.TIME_ZONE
        scheduler.add_job(
            generate_promotions_job,
            trigger=CronTrigger(hour=0, minute=0),
            id="generate_promotions",
            max_instances=1,
            replace_existing=True,
        )

        logger.info(
            "APScheduler started. Daily job scheduled at midnight (%s).",
            settings.TIME_ZONE,
        )
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("APScheduler stopping gracefully.")
            scheduler.shutdown()
            raise

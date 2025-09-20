from flask_mail import Message
from datetime import datetime
from flask import current_app
from typing import Optional

from utils.extensions import mail   # direct import (no circular issue here)
from models.user import User        # direct import avoids undefined name
from utils.report_utils import generate_excel


def monthly_report_job(single_user: Optional[User] = None) -> None:
    """
    Send monthly Excel expense reports via email.
    """
    current_app.logger.info("📅 Running monthly report job...")

    users = [single_user] if single_user else User.query.all()
    for user in users:
        try:
            excel_file = generate_excel(user.expenses)

            msg = Message(
                subject=f"Monthly Report - {datetime.now().strftime('%B %Y')}",
                sender="noreply@budgettracker.com",
                recipients=[user.email],
            )
            msg.body = f"Hello {user.email},\n\nPlease find attached your monthly expense report."
            msg.attach(
                "report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                excel_file.getvalue(),
            )

            with current_app.app_context():
                mail.send(msg)

            current_app.logger.info("✅ Report sent to %s", user.email)
        except Exception as e:
            current_app.logger.error("❌ Failed to send report to %s: %s", user.email, e)

    current_app.logger.info("📅 Monthly report job completed.")


def sample_job() -> None:
    """Simple test job for debugging."""
    current_app.logger.info("✅ Scheduler sample job executed.")


def register_jobs(scheduler) -> None:
    """Register scheduled jobs."""
    scheduler.add_job(
        id="sample_job",
        func=sample_job,
        trigger="interval",
        seconds=10,
        replace_existing=True,
    )

    scheduler.add_job(
        id="monthly_report",
        func=monthly_report_job,
        trigger="cron",
        day=1,
        hour=8,
        minute=0,
        replace_existing=True,
    )
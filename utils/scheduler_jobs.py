from flask_mail import Message
from datetime import datetime
from typing import Optional

from models.user import User
from utils.report_utils import generate_report  # ✅ ensures report generation


# ---------------- JOBS ---------------- #
def monthly_report_job(app, single_user: Optional[User] = None) -> None:
    """
    Send monthly expense reports via email (CSV by default).
    Runs on the 1st day of each month at 8 AM (server time).
    """
    with app.app_context():
        app.logger.info("📅 Running monthly report job...")

        # Get users (all or single)
        users = [single_user] if single_user else User.query.all()

        for user in users:
            try:
                # ✅ Generate CSV report
                response = generate_report(user.id, format="csv")
                if not response:
                    app.logger.warning("⚠️ No expenses found for %s", user.email)
                    continue

                # Extract CSV bytes from Flask response
                report_data = (
                    response.response[0]
                    if isinstance(response.response, list)
                    else response.response
                )

                from utils.extensions import mail  # lazy import avoids circular deps

                msg = Message(
                    subject=f"Monthly Report - {datetime.now().strftime('%B %Y')}",
                    sender="noreply@budgettracker.com",
                    recipients=[user.email],
                )
                msg.body = (
                    f"Hello {user.email},\n\n"
                    f"Please find attached your monthly expense report.\n\n"
                    f"- Budget Tracker Team"
                )
                msg.attach(
                    "expense_report.csv",
                    "text/csv",
                    report_data,
                )

                mail.send(msg)
                app.logger.info("✅ Report sent to %s", user.email)

            except Exception as e:
                app.logger.error("❌ Failed to send report to %s: %s", user.email, e)

        app.logger.info("📅 Monthly report job completed.")


def sample_job(app) -> None:
    """Simple test job for debugging."""
    with app.app_context():
        app.logger.info("🔄 Scheduler sample job executed.")


# ---------------- JOB REGISTRATION ---------------- #
def register_jobs(scheduler, app) -> None:
    """
    Register scheduled jobs with Flask app context.
    """
    # Debug sample job (every 10 seconds)
    scheduler.add_job(
        id="sample_job",
        func=sample_job,
        trigger="interval",
        seconds=10,
        replace_existing=True,
        args=[app],  # ✅ pass app context
    )

    # Monthly report job (1st of every month, 08:00 server time)
    scheduler.add_job(
        id="monthly_report",
        func=monthly_report_job,
        trigger="cron",
        day=1,
        hour=8,
        minute=0,
        replace_existing=True,
        args=[app],  # ✅ pass app context
    )
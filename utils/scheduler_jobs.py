from flask_mail import Message
from datetime import datetime


def monthly_report_job(single_user=None):
    from utils.extensions import mail   # lazy import to avoid circular import
    from models import User             # safe, thanks to __init__.py
    from utils.report_utils import generate_excel

    print("📅 Running monthly report job...")

    users = [single_user] if single_user else User.query.all()
    for user in users:
        try:
            # Generate report
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

            mail.send(msg)
            print(f"✅ Report sent to {user.email}")
        except Exception as e:
            print(f"❌ Failed to send report to {user.email}: {e}")
    print("📅 Monthly report job completed.")


def sample_job():
    print("✅ Scheduler job is running!")


def register_jobs(scheduler):
    # Debug/test job every 10s
    scheduler.add_job(
        id="sample_job",
        func=sample_job,
        trigger="interval",
        seconds=10
    )

    # Monthly report job (runs at 1st day of every month, 8:00 AM)
    scheduler.add_job(
        id="monthly_report",
        func=monthly_report_job,
        trigger="cron",
        day=1,
        hour=8,
        minute=0
    )
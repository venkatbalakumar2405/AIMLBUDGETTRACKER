from flask_mail import Message
from datetime import datetime

def monthly_report_job(single_user=None):
    from utils.extensions import mail   # lazy import to avoid circular
    from models import User                 # safe, thanks to __init__.py
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
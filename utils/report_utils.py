import io
import pandas as pd
from flask import send_file
from utils.extensions import db
from models.expense import Expense


def generate_report(user_id, format="csv"):
    """
    Generate a report of expenses for a given user.
    Supports CSV or JSON formats.
    """

    # Fetch expenses from DB
    expenses = (
        db.session.query(Expense)
        .filter(Expense.user_id == user_id)
        .order_by(Expense.expense_date.desc())
        .all()
    )

    # Convert to DataFrame
    data = [
        {
            "date": e.expense_date.strftime("%Y-%m-%d"),
            "amount": float(e.amount),
            "category": e.category,
            "description": e.description or "",
        }
        for e in expenses
    ]
    df = pd.DataFrame(data)

    if df.empty:
        return None, "No expenses found for this user."

    # ✅ Export as CSV
    if format == "csv":
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return send_file(
            io.BytesIO(buffer.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="expense_report.csv",
        )

    # ✅ Export as JSON
    elif format == "json":
        buffer = io.StringIO()
        df.to_json(buffer, orient="records", indent=2)
        buffer.seek(0)
        return send_file(
            io.BytesIO(buffer.getvalue().encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name="expense_report.json",
        )

    else:
        return None, f"Unsupported format: {format}"
from flask import Blueprint, request, jsonify, send_file
from utils.extensions import db
from models.user import User
from models.expense import Expense
import io
import csv
from reportlab.pdfgen import canvas
import pandas as pd
from datetime import datetime

budget_bp = Blueprint("budget", __name__)

# ✅ Helper function
def get_user_by_email(email):
    if not email:
        return None, jsonify({"error": "Email is required"}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return None, jsonify({"error": "User not found"}), 404
    return user, None, None


# ✅ Get all expenses
@budget_bp.route("/expenses", methods=["GET"])
def get_expenses():
    email = request.args.get("email")
    user, err, code = get_user_by_email(email)
    if err:
        return err, code

    expenses = Expense.query.filter_by(user_id=user.id).all()
    return jsonify({
        "expenses": [
            {
                "id": e.id,
                "amount": e.amount,
                "description": e.description,
                "date": e.date.strftime("%Y-%m-%d") if e.date else None
            }
            for e in expenses
        ]
    })


# ✅ Add expense
@budget_bp.route("/add", methods=["POST"])
def add_expense():
    try:
        data = request.get_json()
        email = data.get("email")
        description = data.get("description")
        amount = data.get("amount")
        date_str = data.get("date")

        user, err, code = get_user_by_email(email)
        if err:
            return err, code

        # Amount validation
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return jsonify({"error": "Amount must be a number"}), 400

        # Date validation
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            date = datetime.utcnow()

        expense = Expense(description=description, amount=amount, date=date, user_id=user.id)
        db.session.add(expense)
        db.session.commit()

        return jsonify({"message": "Expense added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/add:", str(e))
        return jsonify({"error": "Server error while adding expense", "details": str(e)}), 500


# ✅ Update expense
@budget_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):
    data = request.get_json()
    expense = Expense.query.get(id)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    if "description" in data:
        expense.description = data["description"]

    if "amount" in data:
        try:
            expense.amount = float(data["amount"])
        except ValueError:
            return jsonify({"error": "Amount must be a number"}), 400

    if "date" in data:
        try:
            expense.date = datetime.strptime(data["date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    db.session.commit()
    return jsonify({"message": "Expense updated successfully"})


# ✅ Delete expense
@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):
    expense = Expense.query.get(id)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted successfully"})


# ✅ Update salary
@budget_bp.route("/salary", methods=["PUT"])
def update_salary():
    data = request.get_json()
    email = data.get("email")
    salary = data.get("salary")

    user, err, code = get_user_by_email(email)
    if err:
        return err, code

    try:
        user.salary = float(salary)
    except (TypeError, ValueError):
        return jsonify({"error": "Salary must be a number"}), 400

    db.session.commit()
    return jsonify({"message": "Salary updated successfully"})


# ✅ Reset salary & expenses
@budget_bp.route("/reset", methods=["POST"])
def reset_all():
    data = request.get_json()
    email = data.get("email")

    user, err, code = get_user_by_email(email)
    if err:
        return err, code

    user.salary = 0
    Expense.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({"message": "All data reset successfully"})


# ✅ Download reports
@budget_bp.route("/download-expenses-<format>", methods=["GET"])
def download_report(format):
    email = request.args.get("email")
    user, err, code = get_user_by_email(email)
    if err:
        return err, code

    expenses = Expense.query.filter_by(user_id=user.id).all()
    data = [
        {
            "Description": e.description,
            "Amount": e.amount,
            "Date": e.date.strftime("%Y-%m-%d") if e.date else ""
        }
        for e in expenses
    ]

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["Description", "Amount", "Date"])
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()),
                         mimetype="text/csv",
                         download_name="expenses.csv",
                         as_attachment=True)

    elif format == "excel":
        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return send_file(output,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         download_name="expenses.xlsx",
                         as_attachment=True)

    elif format == "pdf":
        output = io.BytesIO()
        p = canvas.Canvas(output)
        p.drawString(100, 800, f"Expenses Report for {email}")
        y = 750
        for e in data:
            p.drawString(100, y, f"{e['Date']} | {e['Description']} - ₹{e['Amount']}")
            y -= 20
        p.save()
        output.seek(0)
        return send_file(output,
                         mimetype="application/pdf",
                         download_name="expenses.pdf",
                         as_attachment=True)

    return jsonify({"error": "Invalid format"}), 400
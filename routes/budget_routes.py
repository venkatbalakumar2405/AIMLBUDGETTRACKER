from flask import Blueprint, request, jsonify, send_file
from utils.extensions import db
from models.user import User
from models.expense import Expense
import io
import csv
import pandas as pd
from reportlab.pdfgen import canvas

budget_bp = Blueprint("budget", __name__)

# ============================
# Get all expenses
# ============================
@budget_bp.route("/expenses", methods=["GET"])
def get_expenses():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()
    return jsonify({"expenses": [
        {"id": e.id, "amount": e.amount, "description": e.description}
        for e in expenses
    ]})


# ============================
# Add a new expense
# ============================
@budget_bp.route("/add", methods=["POST"])
def add_expense():
    data = request.get_json()
    email = data.get("email")
    description = data.get("description")
    amount = data.get("amount")

    if not email or not description or amount is None:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expense = Expense(description=description, amount=amount, user_id=user.id)
    db.session.add(expense)
    db.session.commit()

    return jsonify({"message": "Expense added successfully"}), 201


# ============================
# Update an expense
# ============================
@budget_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):
    data = request.get_json()
    expense = Expense.query.get(id)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    expense.description = data.get("description", expense.description)
    expense.amount = data.get("amount", expense.amount)
    db.session.commit()

    return jsonify({"message": "Expense updated successfully"})


# ============================
# Delete an expense
# ============================
@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):
    expense = Expense.query.get(id)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted successfully"})


# ============================
# Update salary
# ============================
@budget_bp.route("/salary", methods=["PUT"])
def update_salary():
    data = request.get_json()
    email = data.get("email")
    salary = data.get("salary")

    if email is None or salary is None:
        return jsonify({"error": "Missing email or salary"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.salary = salary
    db.session.commit()
    return jsonify({"message": "Salary updated successfully"})


# ============================
# Reset salary & expenses
# ============================
@budget_bp.route("/reset", methods=["POST"])
def reset_all():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.salary = 0
    Expense.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({"message": "All data reset successfully"})


# ============================
# Download reports
# ============================
@budget_bp.route("/download-expenses-<format>", methods=["GET"])
def download_report(format):
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()
    data = [{"Description": e.description, "Amount": e.amount} for e in expenses]

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["Description", "Amount"])
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
            p.drawString(100, y, f"{e['Description']} - ₹{e['Amount']}")
            y -= 20
        p.save()
        output.seek(0)
        return send_file(output,
                         mimetype="application/pdf",
                         download_name="expenses.pdf",
                         as_attachment=True)

    return jsonify({"error": "Invalid format"}), 400
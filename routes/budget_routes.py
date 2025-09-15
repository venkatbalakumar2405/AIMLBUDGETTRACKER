from flask import Blueprint, request, jsonify, send_file
from utils.extensions import db
from models.user import User
from models.expense import Expense
from sqlalchemy import extract, func
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

budget_bp = Blueprint("budget", __name__)

# ✅ Health check
@budget_bp.route("/", methods=["GET"])
def budget_home():
    return jsonify({"message": "Budget API is working!"})


# ✅ Add expense
@budget_bp.route("/add", methods=["POST"])
def add_expense():
    data = request.get_json()
    email = data.get("email")
    amount = data.get("amount")
    description = data.get("description")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expense = Expense(amount=amount, description=description, user_id=user.id)
    db.session.add(expense)
    db.session.commit()

    return jsonify({"message": "Expense added successfully"}), 201


# ✅ Get all expenses
@budget_bp.route("/all/<email>", methods=["GET"])
def get_expenses(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()
    return jsonify([
        {"id": e.id, "amount": e.amount, "description": e.description, "created_at": e.created_at}
        for e in expenses
    ])


# ✅ Update expense
@budget_bp.route("/update/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json()
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    expense.amount = data.get("amount", expense.amount)
    expense.description = data.get("description", expense.description)
    db.session.commit()

    return jsonify({"message": "Expense updated successfully"})


# ✅ Delete expense
@budget_bp.route("/delete/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
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

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.salary = salary
    db.session.commit()

    return jsonify({"message": "Salary updated successfully"})


# ✅ Reset all data
@budget_bp.route("/reset", methods=["POST"])
def reset_data():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.salary = 0
    Expense.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({"message": "All data reset successfully"})


# ✅ Monthly expenses aggregation
@budget_bp.route("/monthly-expenses", methods=["GET"])
def monthly_expenses():
    email = request.args.get("email")  
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    results = (
        db.session.query(
            extract("year", Expense.created_at).label("year"),
            extract("month", Expense.created_at).label("month"),
            func.sum(Expense.amount).label("total"),
        )
        .filter_by(user_id=user.id)
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    return jsonify([
        {"year": int(r.year), "month": int(r.month), "total": float(r.total)}
        for r in results
    ])


# 📂 Export CSV
@budget_bp.route("/download-expenses-csv", methods=["GET"])
def download_csv():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()
    data = [{"Amount": e.amount, "Description": e.description} for e in expenses]

    df = pd.DataFrame(data)
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="expenses.csv", mimetype="text/csv")


# 📊 Export Excel
@budget_bp.route("/download-expenses-excel", methods=["GET"])
def download_excel():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()
    data = [{"Amount": e.amount, "Description": e.description} for e in expenses]

    df = pd.DataFrame(data)
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="expenses.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# 📕 Export PDF
@budget_bp.route("/download-expenses-pdf", methods=["GET"])
def download_pdf():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    expenses = Expense.query.filter_by(user_id=user.id).all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.drawString(200, height - 40, "Expense Report")
    y = height - 80

    for e in expenses:
        p.drawString(50, y, f"₹{e.amount} - {e.description}")
        y -= 20

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="expenses.pdf", mimetype="application/pdf")
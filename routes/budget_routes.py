from flask import Blueprint, request, jsonify, Response, send_file
from models.user import User
from models.expense import Expense
from utils.extensions import db
from datetime import datetime
import io
import csv
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

budget_bp = Blueprint("budget", __name__)

# ================== Helpers ==================

def clean_amount(value):
    """Convert input (string/number) to float safely (removes ₹, commas)."""
    if value is None:
        return None
    try:
        return float(str(value).replace("₹", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def parse_date(date_str):
    """Parse date string into datetime.date or return None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def get_user(email):
    """Fetch user by email."""
    return User.query.filter_by(email=email).first()


def calculate_budget_usage(user, expenses=None):
    """Return total_expenses, usage_percent, warning."""
    if expenses is None:
        expenses = user.expenses
    total_expenses = sum((e.amount or 0) for e in expenses)
    budget_limit = user.budget_limit or 0
    usage_percent = (total_expenses / budget_limit * 100) if budget_limit > 0 else None
    warning = None
    if budget_limit > 0 and total_expenses > budget_limit:
        warning = "⚠️ You have exceeded your budget limit!"
    return float(total_expenses), round(usage_percent, 2) if usage_percent else None, warning


def build_summary(user, expenses=None):
    """Return dict with salary, budget, expenses, savings, usage_percent, category_summary."""
    if expenses is None:
        expenses = user.expenses or []
    total_expenses = sum((e.amount or 0) for e in expenses)
    salary = float(user.salary or 0)
    budget_limit = float(user.budget_limit or 0)
    savings = salary - total_expenses if salary > 0 else 0
    usage_percent = (total_expenses / budget_limit * 100) if budget_limit > 0 else None

    category_summary = {}
    for e in expenses:
        cat = e.category or "Miscellaneous"
        category_summary[cat] = category_summary.get(cat, 0) + float(e.amount)

    return {
        "salary": salary,
        "budget_limit": budget_limit,
        "total_expenses": float(total_expenses),
        "savings": float(savings),
        "usage_percent": round(usage_percent, 2) if usage_percent else None,
        "category_summary": category_summary,
    }

# ================== Expenses ==================

@budget_bp.route("/expenses", methods=["GET"])
def get_expenses():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400
        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date.desc()).all()
        expense_list = [
            {
                "id": e.id,
                "description": e.description,
                "amount": float(e.amount),
                "date": e.date.strftime("%Y-%m-%d"),
                "category": e.category or "Miscellaneous",
            }
            for e in expenses
        ]

        return jsonify({"data": expense_list, "summary": build_summary(user, expenses)}), 200
    except Exception as e:
        print("❌ Error in /budget/expenses:", str(e))
        return jsonify({"error": "Server error while fetching expenses"}), 500


@budget_bp.route("/add", methods=["POST"])
def add_expense():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        description = data.get("description", "")
        amount = clean_amount(data.get("amount"))
        category = data.get("category", "Miscellaneous")
        date_obj = parse_date(data.get("date")) or datetime.utcnow().date()

        if not email or amount is None:
            return jsonify({"error": "Email and valid amount are required"}), 400

        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        new_expense = Expense(
            user_id=user.id,
            description=description,
            amount=amount,
            date=date_obj,
            category=category
        )
        db.session.add(new_expense)
        db.session.commit()

        return jsonify({"message": "Expense added successfully", "summary": build_summary(user)}), 201
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/add:", str(e))
        return jsonify({"error": "Server error while adding expense"}), 500


@budget_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):
    try:
        data = request.get_json() or {}
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        if "description" in data:
            expense.description = data["description"]
        if "amount" in data:
            new_amount = clean_amount(data["amount"])
            if new_amount is None:
                return jsonify({"error": "Amount must be valid"}), 400
            expense.amount = new_amount
        if "category" in data:
            expense.category = data["category"]
        if "date" in data:
            new_date = parse_date(data["date"])
            if new_date is None:
                return jsonify({"error": "Invalid date format"}), 400
            expense.date = new_date

        db.session.commit()
        return jsonify({"message": "Expense updated successfully", "summary": build_summary(expense.user)}), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/update:", str(e))
        return jsonify({"error": "Server error while updating expense"}), 500


@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):
    try:
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({"error": "Expense not found"}), 404
        user = expense.user
        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully", "summary": build_summary(user)}), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/delete:", str(e))
        return jsonify({"error": "Server error while deleting expense"}), 500

# ================== Budget & Salary ==================

@budget_bp.route("/set-budget", methods=["PUT"])
def set_budget():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        budget_limit = clean_amount(data.get("budget_limit"))
        if not email or budget_limit is None:
            return jsonify({"error": "Email and valid budget_limit are required"}), 400
        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.budget_limit = budget_limit
        db.session.commit()
        return jsonify({"message": "Budget limit updated", "summary": build_summary(user)}), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/set-budget:", str(e))
        return jsonify({"error": "Server error while setting budget"}), 500


@budget_bp.route("/salary", methods=["GET", "PUT"])
def salary():
    try:
        if request.method == "GET":
            email = request.args.get("email")
            if not email:
                return jsonify({"error": "Email is required"}), 400
            user = get_user(email)
            if not user:
                return jsonify({"error": "User not found"}), 404
            return jsonify({"salary": float(user.salary or 0), "summary": build_summary(user)}), 200

        # PUT
        data = request.get_json() or {}
        email = data.get("email")
        new_salary = clean_amount(data.get("salary"))
        if not email or new_salary is None:
            return jsonify({"error": "Email and valid salary required"}), 400
        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.salary = new_salary
        db.session.commit()
        return jsonify({"message": "Salary updated", "summary": build_summary(user)}), 200
    except Exception as e:
        db.session.rollback()
        print("❌ Error in /budget/salary:", str(e))
        return jsonify({"error": "Server error while handling salary"}), 500

# ================== Trends ==================

@budget_bp.route("/trends", methods=["GET"])
def get_trends():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400
        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404
        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date).all()
        expense_list = [
            {"date": e.date.strftime("%Y-%m-%d"), "amount": float(e.amount), "category": e.category}
            for e in expenses
        ]
        return jsonify({"summary": build_summary(user, expenses), "expenses": expense_list}), 200
    except Exception as e:
        print("❌ Error in /budget/trends:", str(e))
        return jsonify({"error": "Server error while fetching trends"}), 500

# ================== Export ==================

@budget_bp.route("/export/csv", methods=["GET"])
def export_csv():
    try:
        email = request.args.get("email")
        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404
        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Description", "Category", "Amount"])
        for e in expenses:
            writer.writerow([e.date.strftime("%Y-%m-%d"), e.description, e.category, float(e.amount)])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=expenses.csv"}
        )
    except Exception as e:
        print("❌ Error exporting CSV:", str(e))
        return jsonify({"error": "CSV export failed"}), 500


@budget_bp.route("/export/excel", methods=["GET"])
def export_excel():
    try:
        email = request.args.get("email")
        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404
        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date).all()

        output = io.BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Date", "Description", "Category", "Amount"])
        for e in expenses:
            ws.append([e.date.strftime("%Y-%m-%d"), e.description, e.category, float(e.amount)])
        wb.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="expenses.xlsx")
    except Exception as e:
        print("❌ Error exporting Excel:", str(e))
        return jsonify({"error": "Excel export failed"}), 500


@budget_bp.route("/export/pdf", methods=["GET"])
def export_pdf():
    try:
        email = request.args.get("email")
        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404
        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date).all()

        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=letter)
        y = 750
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Expenses Report")
        y -= 30
        p.setFont("Helvetica", 10)
        for e in expenses:
            p.drawString(50, y, f"{e.date.strftime('%Y-%m-%d')} - {e.description} - {e.category} - {float(e.amount)}")
            y -= 15
            if y < 50:
                p.showPage()
                y = 750
        p.save()
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="expenses.pdf")
    except Exception as e:
        print("❌ Error exporting PDF:", str(e))
        return jsonify({"error": "PDF export failed"}), 500
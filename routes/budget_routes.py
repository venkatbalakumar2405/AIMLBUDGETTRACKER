import io
from flask import Blueprint, request, jsonify, send_file, current_app
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Safe headless plotting
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datetime import datetime
from models.user import User
from models.expense import Expense
from utils.extensions import db
from routes.helpers import get_user, build_summary

# CORS just for this blueprint
from flask_cors import CORS

budget_bp = Blueprint("budget", __name__)
CORS(budget_bp, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


# ================== Helpers ==================

def clean_amount(value):
    """Convert input to float safely (removes ₹, commas)."""
    if value is None:
        return None
    try:
        return float(str(value).replace("₹", "").replace(",", "").strip())
    except ValueError:
        return None


def parse_date(date_str):
    """Parse date string into datetime (YYYY-MM-DD) or default to now."""
    if not date_str:
        return datetime.utcnow()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def calculate_budget_usage(user):
    """Return total expenses, budget usage percentage, and warning if exceeded."""
    total_expenses = (
        db.session.query(db.func.sum(Expense.amount))
        .filter_by(user_id=user.id)
        .scalar()
        or 0
    )
    budget_limit = user.budget_limit or 0
    usage_percent = (total_expenses / budget_limit * 100) if budget_limit > 0 else None
    warning = None
    if budget_limit > 0 and total_expenses > budget_limit:
        warning = "⚠️ You have exceeded your budget limit!"
    return float(total_expenses), round(usage_percent, 2) if usage_percent else None, warning


# ================== Expenses ==================

@budget_bp.route("/expenses", methods=["GET"])
def get_expenses():
    """Fetch all expenses for a user by email."""
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = (
            Expense.query.filter_by(user_id=user.id)
            .order_by(Expense.date.desc())
            .all()
        )

        expense_list = [
            {
                "id": e.id,
                "description": e.description,
                "amount": float(e.amount),
                "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                "category": e.category or "Miscellaneous",
            }
            for e in expenses
        ]

        return jsonify({"data": expense_list}), 200
    except Exception as e:
        current_app.logger.exception("❌ Error in /budget/expenses: %s", e)
        return jsonify({"error": "Server error while fetching expenses"}), 500


@budget_bp.route("/add", methods=["POST"])
def add_expense():
    """Update salary for a user (existing design kept for FE compatibility)."""
    try:
        data = request.get_json() or {}
        email = data.get("email")
        salary = data.get("salary")

        if not email or salary is None:
            return jsonify({"error": "Email and salary are required"}), 400

        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.salary = float(salary)
        db.session.commit()

        return jsonify({"message": "Salary updated", "salary": user.salary}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("❌ Error in /budget/add: %s", e)
        return jsonify({"error": "Server error while adding expense"}), 500


@budget_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):
    """Update a single expense by ID."""
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
                return jsonify({"error": "Amount must be a valid number"}), 400
            expense.amount = new_amount
        if "category" in data:
            expense.category = data["category"]

        db.session.commit()
        return jsonify({"message": "Expense updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("❌ Error in /budget/update: %s", e)
        return jsonify({"error": "Server error while updating expense"}), 500


@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):
    """Delete an expense by ID."""
    try:
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("❌ Error in /budget/delete: %s", e)
        return jsonify({"error": "Server error while deleting expense"}), 500


# ================== Budget Settings ==================

@budget_bp.route("/set-budget", methods=["PUT"])
def set_budget():
    """Set or update a user's budget limit."""
    try:
        data = request.get_json() or {}
        email = data.get("email")
        budget = data.get("budget")

        if not email or budget is None:
            return jsonify({"error": "Email and budget are required"}), 400

        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.budget_limit = float(budget)
        db.session.commit()

        return jsonify({
            "message": "Budget limit updated successfully",
            "budget_limit": user.budget_limit,
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("❌ Failed to update budget: %s", e)
        return jsonify({"error": "Failed to update budget", "details": str(e)}), 500


# ================== Trends (PDF Report) ==================

@budget_bp.route("/trends", methods=["GET"])
def get_trends():
    """Generate a PDF report of expenses with charts."""
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = (
            Expense.query.filter_by(user_id=user.id)
            .order_by(Expense.date)
            .all()
        )
        summary = build_summary(user, expenses)

        # === Create PDF ===
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=letter)
        width, height = letter
        y = height - 60

        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width / 2, y, "Expenses Report")
        y -= 40

        # Budget Summary
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Budget Summary")
        y -= 20
        p.setFont("Helvetica", 10)

        fields = [
            ("salary", "Salary"),
            ("budget_limit", "Budget Limit"),
            ("total_expenses", "Total Expenses"),
            ("savings", "Savings"),
            ("usage_percent", "Usage (%)"),
        ]
        for field, label in fields:
            val = summary.get(field, 0)
            display = f"₹{val:,.2f}" if isinstance(val, (int, float)) else str(val)
            p.drawString(50, y, f"{label}: {display}")
            y -= 15
        y -= 10

        # Category Breakdown
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Category Breakdown")
        y -= 20
        p.setFont("Helvetica", 10)

        cat_summary = summary.get("category_summary", {}) or {}
        for cat, amt in sorted(cat_summary.items(), key=lambda x: -float(x[1] or 0)):
            p.drawString(50, y, f"{cat}: ₹{float(amt or 0):,.2f}")
            y -= 15
            if y < 220:
                p.showPage()
                y = height - 60
        y -= 10

        # Pie Chart
        if cat_summary:
            try:
                sizes = [float(v or 0) for v in cat_summary.values()]
                if sum(sizes) > 0:
                    fig, ax = plt.subplots()
                    ax.pie(sizes, labels=cat_summary.keys(), autopct="%1.1f%%", startangle=90)
                    ax.set_title("Expenses by Category")
                    fig.tight_layout()

                    pie_img = io.BytesIO()
                    plt.savefig(pie_img, format="PNG", bbox_inches="tight")
                    plt.close(fig)
                    pie_img.seek(0)

                    if y < 300:
                        p.showPage()
                        y = height - 60

                    p.drawImage(ImageReader(pie_img), (width-400)/2, y-250, 400, 250)
                    y -= 260
            except Exception as e:
                current_app.logger.exception("❌ Pie chart generation failed: %s", e)

        # Line Chart
        if expenses:
            try:
                dates, amounts = [], []
                for exp in expenses:
                    d = getattr(exp, "date", None)
                    if isinstance(d, str):
                        try:
                            d = datetime.fromisoformat(d)
                        except Exception:
                            d = None
                    dates.append(d)
                    amounts.append(float(getattr(exp, "amount", 0) or 0))

                cum, total = [], 0.0
                for amt in amounts:
                    total += amt
                    cum.append(total)

                if cum:
                    fig, ax = plt.subplots()
                    if any(d is None for d in dates):
                        ax.plot(range(len(cum)), cum, marker="o", linestyle="-")
                        ax.set_xlabel("Expense Index")
                    else:
                        ax.plot(dates, cum, marker="o", linestyle="-")
                        ax.set_xlabel("Date")
                        fig.autofmt_xdate()

                    ax.set_ylabel("Cumulative Expenses (₹)")
                    ax.set_title("Expense Trends Over Time")
                    fig.tight_layout()

                    line_img = io.BytesIO()
                    plt.savefig(line_img, format="PNG", bbox_inches="tight")
                    plt.close(fig)
                    line_img.seek(0)

                    if y < 300:
                        p.showPage()
                        y = height - 60

                    p.drawImage(ImageReader(line_img), (width-400)/2, y-250, 400, 250)
                    y -= 260
            except Exception as e:
                current_app.logger.exception("❌ Line chart generation failed: %s", e)

        # Expense Details
        p.showPage()
        y = height - 60
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Expense Details")
        y -= 20
        p.setFont("Helvetica", 10)

        for exp in expenses:
            d = getattr(exp, "date", None)
            if isinstance(d, datetime):
                date_str = d.strftime("%Y-%m-%d")
            else:
                date_str = str(d) if d else "Unknown Date"
            desc = getattr(exp, "description", getattr(exp, "name", "")) or ""
            cat = getattr(exp, "category", "") or ""
            amt = float(getattr(exp, "amount", 0) or 0)

            p.drawString(50, y, f"{date_str} - {desc} - {cat} - ₹{amt:,.2f}")
            y -= 15
            if y < 50:
                p.showPage()
                y = height - 60

        # Finalize PDF
        p.save()
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="expenses.pdf", mimetype="application/pdf")

    except Exception as e:
        current_app.logger.exception("❌ Error in /budget/trends: %s", e)
        return jsonify({"error": "Server error while fetching trends"}), 500
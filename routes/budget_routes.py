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
from models.expense import Expense
from routes.helpers import get_user, build_summary

# CORS just for this blueprint
from flask_cors import CORS

budget_bp = Blueprint("budget", __name__)
CORS(
    budget_bp,
    resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
    supports_credentials=True,
)


# =========================
# 📌 Update Salary
# =========================
@budget_bp.route("/salary", methods=["PUT", "OPTIONS"])
def update_salary():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    try:
        data = request.json or {}
        email = data.get("email")
        salary = data.get("salary")

        if not email or salary is None:
            return jsonify({"error": "Email and salary are required"}), 400

        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.salary = float(salary)
        from app import db
        db.session.commit()

        return jsonify({"message": "Salary updated", "salary": user.salary}), 200
    except Exception as e:
        current_app.logger.exception("❌ Failed to update salary: %s", e)
        return jsonify({"error": "Failed to update salary", "details": str(e)}), 500


# =========================
# 📌 Update Budget
# =========================
@budget_bp.route("/budget", methods=["PUT", "OPTIONS"])
def update_budget():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    try:
        data = request.json or {}
        email = data.get("email")
        budget = data.get("budget")

        if not email or budget is None:
            return jsonify({"error": "Email and budget are required"}), 400

        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.budget_limit = float(budget)
        from app import db
        db.session.commit()

        return jsonify({"message": "Budget updated", "budget": user.budget_limit}), 200
    except Exception as e:
        current_app.logger.exception("❌ Failed to update budget: %s", e)
        return jsonify({"error": "Failed to update budget", "details": str(e)}), 500


# =========================
# 📌 Export PDF Report
# =========================
@budget_bp.route("/export/pdf", methods=["GET", "OPTIONS"])
def export_pdf():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
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
        current_app.logger.exception("❌ Error exporting PDF: %s", e)
        return jsonify({"error": "PDF export failed", "details": str(e)}), 500
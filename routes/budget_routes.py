import io
from flask import Blueprint, request, jsonify, send_file, current_app
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Make matplotlib safe for headless environments (no display needed)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # type: ignore

from datetime import datetime
from models.expense import Expense
from routes.helpers import get_user, build_summary  # your helper functions

# 🔹 NEW: add CORS support for this blueprint
from flask_cors import CORS

budget_bp = Blueprint("budget", __name__)
CORS(
    budget_bp,
    resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
    supports_credentials=True,
)


@budget_bp.route("/export/pdf", methods=["GET", "OPTIONS"])
def export_pdf():
    """
    Export a detailed PDF report of a user's salary, budget, expenses,
    category breakdown, pie chart, line chart, and expense details.
    Query param: ?email=user@example.com
    """
    # ✅ Handle CORS preflight automatically
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = get_user(email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Fetch expenses sorted by date
        expenses = (
            Expense.query.filter_by(user_id=user.id)
            .order_by(Expense.date)
            .all()
        )

        summary = build_summary(user, expenses)

        # Create PDF in memory
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=letter)
        width, height = letter
        y = height - 60

        # === Title ===
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width / 2, y, "Expenses Report")
        y -= 40

        # === Budget Summary ===
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Budget Summary")
        y -= 20
        p.setFont("Helvetica", 10)

        keys = [
            ("salary", "Salary"),
            ("budget_limit", "Budget Limit"),
            ("total_expenses", "Total Expenses"),
            ("savings", "Savings"),
            ("usage_percent", "Usage (%)"),
        ]

        for field, label in keys:
            value = summary.get(field, 0)
            if isinstance(value, float):
                display = f"₹{value:,.2f}"
            elif isinstance(value, int):
                display = f"₹{value:,}"
            else:
                display = str(value)
            p.drawString(50, y, f"{label}: {display}")
            y -= 15
        y -= 10

        # === Category Breakdown ===
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Category Breakdown")
        y -= 20
        p.setFont("Helvetica", 10)

        cat_summary = summary.get("category_summary", {}) or {}
        for cat, amt in sorted(cat_summary.items(), key=lambda x: -float(x[1] or 0)):
            amt_val = float(amt or 0)
            p.drawString(50, y, f"{cat}: ₹{amt_val:,.2f}")
            y -= 15
            if y < 220:
                p.showPage()
                y = height - 60
        y -= 10

        # === Pie Chart ===
        if cat_summary:
            try:
                fig, ax = plt.subplots()
                labels = list(cat_summary.keys())
                sizes = [float(v or 0) for v in cat_summary.values()]

                if sum(sizes) > 0:  # avoid empty data
                    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
                    ax.set_title("Expenses by Category")
                    fig.tight_layout()

                    pie_img = io.BytesIO()
                    plt.savefig(pie_img, format="PNG", bbox_inches="tight")
                    plt.close(fig)
                    pie_img.seek(0)

                    if y < 300:
                        p.showPage()
                        y = height - 60

                    img_w, img_h = 400, 250
                    x_pos = (width - img_w) / 2
                    p.drawImage(ImageReader(pie_img), x_pos, y - img_h, width=img_w, height=img_h)
                    y -= img_h + 10
            except Exception as e:
                current_app.logger.exception("Pie chart generation failed: %s", e)

        # === Line Chart (Cumulative Expenses) ===
        if expenses:
            try:
                dates, amounts = [], []
                for e in expenses:
                    d = getattr(e, "date", None)
                    if isinstance(d, str):
                        try:
                            d = datetime.fromisoformat(d)
                        except Exception:
                            d = None
                    dates.append(d)
                    amounts.append(float(getattr(e, "amount", 0) or 0))

                cum, total = [], 0.0
                for amt in amounts:
                    total += amt
                    cum.append(total)

                if len(cum) > 0:
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

                    img_w, img_h = 400, 250
                    x_pos = (width - img_w) / 2
                    p.drawImage(ImageReader(line_img), x_pos, y - img_h, width=img_w, height=img_h)
                    y -= img_h + 10
            except Exception as e:
                current_app.logger.exception("Line chart generation failed: %s", e)

        # === Expense Details ===
        p.showPage()
        y = height - 60
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Expense Details")
        y -= 20
        p.setFont("Helvetica", 10)

        for e in expenses:
            d = getattr(e, "date", None)
            if isinstance(d, (datetime,)):
                date_str = d.strftime("%Y-%m-%d")
            else:
                date_str = str(d) if d else "Unknown Date"

            desc = getattr(e, "description", getattr(e, "name", "")) or ""
            category = getattr(e, "category", "") or ""
            amount = float(getattr(e, "amount", 0) or 0)

            line = f"{date_str} - {desc} - {category} - ₹{amount:,.2f}"
            p.drawString(50, y, line)
            y -= 15
            if y < 50:
                p.showPage()
                y = height - 60

        # Finish PDF
        p.save()
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="expenses.pdf",
            mimetype="application/pdf"
        )

    except Exception as exc:
        current_app.logger.exception("❌ Error exporting PDF: %s", exc)
        return jsonify({"error": "PDF export failed", "details": str(exc)}), 500
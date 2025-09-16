from flask import Blueprint, request, jsonify, send_file
from models.user import User
from models.expense import Expense
from utils.extensions import db
from datetime import datetime
import io
import csv
import pandas as pd
from reportlab.pdfgen import canvas
from sqlalchemy import extract, func

budget_bp = Blueprint("budget", __name__)

# ================== Expenses ==================

@budget_bp.route("/expenses", methods=["GET"])
def get_expenses():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date.desc()).all()

        expense_list = [
            {
                "id": e.id,
                "description": e.description,
                "amount": float(e.amount),
                "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
            }
            for e in expenses
        ]

        return jsonify({"data": expense_list}), 200
    except Exception as e:
        print("❌ Error in /budget/expenses:", str(e))
        return jsonify({"error": "Server error while fetching expenses"}), 500


@budget_bp.route("/add", methods=["POST"])
def add_expense():
    try:
        data = request.get_json()
        email = data.get("email")
        description = data.get("description", "")
        amount = data.get("amount")
        date_str = data.get("date")

        if not email or amount is None:
            return jsonify({"error": "Email and amount are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # ✅ Convert amount safely
        try:
            clean_amount = float(str(amount).replace("₹", "").replace(",", "").strip())
        except ValueError:
            return jsonify({"error": "Amount must be a number"}), 400

        # ✅ Parse date or default to today
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            date = datetime.utcnow()

        new_expense = Expense(
            user_id=user.id,
            description=description,
            amount=clean_amount,
            date=date
        )
        db.session.add(new_expense)
        db.session.commit()

        return jsonify({"message": "Expense added successfully"}), 201
    except Exception as e:
        print("❌ Error in /budget/add:", str(e))
        return jsonify({"error": "Server error while adding expense"}), 500


@budget_bp.route("/update/<int:id>", methods=["PUT"])
def update_expense(id):
    try:
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

        db.session.commit()
        return jsonify({"message": "Expense updated successfully"}), 200
    except Exception as e:
        print("❌ Error in /budget/update:", str(e))
        return jsonify({"error": "Server error while updating expense"}), 500


@budget_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):
    try:
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully"}), 200
    except Exception as e:
        print("❌ Error in /budget/delete:", str(e))
        return jsonify({"error": "Server error while deleting expense"}), 500


# ================== Reports ==================

@budget_bp.route("/download-expenses-csv", methods=["GET"])
def download_csv():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(user_id=user.id).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Description", "Amount", "Date"])
        for e in expenses:
            writer.writerow([e.id, e.description, e.amount, e.date.strftime("%Y-%m-%d") if e.date else ""])

        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode("utf-8")),
                         mimetype="text/csv",
                         as_attachment=True,
                         download_name="expenses.csv")
    except Exception as e:
        print("❌ Error in /budget/download-expenses-csv:", str(e))
        return jsonify({"error": "Server error while generating CSV"}), 500


@budget_bp.route("/download-expenses-excel", methods=["GET"])
def download_excel():
    try:
        email = request.args.get("email")
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(user_id=user.id).all()
        data = [
            {"Description": e.description, "Amount": float(e.amount), "Date": e.date.strftime("%Y-%m-%d")}
            for e in expenses
        ]

        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        return send_file(output,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True,
                         download_name="expenses.xlsx")
    except Exception as e:
        print("❌ Error in /budget/download-expenses-excel:", str(e))
        return jsonify({"error": "Server error while generating Excel"}), 500


@budget_bp.route("/download-expenses-pdf", methods=["GET"])
def download_pdf():
    try:
        email = request.args.get("email")
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(user_id=user.id).all()
        output = io.BytesIO()
        p = canvas.Canvas(output)
        p.drawString(100, 800, f"Expenses Report for {email}")

        y = 760
        for e in expenses:
            p.drawString(100, y, f"{e.date.strftime('%Y-%m-%d')} | {e.description} - ₹{e.amount}")
            y -= 20
            if y < 50:
                p.showPage()
                y = 800

        p.save()
        output.seek(0)

        return send_file(output, mimetype="application/pdf", as_attachment=True, download_name="expenses.pdf")
    except Exception as e:
        print("❌ Error in /budget/download-expenses-pdf:", str(e))
        return jsonify({"error": "Server error while generating PDF"}), 500


# ================== Trends ==================

@budget_bp.route("/trends", methods=["GET"])
def get_trends():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date).all()

        total_expenses = sum(e.amount for e in expenses)
        salary = user.salary or 0
        savings = salary - total_expenses if salary > 0 else 0

        expense_list = [
            {"date": e.date.strftime("%Y-%m-%d"), "amount": float(e.amount)}
            for e in expenses
        ]

        return jsonify({
            "salary": float(salary),
            "total_expenses": float(total_expenses),
            "savings": float(savings),
            "expenses": expense_list
        }), 200
    except Exception as e:
        print("❌ Error in /budget/trends:", str(e))
        return jsonify({"error": "Server error while fetching trends"}), 500


@budget_bp.route("/monthly-trends", methods=["GET"])
def get_monthly_trends():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Group by year + month
        monthly_data = (
            db.session.query(
                extract("year", Expense.date).label("year"),
                extract("month", Expense.date).label("month"),
                func.sum(Expense.amount).label("total")
            )
            .filter(Expense.user_id == user.id)
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )

        result = [
            {
                "month": f"{int(m)}-{int(y)}",
                "total": float(total)
            }
            for y, m, total in monthly_data
        ]

        return jsonify(result), 200
    except Exception as e:
        print("❌ Error in /budget/monthly-trends:", str(e))
        return jsonify({"error": "Server error while fetching monthly trends"}), 500
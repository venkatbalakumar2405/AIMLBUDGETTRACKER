from flask import Blueprint, jsonify, send_file
from utils.scheduler_jobs import monthly_report_job
from utils.decorators import token_required
from utils.report_utils import generate_csv, generate_excel, generate_pdf
import io

budget_bp = Blueprint("budget", __name__)

# ✅ Manual report trigger
@budget_bp.route("/send-monthly-report-now", methods=["POST"])
@token_required
def send_monthly_report_now(current_user):
    try:
        monthly_report_job(single_user=current_user)
        return jsonify({"message": "Report sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ CSV Download
@budget_bp.route("/download-expenses-csv", methods=["GET"])
@token_required
def download_expenses_csv(current_user):
    try:
        buffer = io.BytesIO()
        generate_csv(current_user, buffer)

        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="text/csv",
            as_attachment=True,
            download_name="expenses.csv"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Excel Download
@budget_bp.route("/download-expenses-excel", methods=["GET"])
@token_required
def download_expenses_excel(current_user):
    try:
        buffer = io.BytesIO()
        generate_excel(current_user, buffer)

        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="expenses.xlsx"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ PDF Download
@budget_bp.route("/download-expenses-pdf", methods=["GET"])
@token_required
def download_expenses_pdf(current_user):
    try:
        buffer = io.BytesIO()
        generate_pdf(current_user, buffer)

        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="expenses.pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
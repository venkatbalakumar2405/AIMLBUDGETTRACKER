import io
import csv
import pandas as pd
from fpdf import FPDF

# Lazy import to avoid circular issues
def get_expense_model():
    from models.expense import Expense
    return Expense


def generate_csv(expenses):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Amount", "Description"])

    for expense in expenses:
        writer.writerow([expense.date, expense.category, expense.amount, expense.description])

    return io.BytesIO(output.getvalue().encode())


def generate_excel(expenses):
    data = [
        {"Date": e.date, "Category": e.category, "Amount": e.amount, "Description": e.description}
        for e in expenses
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Expenses")
    output.seek(0)
    return output


def generate_pdf(expenses):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Expense Report", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(40, 10, "Category", 1)
    pdf.cell(40, 10, "Amount", 1)
    pdf.cell(70, 10, "Description", 1)
    pdf.ln()

    for expense in expenses:
        pdf.cell(40, 10, str(expense.date), 1)
        pdf.cell(40, 10, expense.category, 1)
        pdf.cell(40, 10, str(expense.amount), 1)
        pdf.cell(70, 10, expense.description, 1)
        pdf.ln()

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output
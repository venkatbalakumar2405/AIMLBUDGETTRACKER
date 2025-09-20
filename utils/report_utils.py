import io
import csv
import pandas as pd
from fpdf import FPDF
from typing import List, Any


# ================== Lazy Import ==================
def get_expense_model():
    """
    Lazy import to avoid circular imports.
    Call this when you need the Expense model.
    """
    from models.expense import Expense
    return Expense


# ================== CSV Report ==================
def generate_csv(expenses: List[Any]) -> io.BytesIO:
    """
    Generate a CSV report from expenses.
    
    Args:
        expenses: List of Expense model instances.
    
    Returns:
        BytesIO containing CSV data.
    """
    headers = ["Date", "Category", "Amount", "Description"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for e in expenses:
        writer.writerow([
            e.date or "",
            e.category or "Misc",
            e.amount or 0,
            e.description or "",
        ])

    buffer = io.BytesIO(output.getvalue().encode("utf-8"))
    buffer.seek(0)
    return buffer


# ================== Excel Report ==================
def generate_excel(expenses: List[Any]) -> io.BytesIO:
    """
    Generate an Excel report from expenses.
    
    Args:
        expenses: List of Expense model instances.
    
    Returns:
        BytesIO containing Excel data.
    """
    data = [
        {
            "Date": e.date or "",
            "Category": e.category or "Misc",
            "Amount": e.amount or 0,
            "Description": e.description or "",
        }
        for e in expenses
    ]
    df = pd.DataFrame(data)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Expenses")
    buffer.seek(0)
    return buffer


# ================== PDF Report ==================
def generate_pdf(expenses: List[Any]) -> io.BytesIO:
    """
    Generate a PDF report from expenses.
    
    Args:
        expenses: List of Expense model instances.
    
    Returns:
        BytesIO containing PDF data.
    """
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", size=14, style="B")
    pdf.cell(200, 10, txt="Expense Report", ln=True, align="C")
    pdf.ln(10)

    # Headers
    pdf.set_font("Arial", size=10, style="B")
    pdf.cell(40, 10, "Date", 1)
    pdf.cell(40, 10, "Category", 1)
    pdf.cell(40, 10, "Amount", 1)
    pdf.cell(70, 10, "Description", 1)
    pdf.ln()

    # Rows
    pdf.set_font("Arial", size=9)
    for e in expenses:
        pdf.cell(40, 10, str(e.date or ""), 1)
        pdf.cell(40, 10, str(e.category or "Misc"), 1)
        pdf.cell(40, 10, str(e.amount or 0), 1)
        pdf.cell(70, 10, str(e.description or ""), 1)
        pdf.ln()

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer
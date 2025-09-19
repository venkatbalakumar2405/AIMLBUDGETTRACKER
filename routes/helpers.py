from models.user import User

# ================== Helper Functions ==================

def get_user(email: str):
    """Fetch a user by email (case-insensitive)."""
    if not email:
        return None
    return User.query.filter_by(email=email.lower().strip()).first()


def build_summary(user, expenses):
    """
    Build a budget summary for a user.
    Returns a dictionary with salary, budget_limit, total expenses,
    savings, usage percent, and category breakdown.
    """
    if not user:
        return {}

    category_summary = {}
    total_expenses = 0

    for e in expenses:
        amt = float(e.amount or 0)
        total_expenses += amt
        cat = e.category or "Misc"
        category_summary[cat] = category_summary.get(cat, 0) + amt

    salary = float(user.salary or 0)
    budget_limit = float(user.budget_limit or 0)
    savings = max(budget_limit - total_expenses, 0)
    usage_percent = (total_expenses / budget_limit * 100) if budget_limit else 0

    return {
        "salary": salary,
        "budget_limit": budget_limit,
        "total_expenses": total_expenses,
        "savings": savings,
        "usage_percent": round(usage_percent, 2),
        "category_summary": category_summary,
    }
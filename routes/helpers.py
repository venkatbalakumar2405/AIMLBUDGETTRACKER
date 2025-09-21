from typing import Dict, Optional, List
from models import User


# ================== Helper Functions ================== #
def get_user(email: Optional[str]) -> Optional[User]:
    """Fetch a user by email (case-insensitive)."""
    if not email:
        return None
    return User.query.filter_by(email=email.lower().strip()).first()


def build_summary(user: Optional[User], expenses: Optional[List]) -> Dict:
    """
    Build a budget summary for a user.

    Returns:
        dict: {
            salary, budget_limit, total_expenses,
            savings, usage_percent, category_summary
        }
    """
    if not user:
        return {
            "salary": 0.0,
            "budget_limit": 0.0,
            "total_expenses": 0.0,
            "savings": 0.0,
            "usage_percent": 0.0,
            "category_summary": {},
        }

    category_summary: Dict[str, float] = {}
    total_expenses: float = 0.0

    for e in expenses or []:
        amt = float(getattr(e, "amount", 0) or 0.0)
        cat = getattr(e, "category", None) or "Miscellaneous"
        total_expenses += amt
        category_summary[cat] = category_summary.get(cat, 0.0) + amt

    salary = float(getattr(user, "salary", 0.0) or 0.0)
    budget_limit = float(getattr(user, "budget_limit", 0.0) or 0.0)

    savings = max(budget_limit - total_expenses, 0.0)
    usage_percent = (total_expenses / budget_limit * 100.0) if budget_limit else 0.0

    return {
        "salary": salary,
        "budget_limit": budget_limit,
        "total_expenses": total_expenses,
        "savings": savings,
        "usage_percent": round(usage_percent, 2),
        "category_summary": category_summary,
    }

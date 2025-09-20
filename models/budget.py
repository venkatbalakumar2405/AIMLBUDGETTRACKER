from utils.extensions import db
from datetime import datetime


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(100), nullable=False, default="Miscellaneous")
    limit = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Budget {self.category} - Limit: {self.limit}>"


# ================== Utility Functions ==================

def reset_all_budgets(user_id):
    """Reset all budgets for a user back to zero."""
    budgets = Budget.query.filter_by(user_id=user_id).all()
    for budget in budgets:
        budget.limit = 0.0
    db.session.commit()


def delete_all_budgets(user_id):
    """Delete all budgets for a user."""
    budgets = Budget.query.filter_by(user_id=user_id).all()
    for budget in budgets:  # ✅ changed from `for e in budgets`
        db.session.delete(budget)
    db.session.commit()


def seed_default_budgets(user_id):
    """Seed default categories if none exist."""
    default_categories = ["Food", "Transport", "Entertainment", "Bills", "Miscellaneous"]

    budgets = Budget.query.filter_by(user_id=user_id).all()
    if not budgets:
        for category in default_categories:  # ✅ meaningful name
            db.session.add(Budget(user_id=user_id, category=category, limit=0.0))
        db.session.commit()


def update_budget_limits(user_id, new_limits):
    """Update budget limits from a dict {category: limit}."""
    budgets = Budget.query.filter_by(user_id=user_id).all()

    for budget in budgets:  # ✅ not `e`
        if budget.category in new_limits:
            budget.limit = float(new_limits[budget.category])

    db.session.commit()


def remove_unused_categories(user_id, used_categories):
    """Remove categories that are not in use anymore."""
    budgets = Budget.query.filter_by(user_id=user_id).all()

    for budget in budgets:  # ✅
        if budget.category not in used_categories:
            db.session.delete(budget)

    db.session.commit()
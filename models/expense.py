from utils.extensions import db
from datetime import datetime


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    category = db.Column(
        db.String(100),
        default="Miscellaneous",
        nullable=False,
        index=True
    )

    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    user = db.relationship("User", back_populates="expenses")

    # ================== Methods ==================

    def to_dict(self, include_user: bool = False):
        """Serialize expense object for API responses."""
        data = {
            "id": self.id,
            "description": self.description,
            "amount": float(self.amount),
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else None,
            "category": self.category or "Miscellaneous",
            "user_id": self.user_id,
        }

        if include_user and self.user:
            data["user"] = {
                "id": self.user.id,
                "email": self.user.email,
                "salary": float(self.user.salary or 0),
                "budget_limit": float(self.user.budget_limit or 0),
            }

        return data

    @classmethod
    def from_dict(cls, data, user_id):
        """Factory method to create an Expense instance from a dict."""
        return cls(
            description=data.get("description", "").strip(),
            amount=float(data.get("amount", 0)),
            date=datetime.strptime(data.get("date"), "%Y-%m-%d") if data.get("date") else datetime.utcnow(),
            category=(data.get("category") or "Miscellaneous").title(),
            user_id=user_id,
        )

    def __repr__(self):
        return f"<Expense id={self.id}, user_id={self.user_id}, category={self.category}, amount={self.amount}>"

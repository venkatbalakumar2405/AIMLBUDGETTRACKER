from utils.extensions import db


class User(db.Model):
    """
    User model for authentication and budget tracking.
    Stores salary, budget limit, and related expenses.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    # Budget-related fields with indexing
    salary = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
        server_default="0",
        index=True,  # ✅ index for faster queries
    )
    budget_limit = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
        server_default="0",
        index=True,  # ✅ index for faster queries
    )

    # Relationships
    expenses = db.relationship(
        "Expense",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined",  # eager load to avoid N+1 queries
    )

    # ------------------ Utility Methods ------------------ #

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"

    def to_dict(self, include_expenses: bool = False) -> dict:
        """
        Serialize user data into a dictionary.
        Optionally include related expenses.
        """
        data = {
            "id": self.id,
            "email": self.email,
            "salary": float(self.salary or 0),
            "budget_limit": float(self.budget_limit or 0),
        }

        if include_expenses:
            data["expenses"] = [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": float(e.amount or 0),
                    "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                    "category": e.category,
                }
                for e in self.expenses
            ]

        return data
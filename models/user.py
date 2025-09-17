from utils.extensions import db


class User(db.Model):
    """
    User model for authentication and budget tracking.
    Stores salary, budget limit, and related expenses.
    """
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    salary = db.Column(db.Float, default=0.0, nullable=False)
    budget_limit = db.Column(db.Float, default=0.0, nullable=False)

    # Relationships
    expenses = db.relationship(
        "Expense",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<User {self.email}>"

    def to_dict(self, include_expenses=False):
        """
        Serialize user data into a dictionary.
        Optionally include expenses.
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
                    "amount": float(e.amount),
                    "date": e.date.strftime("%Y-%m-%d %H:%M:%S") if e.date else None,
                    "category": e.category,
                }
                for e in self.expenses
            ]

        return data
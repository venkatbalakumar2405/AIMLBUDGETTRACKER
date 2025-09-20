from utils.extensions import db


class User(db.Model):
    """
    User model for authentication and budget tracking.
    Stores email, hashed password, salary, budget limit, and related expenses.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    # Budget-related fields with defaults & indexing
    salary = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
        server_default="0",
        index=True,
    )
    budget_limit = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
        server_default="0",
        index=True,
    )

    # Relationships
    expenses = db.relationship(
        "Expense",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",  # ✅ better than "joined" for large datasets
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
            data["expenses"] = [e.to_dict() for e in self.expenses]

        return data
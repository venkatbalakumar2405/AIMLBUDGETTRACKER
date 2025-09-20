# models/salary.py
from utils.extensions import db

class Salary(db.Model):
    __tablename__ = "salaries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)  # e.g., 2025
    amount = db.Column(db.Float, nullable=False, default=0.0)

    # Relationship back to user (optional, if you need it)
    user = db.relationship("User", backref=db.backref("salaries", lazy=True))

    def __init__(self, user_id, year, amount):
        self.user_id = user_id
        self.year = year
        self.amount = amount

    def to_dict(self):
        """Serialize Salary object into dict (for JSON responses)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "year": self.year,
            "amount": self.amount,
        }

    def __repr__(self):
        return f"<Salary user_id={self.user_id}, year={self.year}, amount={self.amount}>"
from utils.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    salary = db.Column(db.Float, default=0.0)
    budget_limit = db.Column(db.Float, default=0.0)

    # Relationships
    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")
    salaries = db.relationship("Salary", backref="user", lazy=True, cascade="all, delete-orphan")

    # Helper methods
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
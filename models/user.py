from utils.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"   # ✅ matches your DB table name

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    budget_limit = db.Column(db.Float, default=0.0)

    # Relationships
    expenses = db.relationship("Expense", backref="user", lazy=True)
    salaries = db.relationship("Salary", backref="user", lazy=True)

    # Helper methods
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
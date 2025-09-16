from utils.extensions import db

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}  # ✅ same fix

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    salary = db.Column(db.Float, default=0)
    budget_limit = db.Column(db.Float, default=0)

    expenses = db.relationship("Expense", back_populates="user", cascade="all, delete-orphan")
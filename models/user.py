from utils.extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    salary = db.Column(db.Float, default=0)

    # Relationship
    expenses = db.relationship("Expense", back_populates="user", cascade="all, delete")
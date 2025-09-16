from utils.extensions import db
from datetime import datetime

class Expense(db.Model):
    __tablename__ = "expenses"   # ensure consistent table name
    __table_args__ = {"extend_existing": True}  # ✅ prevents duplicate definition

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default="Miscellaneous")
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="expenses")
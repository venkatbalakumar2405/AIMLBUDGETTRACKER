from utils.extensions import db

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    expense_date = db.Column(db.Date)

    # FK → users.id
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
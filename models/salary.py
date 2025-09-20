from utils.extensions import db

class Salary(db.Model):
    __tablename__ = "salary"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    salary_date = db.Column(db.Date)

    # FK → users.id
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
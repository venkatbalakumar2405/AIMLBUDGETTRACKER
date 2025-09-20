from utils.extensions import db
from models.user import User
from models.expense import Expense
from app import create_app
from datetime import datetime
from werkzeug.security import generate_password_hash
import sys

app = create_app()

with app.app_context():
    # ✅ Check for reset flag
    reset = "--reset" in sys.argv

    # ✅ Create test user if not exists
    user = User.query.filter_by(email="testuser@example.com").first()
    if not user:
        user = User(
            email="testuser@example.com",
            password=generate_password_hash("Bala123")
        )
        db.session.add(user)
        db.session.commit()
        print("✅ Test user created: testuser@example.com / Bala123")
    else:
        print("ℹ️ Test user already exists.")

    if reset:
        # ✅ Clear existing expenses for this user
        Expense.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        print("♻️ Old expenses cleared.")

    # ✅ Insert sample expenses if none exist
    existing_expenses = Expense.query.filter_by(user_id=user.id).count()
    if existing_expenses == 0:
        expenses = [
            Expense(user_id=user.id, category="Salary", amount=5000,
                    date=datetime(2025, 1, 1), description="Monthly salary"),
            Expense(user_id=user.id, category="Food", amount=1200,
                    date=datetime(2025, 1, 5), description="Groceries and dining"),
            Expense(user_id=user.id, category="Transport", amount=400,
                    date=datetime(2025, 1, 10), description="Bus and fuel"),
            Expense(user_id=user.id, category="Salary", amount=5200,
                    date=datetime(2025, 2, 1), description="Monthly salary"),
            Expense(user_id=user.id, category="Food", amount=1500,
                    date=datetime(2025, 2, 7), description="Eating out"),
            Expense(user_id=user.id, category="Shopping", amount=2000,
                    date=datetime(2025, 2, 15), description="Clothes and gadgets"),
            Expense(user_id=user.id, category="Salary", amount=5100,
                    date=datetime(2025, 3, 1), description="Monthly salary"),
            Expense(user_id=user.id, category="Bills", amount=1800,
                    date=datetime(2025, 3, 10), description="Electricity and internet"),
            Expense(user_id=user.id, category="Travel", amount=2500,
                    date=datetime(2025, 3, 20), description="Vacation trip"),
        ]

        db.session.bulk_save_objects(expenses)
        db.session.commit()
        print("✅ Database seeded with test expenses.")
    else:
        print("ℹ️ Expenses already exist, skipping seeding. Use --reset to refresh.")
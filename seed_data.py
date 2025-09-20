from utils.extensions import db
from models.user import User
from models.expense import Expense
from models.salary import Salary
from app import create_app
from datetime import datetime
from werkzeug.security import generate_password_hash
import sys

app = create_app()

with app.app_context():
    reset = "--reset" in sys.argv

    # ✅ Ensure test user
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
        Expense.query.filter_by(user_id=user.id).delete()
        Salary.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        print("♻️ Old salaries & expenses cleared.")

    # ✅ Insert salaries (Jan–Dec 2025)
    if Salary.query.filter_by(user_id=user.id).count() == 0:
        salaries = [
            Salary(user_id=user.id, amount=5000, received_date=datetime(2025, 1, 1)),
            Salary(user_id=user.id, amount=5050, received_date=datetime(2025, 2, 1)),
            Salary(user_id=user.id, amount=5100, received_date=datetime(2025, 3, 1)),
            Salary(user_id=user.id, amount=5200, received_date=datetime(2025, 4, 1)),
            Salary(user_id=user.id, amount=5250, received_date=datetime(2025, 5, 1)),
            Salary(user_id=user.id, amount=5300, received_date=datetime(2025, 6, 1)),
            Salary(user_id=user.id, amount=5400, received_date=datetime(2025, 7, 1)),
            Salary(user_id=user.id, amount=5450, received_date=datetime(2025, 8, 1)),
            Salary(user_id=user.id, amount=5500, received_date=datetime(2025, 9, 1)),
            Salary(user_id=user.id, amount=5600, received_date=datetime(2025, 10, 1)),
            Salary(user_id=user.id, amount=5650, received_date=datetime(2025, 11, 1)),
            Salary(user_id=user.id, amount=5700, received_date=datetime(2025, 12, 1)),
        ]
        db.session.bulk_save_objects(salaries)
        db.session.commit()
        print("✅ Inserted 12 months of salaries.")

    # ✅ Insert expenses (Jan–Dec 2025)
    if Expense.query.filter_by(user_id=user.id).count() == 0:
        expenses = [
            # January
            Expense(user_id=user.id, category="Food", amount=1200, date=datetime(2025, 1, 5), description="Groceries"),
            Expense(user_id=user.id, category="Rent", amount=2000, date=datetime(2025, 1, 1), description="Monthly rent"),
            Expense(user_id=user.id, category="Transport", amount=300, date=datetime(2025, 1, 10), description="Bus & fuel"),

            # February
            Expense(user_id=user.id, category="Food", amount=1500, date=datetime(2025, 2, 7), description="Dining out"),
            Expense(user_id=user.id, category="Shopping", amount=1800, date=datetime(2025, 2, 15), description="Clothes"),
            Expense(user_id=user.id, category="Bills", amount=900, date=datetime(2025, 2, 20), description="Electricity"),

            # March
            Expense(user_id=user.id, category="Food", amount=1400, date=datetime(2025, 3, 8), description="Groceries"),
            Expense(user_id=user.id, category="Travel", amount=2500, date=datetime(2025, 3, 20), description="Vacation trip"),

            # April
            Expense(user_id=user.id, category="Food", amount=1600, date=datetime(2025, 4, 6), description="Dining out"),
            Expense(user_id=user.id, category="Bills", amount=1000, date=datetime(2025, 4, 12), description="Water & electricity"),

            # May
            Expense(user_id=user.id, category="Shopping", amount=2200, date=datetime(2025, 5, 18), description="Electronics"),
            Expense(user_id=user.id, category="Other", amount=800, date=datetime(2025, 5, 25), description="Miscellaneous"),

            # June
            Expense(user_id=user.id, category="Food", amount=1700, date=datetime(2025, 6, 5), description="Dining & groceries"),
            Expense(user_id=user.id, category="Bills", amount=1200, date=datetime(2025, 6, 15), description="Internet"),

            # July
            Expense(user_id=user.id, category="Travel", amount=3000, date=datetime(2025, 7, 22), description="Trip to Goa"),
            Expense(user_id=user.id, category="Food", amount=1500, date=datetime(2025, 7, 10), description="Restaurants"),

            # August
            Expense(user_id=user.id, category="Rent", amount=2100, date=datetime(2025, 8, 1), description="Monthly rent"),
            Expense(user_id=user.id, category="Shopping", amount=2500, date=datetime(2025, 8, 18), description="Festival shopping"),

            # September
            Expense(user_id=user.id, category="Food", amount=1600, date=datetime(2025, 9, 7), description="Groceries"),
            Expense(user_id=user.id, category="Transport", amount=500, date=datetime(2025, 9, 15), description="Fuel"),

            # October
            Expense(user_id=user.id, category="Bills", amount=1300, date=datetime(2025, 10, 12), description="Electricity & water"),
            Expense(user_id=user.id, category="Travel", amount=4000, date=datetime(2025, 10, 22), description="Family trip"),

            # November
            Expense(user_id=user.id, category="Food", amount=1700, date=datetime(2025, 11, 6), description="Groceries"),
            Expense(user_id=user.id, category="Shopping", amount=2800, date=datetime(2025, 11, 15), description="Diwali shopping"),

            # December
            Expense(user_id=user.id, category="Food", amount=2000, date=datetime(2025, 12, 8), description="Holiday dining"),
            Expense(user_id=user.id, category="Other", amount=1500, date=datetime(2025, 12, 20), description="Miscellaneous"),
        ]
        db.session.bulk_save_objects(expenses)
        db.session.commit()
        print("✅ Inserted sample expenses for all 12 months.")
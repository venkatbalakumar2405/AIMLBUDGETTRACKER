from .auth_routes import auth_bp
from .budget_routes import budget_bp
from .home_routes import home_bp
from .trends_routes import trends_bp
from .expense_routes import expense_bp
from .salary_routes import salary_bp

__all__ = [
    "auth_bp",
    "budget_bp",
    "home_bp",
    "trends_bp",
    "expense_bp",
    "salary_bp",
]

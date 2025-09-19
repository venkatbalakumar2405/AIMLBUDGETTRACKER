from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_apscheduler import APScheduler

# ================== Flask Extensions ==================
# Initialize Flask extensions once; they will be bound to the app later
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
scheduler = APScheduler()
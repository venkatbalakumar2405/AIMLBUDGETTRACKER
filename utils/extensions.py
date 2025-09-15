from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_apscheduler import APScheduler

# ✅ Initialize Flask extensions (only once, no app binding yet)
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
scheduler = APScheduler()
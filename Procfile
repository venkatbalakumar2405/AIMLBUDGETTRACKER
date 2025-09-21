# Procfile (for Render deployment)

# Run the Flask app using Gunicorn.
# "app" = the filename (app.py, without .py)
# "create_app()" = the application factory function
# "-b 0.0.0.0:5000" ensures Gunicorn listens on Render's expected port
web: gunicorn "app:create_app()" -b 0.0.0.0:$PORT --workers=4 --threads=2 --timeout 120

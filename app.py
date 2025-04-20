from flask import Flask
from config import Config
from extensions import db, migrate
from routes import register_blueprints


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    register_blueprints(app)

    # Load configuration
    app.config.from_object(Config)
    if app.config["SQLALCHEMY_DATABASE_URI"] == "DATABASE_URL not set.":
        raise ValueError("DATABASE_URL is not set!")
    if not app.config.get("SECRET_KEY"):
        raise ValueError("SECRET_KEY is not set! Please configure it properly in the environment or config.")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Routes are now defined in blueprint files in the routes/ directory
    # - Main routes (/, /favicon.ico) are in routes/main_routes.py
    # - Authentication routes (/login, /logout) are in routes/auth_routes.py

    with app.app_context():
        db.create_all()  # Create all tables (like the "users" table)

    return app


if __name__ == "__main__":
    application = create_app()  # Renaming 'app' to 'application' in the outer scope
    application.run(debug=True)

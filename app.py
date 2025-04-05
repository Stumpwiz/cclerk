from flask import Flask
from config import Config
from extensions import db, migrate
from routes import register_blueprints
from commands.init_db import init_db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    register_blueprints(app)
    # Register CLI command
    app.cli.add_command(init_db)

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
        db.create_all()  # Create all tables (like the users table)
        #
        # # Create a dedicated directory for LaTeX compilation
        # import os
        # import shutil
        # latex_compile_dir = os.path.join(app.instance_path, "latex_compile")
        # os.makedirs(latex_compile_dir, exist_ok=True)
        #
        # # Copy the logo file to the LaTeX compilation directory
        # logo_src_path = os.path.join(app.root_path, "static", "residentCouncilLogoSmall.jpg")
        # logo_dest_path = os.path.join(latex_compile_dir, "residentCouncilLogoSmall.jpg")
        # if os.path.exists(logo_src_path):
        #     shutil.copy2(logo_src_path, logo_dest_path)
        #     print(f"Logo file copied to LaTeX compilation directory: {logo_dest_path}")
        # else:
        #     print(f"Warning: Logo file not found at {logo_src_path}")

    return app


if __name__ == "__main__":
    application = create_app()  # Renaming 'app' to 'application' in the outer scope
    application.run(debug=True)

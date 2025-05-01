import click
from flask import Flask, current_app, render_template
from flask.cli import with_appcontext

from config import Config
from extensions import db, migrate, csrf
from routes import register_blueprints


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    register_blueprints(app)

    # Load configuration
    if test_config is None:
        app.config.from_object(Config)
        if app.config["SQLALCHEMY_DATABASE_URI"] == "DATABASE_URL not set.":
            raise ValueError("DATABASE_URL is not set!")
        if not app.config.get("SECRET_KEY"):
            raise ValueError("SECRET_KEY is not set! Please configure it properly in the environment or config.")
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Routes are now defined in blueprint files in the routes/ directory
    # - Main routes (/, /favicon.ico) are in routes/main_routes.py
    # - Authentication routes (/login, /logout) are in routes/auth_routes.py

    @app.before_request
    def load_logged_in_user():
        from flask import g, session
        from models.user import User

        user_id = session.get('user_id')
        if user_id is None:
            g.user = None
        else:
            g.user = User.query.get(user_id)

    with app.app_context():
        db.create_all()  # Create all tables (like the "users" table)

    @click.command('init-db')
    @with_appcontext
    def init_db_command():
        from db_utils import init_db
        """Clear the existing data and create new tables/views from schema.sql."""
        init_db()
        click.echo(f"Initialized test database from schema.sql at {current_app.config['DATABASE']}")

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


if __name__ == "__main__":
    application = create_app()  # Renaming 'app' to 'application' in the outer scope
    application.run(debug=True)

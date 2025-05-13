from flask import Flask, current_app, render_template

from config import Config
from extensions import db, migrate, csrf
from routes import register_blueprints

from dotenv import load_dotenv
import os
import json
import shutil
import subprocess
import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))



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
            g.user = db.session.get(User, user_id)

    with app.app_context():
        db.create_all()  # Create all tables (like the "users" table)


    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # Register CSRF error handler
    from flask_wtf.csrf import CSRFError
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import jsonify, request

        # Print debug information
        print(f"CSRF error: {str(e)}")
        print(f"Request path: {request.path}")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request form data: {request.form}")
        print(f"Request JSON data: {request.get_json(silent=True)}")
        print(f"Request raw data: {request.data}")

        # Check if the CSRF token is in the request
        csrf_token = request.headers.get('X-CSRFToken')
        if csrf_token:
            print(f"CSRF token found in headers: {csrf_token}")
        else:
            print("CSRF token not found in headers")

        # Check if the CSRF token is in the form data
        if request.form and '_csrf_token' in request.form:
            print(f"CSRF token found in form data: {request.form['_csrf_token']}")
        else:
            print("CSRF token not found in form data")

        # Always return JSON for any delete requests, regardless of method
        if '/delete_file' in request.path or '/delete_pdf' in request.path:
            print(f"Returning JSON response for {request.path} request")
            return jsonify({
                "success": False, 
                "error": "CSRF token validation failed", 
                "details": str(e),
                "path": request.path,
                "method": request.method
            }), 400

        # Check multiple conditions to identify AJAX/JSON requests
        content_type = request.headers.get('Content-Type', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        accepts_json = 'application/json' in request.headers.get('Accept', '')

        # Additional check for fetch requests
        is_fetch_request = request.referrer and ('fetch' in request.referrer or 'ajax' in request.referrer.lower())

        # Check if the request is from the home page
        is_home_request = False
        if request.referrer:
            referrer_path = request.referrer.split('://')[-1].split('/', 1)[-1] if '/' in request.referrer.split('://')[-1] else ''
            is_home_request = referrer_path == ''

        if request.is_json or 'application/json' in content_type or is_ajax or accepts_json or is_fetch_request or is_home_request:
            return jsonify({"success": False, "error": "CSRF token validation failed", "details": str(e)}), 400
        return render_template('errors/400.html', reason=str(e)), 400

    return app


if __name__ == "__main__":
    application = create_app()  # Renaming 'app' to 'application' in the outer scope
    application.run(debug=True)

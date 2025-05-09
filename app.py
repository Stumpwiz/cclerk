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

def check_for_scheduled_restore(app):
    """
    Check if a database restore operation has been scheduled and perform it if needed.

    This function is called when the application starts. It checks for the presence
    of a restore_scheduled.json file in the instance directory. If the file exists,
    it performs the restore operation and then deletes the file.
    """
    restore_info_path = os.path.join(app.root_path, 'instance', 'restore_scheduled.json')

    if not os.path.exists(restore_info_path):
        return

    app.logger.info("Found scheduled restore operation")

    try:
        # Read the restore information from the file
        with open(restore_info_path, 'r') as f:
            restore_info = json.load(f)

        sql_file = restore_info.get('sql_file')
        if not sql_file:
            app.logger.error("Invalid restore information: missing SQL file name")
            os.remove(restore_info_path)
            return

        # Get the full path to the SQL file
        backup_dir = os.path.join(app.root_path, app.config['BACKUP_DIR'])
        sql_path = os.path.join(backup_dir, sql_file)

        if not os.path.exists(sql_path):
            app.logger.error(f"SQL file not found: {sql_path}")
            os.remove(restore_info_path)
            return

        # Database path
        db_path = os.path.join(app.root_path, app.config['DB_PATH'])
        temp_backup = f"{db_path}.bak"
        temp_new_db = f"{db_path}.new"

        # Create a backup of the current database
        if os.path.exists(db_path):
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
            shutil.copy2(db_path, temp_backup)

        # Create a new empty database file
        if os.path.exists(temp_new_db):
            os.remove(temp_new_db)
        open(temp_new_db, 'a').close()

        # Restore from the SQL file to the new database
        command = f"sqlite3 {temp_new_db} < {sql_path}"
        subprocess.run(command, shell=True, check=True)

        # Replace the current database with the new one
        if os.path.exists(db_path):
            os.remove(db_path)
        shutil.move(temp_new_db, db_path)

        # Clean up the temporary backup
        if os.path.exists(temp_backup):
            os.remove(temp_backup)

        app.logger.info(f"Successfully restored database from {sql_file}")

        # Create a file to indicate that a restore has been completed
        restore_completed_path = os.path.join(app.root_path, 'instance', 'restore_completed.json')
        with open(restore_completed_path, 'w') as f:
            json.dump({
                'sql_file': sql_file,
                'timestamp': datetime.datetime.now().isoformat()
            }, f)
        app.logger.info(f"Created restore_completed.json file")
    except Exception as e:
        app.logger.error(f"Error during scheduled restore: {str(e)}")

        # Try to restore the original database if something went wrong
        if os.path.exists(temp_backup) and not os.path.exists(db_path):
            try:
                shutil.copy2(temp_backup, db_path)
                app.logger.info("Restored original database after failed restore")
            except Exception:
                app.logger.error("Failed to restore original database")
    finally:
        # Delete the restore information file
        if os.path.exists(restore_info_path):
            os.remove(restore_info_path)
            app.logger.info("Removed scheduled restore information file")


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

    # Check for scheduled database restore operations
    with app.app_context():
        check_for_scheduled_restore(app)

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
        if '/delete_file' in request.path or '/delete_pdf' in request.path or '/delete_sql' in request.path:
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

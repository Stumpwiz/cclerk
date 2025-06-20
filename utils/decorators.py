from functools import wraps
from flask import request, jsonify, current_app
from extensions import db


def login_required(f):
    """Decorator to restrict access to logged in users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session, flash, redirect, url_for

        # Check if user is logged in
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated_function


def role_required(required_role):
    """Decorator to restrict access based on the user role."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, flash, redirect, url_for
            from models.user import User

            # Check if user is logged in
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({"error": "Authentication required"}), 401
                flash('Please log in to access this page', 'danger')
                return redirect(url_for('auth.login'))

            # Get user from database
            user = db.session.get(User, session['user_id'])
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('auth.login'))

            # Check if user has the required role
            if user.role != required_role:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('main.index'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def handle_errors(f):
    """Decorator for standardized error handling across all routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Failed to process request",
                "details": str(e)
            }), 500
    return decorated_function

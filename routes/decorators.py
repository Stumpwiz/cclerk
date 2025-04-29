from functools import wraps
from flask import request, jsonify, current_app


def role_required(required_role):
    """Decorator to restrict access based on the user role."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract the role from headers or authenticated user session
            # This would depend on your authentication or role set-up
            user_role = request.headers.get('X-Role', 'user')

            if user_role != required_role:
                return jsonify({'error': 'Unauthorized'}), 403
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

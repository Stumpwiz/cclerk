from functools import wraps
from flask import request, jsonify


def role_required(required_role):
    """Decorator to restrict access based on user role."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract role from headers or authenticated user session
            # This would depend on your authentication or role set-up
            user_role = request.headers.get('X-Role', 'user')

            if user_role != required_role:
                return jsonify({'error': 'Unauthorized'}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator

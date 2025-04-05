# user.py.  A user of this project.

from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import jsonify, request
from extensions import db


# Define the User model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=True, default="user")  # e.g., "admin" or "user"

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def role_required(self):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Extract user role from the request or session (example logic here)
                user_role = request.headers.get("X-Role", "user")  # Replace with actual role fetching logic

                if user_role != self:
                    return jsonify({"error": "Unauthorized"}), 403
                return f(*args, **kwargs)

            return decorated_function

        return decorator

    def __repr__(self):
        return f'<User {self.username}>'

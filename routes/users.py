from flask import Blueprint, jsonify

# Define a blueprint for the "users" feature
users_bp = Blueprint('users', __name__)


@users_bp.route('/get', methods=['GET'])
def get_users():
    # Example route logic
    return jsonify({"message": "This is the users endpoint"})

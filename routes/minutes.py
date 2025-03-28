from flask import Blueprint, jsonify
from .decorators import role_required  # Import your decorator

# Define a blueprint for the "minutes" feature
minutes_bp = Blueprint('minutes', __name__)


@minutes_bp.route('/get', methods=['GET'])
def get_minutes():
    # Example route logic
    return jsonify({"message": "This is the minutes endpoint"})


@minutes_bp.route('/edit', methods=['POST'])
@role_required("admin")
def edit_minutes():
    return jsonify({"message": "Only admins can edit minutes"})

from flask import Blueprint, jsonify

# Define a blueprint for the "rosters" feature
rosters_bp = Blueprint('rosters', __name__)


@rosters_bp.route('/get', methods=['GET'])
def get_rosters():
    # Example route logic
    return jsonify({"message": "This is the rosters endpoint"})

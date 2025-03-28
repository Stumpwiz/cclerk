from flask import Blueprint, jsonify

# Define a blueprint for the "reports" feature
reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/get', methods=['GET'])
def get_reports():
    # Example route logic
    return jsonify({"message": "This is the reports endpoint"})

from flask import Blueprint, jsonify

# Define a blueprint for the "letters" feature
letters_bp = Blueprint('letters', __name__)


@letters_bp.route('/get', methods=['GET'])
def get_letters():
    # Example route logic
    return jsonify({"message": "This is the letters endpoint"})

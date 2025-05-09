from flask import Blueprint, jsonify, request, render_template
from models.office import Office
from models.body import Body
from extensions import db
from routes.decorators import handle_errors, login_required

# Define a blueprint for the "office" feature
office_bp = Blueprint('office', __name__)


@office_bp.route('/get', methods=['GET'])
@handle_errors
@login_required
def get_offices():
    """Get all offices or a specific office by ID"""
    office_id = request.args.get('id')
    body_id = request.args.get('body_id')

    if office_id:
        office = Office.query.get(office_id)
        if office:
            return jsonify({
                "id": office.office_id,
                "title": office.title,
                "precedence": office.office_precedence,
                "body_id": office.office_body_id,
                "body_name": office.body.name if office.body else None
            })
        return jsonify({"error": "Office not found"}), 404

    if body_id:
        offices = Office.query.filter_by(office_body_id=body_id).order_by(Office.office_precedence).all()
    else:
        offices = Office.query.order_by(Office.office_precedence).all()

    return jsonify([{
        "id": office.office_id,
        "title": office.title,
        "precedence": office.office_precedence,
        "body_id": office.office_body_id,
        "body_name": office.body.name if office.body else None
    } for office in offices])




@office_bp.route('/create', methods=['POST'])  # Primary route used by the frontend
@office_bp.route('/add', methods=['POST'])  # Kept for backward compatibility
@handle_errors
@login_required
def add_office():
    """
    Create a new office with a standardized response format.
    The '/create' route is the primary route used by the frontend.
    The '/add' route is kept for backward compatibility.
    """
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.json

    if not data or 'title' not in data or ('body_id' not in data and 'office_body_id' not in data):
        return jsonify({"success": False, "error": "Title and body_id are required"}), 400

    # Get the body_id from either 'body_id' or 'office_body_id' parameter
    body_id = data.get('body_id') or data.get('office_body_id')

    # Verify that the body exists
    body = Body.query.get(body_id)
    if not body:
        return jsonify({"success": False, "error": "Body not found"}), 404

    # Get precedence from either 'precedence' or 'office_precedence' parameter
    precedence = data.get('precedence', data.get('office_precedence', 0))

    new_office = Office(
        title=data['title'],
        office_precedence=precedence,
        office_body_id=body_id
    )

    db.session.add(new_office)
    db.session.commit()

    return jsonify({
        "success": True,
        "id": new_office.office_id,
        "title": new_office.title,
        "precedence": new_office.office_precedence,
        "body_id": new_office.office_body_id,
        "body_name": new_office.body.name
    })


@office_bp.route('/update', methods=['PUT'])
@handle_errors
def update_office():
    """Update an existing office"""
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.json

    if not data or 'id' not in data:
        return jsonify({"error": "Office ID is required"}), 400

    office = Office.query.get(data['id'])
    if not office:
        return jsonify({"error": "Office not found"}), 404

    if 'title' in data:
        office.title = data['title']
    if 'precedence' in data:
        office.office_precedence = data['precedence']
    if 'body_id' in data:
        # Verify that the body exists
        body = Body.query.get(data['body_id'])
        if not body:
            return jsonify({"error": "Body not found"}), 404
        office.office_body_id = data['body_id']

    db.session.commit()

    return jsonify({
        "id": office.office_id,
        "title": office.title,
        "precedence": office.office_precedence,
        "body_id": office.office_body_id,
        "body_name": office.body.name
    })


@office_bp.route('/delete', methods=['DELETE'])
@handle_errors
def delete_office():
    """Delete an office"""
    office_id = request.args.get('id')

    if not office_id:
        return jsonify({"error": "Office ID is required"}), 400

    office = Office.query.get(office_id)
    if not office:
        return jsonify({"error": "Office not found"}), 404

    db.session.delete(office)
    db.session.commit()

    return jsonify({"message": "Office deleted successfully"})


@office_bp.route('/view', methods=['GET'])
@handle_errors
def view_offices():
    """
    This route is for the web interface.
    It renders the office.html template.
    """
    # Render the template
    return render_template("office.html")

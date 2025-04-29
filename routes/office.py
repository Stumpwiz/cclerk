from flask import Blueprint, jsonify, request, render_template
from models.office import Office
from models.body import Body
from extensions import db
from routes.decorators import handle_errors

# Define a blueprint for the "office" feature
office_bp = Blueprint('office', __name__)


@office_bp.route('/get', methods=['GET'])
@handle_errors
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


@office_bp.route('/create', methods=['POST'])
@handle_errors
def create_office():
    """Create a new office"""
    data = request.json

    if not data or 'title' not in data or 'body_id' not in data:
        return jsonify({"error": "Title and body_id are required"}), 400

    # Verify that the body exists
    body = Body.query.get(data['body_id'])
    if not body:
        return jsonify({"error": "Body not found"}), 404

    new_office = Office(
        title=data['title'],
        office_precedence=data.get('precedence'),
        office_body_id=data['body_id']
    )

    db.session.add(new_office)
    db.session.commit()

    return jsonify({
        "id": new_office.office_id,
        "title": new_office.title,
        "precedence": new_office.office_precedence,
        "body_id": new_office.office_body_id,
        "body_name": new_office.body.name
    }), 201


@office_bp.route('/update', methods=['PUT'])
@handle_errors
def update_office():
    """Update an existing office"""
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

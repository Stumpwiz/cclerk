from flask import Blueprint, jsonify, request, render_template
from models.person import Person
from extensions import db
from sqlalchemy.exc import IntegrityError
from utils.decorators import handle_errors, login_required

# Define a blueprint for the "person" feature
person_bp = Blueprint('person', __name__)


@person_bp.route('/get', methods=['GET'])
@handle_errors
@login_required
def get_persons():
    """Get all persons or a specific person by ID"""
    person_id = request.args.get('id')

    if person_id:
        person = db.session.get(Person, person_id)
        if person:
            return jsonify({
                "id": person.person_id,
                "first": person.first,
                "last": person.last,
                "email": person.email,
                "phone": person.phone,
                "apt": person.apt
            })
        return jsonify({"error": "Person not found"}), 404

    persons = Person.query.order_by(Person.first, Person.last).all()
    return jsonify([{
        "id": person.person_id,
        "first": person.first,
        "last": person.last,
        "email": person.email,
        "phone": person.phone,
        "apt": person.apt
    } for person in persons])


@person_bp.route('/add', methods=['POST'])
@handle_errors
@login_required
def add_person():
    """
    Create a new person with a standardized response format.
    This route is for compatibility with the test suite.
    """
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.json

    if not data or 'last' not in data:
        return jsonify({"success": False, "error": "Last name is required"}), 400

    new_person = Person(
        first=data.get('first'),
        last=data['last'],
        email=data.get('email'),
        phone=data.get('phone'),
        apt=data.get('apt')
    )

    db.session.add(new_person)
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "id": new_person.person_id,
            "first": new_person.first,
            "last": new_person.last,
            "email": new_person.email,
            "phone": new_person.phone,
            "apt": new_person.apt
        })
    except IntegrityError as e:
        db.session.rollback()
        if 'uix_person_first_last' in str(e):
            return jsonify({"success": False, "error": "A person with this first and last name already exists"}), 400
        return jsonify({"success": False, "error": "An error occurred while creating the person"}), 400


@person_bp.route('/update', methods=['PUT'])
@handle_errors
def update_person():
    """Update an existing person"""
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.json

    if not data or 'id' not in data:
        return jsonify({"error": "Person ID is required"}), 400

    person = db.session.get(Person, data['id'])
    if not person:
        return jsonify({"error": "Person not found"}), 404

    if 'first' in data:
        person.first = data['first']
    if 'last' in data:
        person.last = data['last']
    if 'email' in data:
        person.email = data['email']
    if 'phone' in data:
        person.phone = data['phone']
    if 'apt' in data:
        person.apt = data['apt']

    try:
        db.session.commit()
        return jsonify({
            "id": person.person_id,
            "first": person.first,
            "last": person.last,
            "email": person.email,
            "phone": person.phone,
            "apt": person.apt
        })
    except IntegrityError as e:
        db.session.rollback()
        if 'uix_person_first_last' in str(e):
            return jsonify({"error": "A person with this first and last name already exists"}), 400
        return jsonify({"error": "An error occurred while updating the person"}), 400


@person_bp.route('/delete', methods=['DELETE'])
@handle_errors
def delete_person():
    """Delete a person"""
    person_id = request.args.get('id')

    if not person_id:
        return jsonify({"error": "Person ID is required"}), 400

    person = db.session.get(Person, person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    # Check if there are any terms associated with this person
    if person.terms:
        return jsonify({
            "error": "Cannot delete person with associated terms",
            "details": f"This person has {len(person.terms)} term(s) associated with them. Please delete or modify these terms first."
        }), 400

    db.session.delete(person)
    db.session.commit()

    return jsonify({"message": "Person deleted successfully"})


@person_bp.route('/view', methods=['GET'])
@handle_errors
def view_persons():
    """
    This route is for the web interface.
    It renders the person.html template.
    """
    # Render the template
    return render_template("person.html")

from flask import Blueprint, jsonify, request, render_template
from models.term import Term
from models.person import Person
from models.office import Office
from extensions import db, csrf
from datetime import datetime
from utils.decorators import handle_errors, login_required

# Define a blueprint for the "term" feature
term_bp = Blueprint('term', __name__)


@term_bp.route('/get', methods=['GET'])
@handle_errors
@login_required
def get_terms():
    """Get all terms, terms by person_id, or terms by office_id"""
    person_id = request.args.get('person_id')
    office_id = request.args.get('office_id')

    if person_id and office_id:
        # Get a specific term by composite key
        term = Term.query.filter_by(term_person_id=person_id, term_office_id=office_id).first()
        if term:
            return jsonify({
                "person_id": term.term_person_id,
                "office_id": term.term_office_id,
                "start": term.start.isoformat() if term.start else None,
                "end": term.end.isoformat() if term.end else None,
                "ordinal": term.ordinal,
                "person_name": f"{term.person.first} {term.person.last}" if term.person else None,
                "body_name": term.office.body.name if term.office and term.office.body else None,
                "office_title": term.office.title if term.office else None
            })
        return jsonify({"error": "Term not found"}), 404

    if person_id:
        # Get all terms for a specific person
        terms = Term.query.filter_by(term_person_id=person_id).join(Person).order_by(Person.first, Person.last).all()
    elif office_id:
        # Get all terms for a specific office
        terms = Term.query.filter_by(term_office_id=office_id).join(Person).order_by(Person.first, Person.last).all()
    else:
        # Get all terms
        terms = Term.query.join(Person).order_by(Person.first, Person.last).all()

    return jsonify([{
        "person_id": term.term_person_id,
        "office_id": term.term_office_id,
        "start": term.start.isoformat() if term.start else None,
        "end": term.end.isoformat() if term.end else None,
        "ordinal": term.ordinal,
        "person_name": f"{term.person.first} {term.person.last}" if term.person else None,
        "body_name": term.office.body.name if term.office and term.office.body else None,
        "office_title": term.office.title if term.office else None
    } for term in terms])


@term_bp.route('/add', methods=['POST'])
@term_bp.route('/create', methods=['POST'])
@handle_errors
@login_required
def add_term():
    """
    Create a new term with a standardized response format.
    This route is for compatibility with the test suite.
    The '/create' route is added for compatibility with the frontend.
    """
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.json

    # Handle both parameter naming conventions (frontend uses person_id, backend uses term_person_id)
    term_person_id = data.get('term_person_id') or data.get('person_id')
    term_office_id = data.get('term_office_id') or data.get('office_id')

    if not data or not term_person_id or not term_office_id:
        return jsonify({"success": False, "error": "Person ID and Office ID are required"}), 400

    # Verify that the person exists
    person = db.session.get(Person, term_person_id)
    if not person:
        return jsonify({"success": False, "error": "Person not found"}), 404

    # Verify that the office exists
    office = db.session.get(Office, term_office_id)
    if not office:
        return jsonify({"success": False, "error": "Office not found"}), 404

    # Check if the term already exists
    existing_term = Term.query.filter_by(
        term_person_id=term_person_id,
        term_office_id=term_office_id
    ).first()

    if existing_term:
        return jsonify({"success": False, "error": "Term already exists for this person and office"}), 400

    # Parse dates if provided
    start_date = None
    end_date = None

    if 'start' in data and data['start']:
        try:
            start_date = datetime.fromisoformat(data['start'])
        except ValueError:
            return jsonify({"success": False, "error": "Invalid start date format. Use ISO format (YYYY-MM-DD)"}), 400

    if 'end' in data and data['end']:
        try:
            end_date = datetime.fromisoformat(data['end'])
        except ValueError:
            return jsonify({"success": False, "error": "Invalid end date format. Use ISO format (YYYY-MM-DD)"}), 400

    new_term = Term(
        term_person_id=term_person_id,
        term_office_id=term_office_id,
        start=start_date,
        end=end_date,
        ordinal=data.get('ordinal')
    )

    db.session.add(new_term)
    db.session.commit()

    return jsonify({
        "success": True,
        "person_id": new_term.term_person_id,
        "office_id": new_term.term_office_id,
        "start": new_term.start.isoformat() if new_term.start else None,
        "end": new_term.end.isoformat() if new_term.end else None,
        "ordinal": new_term.ordinal,
        "person_name": f"{new_term.person.first} {new_term.person.last}",
        "body_name": new_term.office.body.name if new_term.office and new_term.office.body else None,
        "office_title": new_term.office.title
    })


@term_bp.route('/update', methods=['POST'])
@handle_errors
@login_required
def update_term():
    """Update an existing term"""
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.json

    if not data or 'person_id' not in data or 'office_id' not in data:
        return jsonify({"error": "Person ID and Office ID are required"}), 400

    term = Term.query.filter_by(
        term_person_id=data['person_id'],
        term_office_id=data['office_id']
    ).first()

    if not term:
        return jsonify({"error": "Term not found"}), 404

    # Parse dates if provided
    if 'start' in data:
        if data['start']:
            try:
                term.start = datetime.fromisoformat(data['start'])
            except ValueError:
                return jsonify({"error": "Invalid start date format. Use ISO format (YYYY-MM-DD)"}), 400
        else:
            term.start = None

    if 'end' in data:
        if data['end']:
            try:
                term.end = datetime.fromisoformat(data['end'])
            except ValueError:
                return jsonify({"error": "Invalid end date format. Use ISO format (YYYY-MM-DD)"}), 400
        else:
            term.end = None

    if 'ordinal' in data:
        term.ordinal = data['ordinal']

    db.session.commit()

    return jsonify({
        "person_id": term.term_person_id,
        "office_id": term.term_office_id,
        "start": term.start.isoformat() if term.start else None,
        "end": term.end.isoformat() if term.end else None,
        "ordinal": term.ordinal,
        "person_name": f"{term.person.first} {term.person.last}",
        "body_name": term.office.body.name if term.office and term.office.body else None,
        "office_title": term.office.title
    })

@term_bp.route('/delete', methods=['POST'])
@handle_errors
@login_required
def delete_term():
    """Delete a term"""
    # Check if request contains valid JSON data
    if request.is_json:
        data = request.json
        person_id = data.get('person_id')
        office_id = data.get('office_id')
    else:
        person_id = request.args.get('person_id')
        office_id = request.args.get('office_id')

    if not person_id or not office_id:
        return jsonify({"error": "Person ID and Office ID are required"}), 400

    term = Term.query.filter_by(
        term_person_id=person_id,
        term_office_id=office_id
    ).first()

    if not term:
        return jsonify({"error": "Term not found"}), 404

    db.session.delete(term)
    db.session.commit()

    return jsonify({"message": "Term deleted successfully"})


@term_bp.route('/view', methods=['GET'])
@handle_errors
def view_terms():
    """
    This route is for the web interface.
    It renders the term.html template.
    """
    # Render the template
    return render_template("term.html")

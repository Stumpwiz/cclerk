from flask import Blueprint, jsonify, request
from models.term import Term
from models.person import Person
from models.office import Office
from extensions import db
from datetime import datetime

# Define a blueprint for the "term" feature
term_bp = Blueprint('term', __name__)


@term_bp.route('/get', methods=['GET'])
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
                "office_title": term.office.title if term.office else None
            })
        return jsonify({"error": "Term not found"}), 404
    
    if person_id:
        # Get all terms for a specific person
        terms = Term.query.filter_by(term_person_id=person_id).all()
    elif office_id:
        # Get all terms for a specific office
        terms = Term.query.filter_by(term_office_id=office_id).all()
    else:
        # Get all terms
        terms = Term.query.all()
    
    return jsonify([{
        "person_id": term.term_person_id,
        "office_id": term.term_office_id,
        "start": term.start.isoformat() if term.start else None,
        "end": term.end.isoformat() if term.end else None,
        "ordinal": term.ordinal,
        "person_name": f"{term.person.first} {term.person.last}" if term.person else None,
        "office_title": term.office.title if term.office else None
    } for term in terms])


@term_bp.route('/create', methods=['POST'])
def create_term():
    """Create a new term"""
    data = request.json
    
    if not data or 'person_id' not in data or 'office_id' not in data:
        return jsonify({"error": "Person ID and Office ID are required"}), 400
    
    # Verify that the person exists
    person = Person.query.get(data['person_id'])
    if not person:
        return jsonify({"error": "Person not found"}), 404
    
    # Verify that the office exists
    office = Office.query.get(data['office_id'])
    if not office:
        return jsonify({"error": "Office not found"}), 404
    
    # Check if the term already exists
    existing_term = Term.query.filter_by(
        term_person_id=data['person_id'],
        term_office_id=data['office_id']
    ).first()
    
    if existing_term:
        return jsonify({"error": "Term already exists for this person and office"}), 400
    
    # Parse dates if provided
    start_date = None
    end_date = None
    
    if 'start' in data and data['start']:
        try:
            start_date = datetime.fromisoformat(data['start'])
        except ValueError:
            return jsonify({"error": "Invalid start date format. Use ISO format (YYYY-MM-DD)"}), 400
    
    if 'end' in data and data['end']:
        try:
            end_date = datetime.fromisoformat(data['end'])
        except ValueError:
            return jsonify({"error": "Invalid end date format. Use ISO format (YYYY-MM-DD)"}), 400
    
    new_term = Term(
        term_person_id=data['person_id'],
        term_office_id=data['office_id'],
        start=start_date,
        end=end_date,
        ordinal=data.get('ordinal')
    )
    
    db.session.add(new_term)
    db.session.commit()
    
    return jsonify({
        "person_id": new_term.term_person_id,
        "office_id": new_term.term_office_id,
        "start": new_term.start.isoformat() if new_term.start else None,
        "end": new_term.end.isoformat() if new_term.end else None,
        "ordinal": new_term.ordinal,
        "person_name": f"{new_term.person.first} {new_term.person.last}",
        "office_title": new_term.office.title
    }), 201


@term_bp.route('/update', methods=['PUT'])
def update_term():
    """Update an existing term"""
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
        "office_title": term.office.title
    })


@term_bp.route('/delete', methods=['DELETE'])
def delete_term():
    """Delete a term"""
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
from flask import Blueprint, jsonify, request
from models.person import Person
from extensions import db

# Define a blueprint for the "person" feature
person_bp = Blueprint('person', __name__)


@person_bp.route('/get', methods=['GET'])
def get_persons():
    """Get all persons or a specific person by ID"""
    person_id = request.args.get('id')
    
    if person_id:
        person = Person.query.get(person_id)
        if person:
            return jsonify({
                "id": person.person_id,
                "first": person.first,
                "last": person.last,
                "email": person.email,
                "phone": person.phone,
                "apt": person.apt,
                "image": person.person_image
            })
        return jsonify({"error": "Person not found"}), 404
    
    persons = Person.query.order_by(Person.last, Person.first).all()
    return jsonify([{
        "id": person.person_id,
        "first": person.first,
        "last": person.last,
        "email": person.email,
        "phone": person.phone,
        "apt": person.apt,
        "image": person.person_image
    } for person in persons])


@person_bp.route('/create', methods=['POST'])
def create_person():
    """Create a new person"""
    data = request.json
    
    if not data or 'last' not in data:
        return jsonify({"error": "Last name is required"}), 400
    
    new_person = Person(
        first=data.get('first'),
        last=data['last'],
        email=data.get('email'),
        phone=data.get('phone'),
        apt=data.get('apt'),
        person_image=data.get('image')
    )
    
    db.session.add(new_person)
    db.session.commit()
    
    return jsonify({
        "id": new_person.person_id,
        "first": new_person.first,
        "last": new_person.last,
        "email": new_person.email,
        "phone": new_person.phone,
        "apt": new_person.apt,
        "image": new_person.person_image
    }), 201


@person_bp.route('/update', methods=['PUT'])
def update_person():
    """Update an existing person"""
    data = request.json
    
    if not data or 'id' not in data:
        return jsonify({"error": "Person ID is required"}), 400
    
    person = Person.query.get(data['id'])
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
    if 'image' in data:
        person.person_image = data['image']
    
    db.session.commit()
    
    return jsonify({
        "id": person.person_id,
        "first": person.first,
        "last": person.last,
        "email": person.email,
        "phone": person.phone,
        "apt": person.apt,
        "image": person.person_image
    })


@person_bp.route('/delete', methods=['DELETE'])
def delete_person():
    """Delete a person"""
    person_id = request.args.get('id')
    
    if not person_id:
        return jsonify({"error": "Person ID is required"}), 400
    
    person = Person.query.get(person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    
    db.session.delete(person)
    db.session.commit()
    
    return jsonify({"message": "Person deleted successfully"})
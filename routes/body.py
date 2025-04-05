from flask import Blueprint, jsonify, request
from models.body import Body
from extensions import db

# Define a blueprint for the "body" feature
body_bp = Blueprint('body', __name__)


@body_bp.route('/get', methods=['GET'])
def get_bodies():
    """Get all bodies or a specific body by ID"""
    body_id = request.args.get('id')
    
    if body_id:
        body = Body.query.get(body_id)
        if body:
            return jsonify({
                "id": body.body_id,
                "name": body.name,
                "mission": body.mission,
                "image": body.body_image,
                "precedence": body.body_precedence
            })
        return jsonify({"error": "Body not found"}), 404
    
    bodies = Body.query.order_by(Body.body_precedence).all()
    return jsonify([{
        "id": body.body_id,
        "name": body.name,
        "mission": body.mission,
        "image": body.body_image,
        "precedence": body.body_precedence
    } for body in bodies])


@body_bp.route('/create', methods=['POST'])
def create_body():
    """Create a new body"""
    data = request.json
    
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    
    new_body = Body(
        name=data['name'],
        mission=data.get('mission'),
        body_image=data.get('image'),
        body_precedence=data.get('precedence', 0)
    )
    
    db.session.add(new_body)
    db.session.commit()
    
    return jsonify({
        "id": new_body.body_id,
        "name": new_body.name,
        "mission": new_body.mission,
        "image": new_body.body_image,
        "precedence": new_body.body_precedence
    }), 201


@body_bp.route('/update', methods=['PUT'])
def update_body():
    """Update an existing body"""
    data = request.json
    
    if not data or 'id' not in data:
        return jsonify({"error": "Body ID is required"}), 400
    
    body = Body.query.get(data['id'])
    if not body:
        return jsonify({"error": "Body not found"}), 404
    
    if 'name' in data:
        body.name = data['name']
    if 'mission' in data:
        body.mission = data['mission']
    if 'image' in data:
        body.body_image = data['image']
    if 'precedence' in data:
        body.body_precedence = data['precedence']
    
    db.session.commit()
    
    return jsonify({
        "id": body.body_id,
        "name": body.name,
        "mission": body.mission,
        "image": body.body_image,
        "precedence": body.body_precedence
    })


@body_bp.route('/delete', methods=['DELETE'])
def delete_body():
    """Delete a body"""
    body_id = request.args.get('id')
    
    if not body_id:
        return jsonify({"error": "Body ID is required"}), 400
    
    body = Body.query.get(body_id)
    if not body:
        return jsonify({"error": "Body not found"}), 404
    
    db.session.delete(body)
    db.session.commit()
    
    return jsonify({"message": "Body deleted successfully"})
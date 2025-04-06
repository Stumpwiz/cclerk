from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
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
    """
    Create a new body.
    This route handles API requests and returns JSON.
    For web interface, use the create_body_html route.
    """
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
    """
    Update an existing body.
    This route handles API requests and returns JSON.
    For web interface, use the update_body_html route.
    """
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
    """
    Delete a body.
    This route handles API requests and returns JSON.
    For web interface, use the delete_body_html route.
    """
    body_id = request.args.get('id')

    if not body_id:
        return jsonify({"error": "Body ID is required"}), 400

    body = Body.query.get(body_id)
    if not body:
        return jsonify({"error": "Body not found"}), 404

    db.session.delete(body)
    db.session.commit()

    return jsonify({"message": "Body deleted successfully"})


@body_bp.route('/view', methods=['GET'])
def view_bodies():
    """
    This route is for the web interface.
    It renders the body.html template with the body data.
    """
    # Query all bodies ordered by name
    bodies = Body.query.order_by(Body.name).all()

    # Render the template with the bodies data
    return render_template("body.html", bodies=bodies)


@body_bp.route('/create_html', methods=['POST'])
def create_body_html():
    """
    Create a new body from the web interface.
    This route handles form submissions and redirects to the view page.
    """
    name = request.form.get('name')
    mission = request.form.get('mission')
    precedence = request.form.get('precedence')
    image = request.form.get('image')

    if not name:
        flash('Name is required', 'danger')
        return redirect(url_for('body.view_bodies'))

    new_body = Body(
        name=name,
        mission=mission,
        body_image=image,
        body_precedence=float(precedence) if precedence else 0
    )

    db.session.add(new_body)
    db.session.commit()

    flash(f'Body "{name}" created successfully!', 'success')
    return redirect(url_for('body.view_bodies'))


@body_bp.route('/update_html', methods=['POST'])
def update_body_html():
    """
    Update an existing body from the web interface.
    This route handles form submissions and redirects to the view page.
    """
    body_id = request.form.get('id')
    name = request.form.get('name')
    mission = request.form.get('mission')
    precedence = request.form.get('precedence')
    image = request.form.get('image')

    if not body_id:
        flash('Body ID is required', 'danger')
        return redirect(url_for('body.view_bodies'))

    body = Body.query.get(body_id)
    if not body:
        flash('Body not found', 'danger')
        return redirect(url_for('body.view_bodies'))

    body.name = name
    body.mission = mission
    body.body_image = image
    body.body_precedence = float(precedence) if precedence else 0

    db.session.commit()

    flash(f'Body "{name}" updated successfully!', 'success')
    return redirect(url_for('body.view_bodies'))


@body_bp.route('/delete_html', methods=['POST'])
def delete_body_html():
    """
    Delete a body from the web interface.
    This route handles form submissions and redirects to the view page.
    """
    body_id = request.form.get('id')

    if not body_id:
        flash('Body ID is required', 'danger')
        return redirect(url_for('body.view_bodies'))

    body = Body.query.get(body_id)
    if not body:
        flash('Body not found', 'danger')
        return redirect(url_for('body.view_bodies'))

    name = body.name
    db.session.delete(body)
    db.session.commit()

    flash(f'Body "{name}" deleted successfully!', 'success')
    return redirect(url_for('body.view_bodies'))

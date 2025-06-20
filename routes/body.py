from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from models.body import Body
from extensions import db
from forms import CSRFForm
from utils.decorators import handle_errors, login_required

# Define a blueprint for the "body" feature
body_bp = Blueprint('body', __name__)


@body_bp.route('/get', methods=['GET'])
@handle_errors
@login_required
def get_bodies():
    """Get all bodies or a specific body by ID"""
    body_id = request.args.get('id')

    if body_id:
        body = db.session.get(Body, body_id)
        if body:
            return jsonify({
                "id": body.body_id,
                "name": body.name,
                "mission": body.mission,
                "precedence": body.body_precedence
            })
        return jsonify({"error": "Body not found"}), 404

    bodies = Body.query.order_by(Body.body_precedence).all()
    return jsonify([{
        "id": body.body_id,
        "name": body.name,
        "mission": body.mission,
        "precedence": body.body_precedence
    } for body in bodies])




@body_bp.route('/add', methods=['POST'])
@handle_errors
@login_required
def add_body():
    """
    Create a new body with a standardized response format.
    This route is for compatibility with the test suite.
    """
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.json

    if not data or 'name' not in data:
        return jsonify({"success": False, "error": "Name is required"}), 400

    new_body = Body(
        name=data['name'],
        mission=data.get('mission'),
        body_precedence=data.get('precedence', 0)
    )

    db.session.add(new_body)
    db.session.commit()

    return jsonify({
        "success": True,
        "id": new_body.body_id,
        "name": new_body.name,
        "mission": new_body.mission,
        "precedence": new_body.body_precedence
    })


@body_bp.route('/update', methods=['PUT'])
@handle_errors
def update_body():
    """
    Update an existing body.
    This route handles API requests and returns JSON.
    For web interface, use the update_body_html route.
    """
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.json

    if not data or 'id' not in data:
        return jsonify({"error": "Body ID is required"}), 400

    body = db.session.get(Body, data['id'])
    if not body:
        return jsonify({"error": "Body not found"}), 404

    if 'name' in data:
        body.name = data['name']
    if 'mission' in data:
        body.mission = data['mission']
    if 'precedence' in data:
        body.body_precedence = data['precedence']

    db.session.commit()

    return jsonify({
        "id": body.body_id,
        "name": body.name,
        "mission": body.mission,
        "precedence": body.body_precedence
    })


@body_bp.route('/delete', methods=['DELETE'])
@handle_errors
def delete_body():
    """
    Delete a body.
    This route handles API requests and returns JSON.
    For web interface, use the delete_body_html route.
    """
    body_id = request.args.get('id')

    if not body_id:
        return jsonify({"error": "Body ID is required"}), 400

    body = db.session.get(Body, body_id)
    if not body:
        return jsonify({"error": "Body not found"}), 404

    # Check if there are any offices associated with this body
    from models.office import Office
    offices = Office.query.filter_by(office_body_id=body.body_id).all()
    if offices:
        return jsonify({
            "error": "Cannot delete body with associated offices",
            "details": f"This body has {len(offices)} office(s) associated with it. Please delete or reassign these offices first."
        }), 400

    db.session.delete(body)
    db.session.commit()

    return jsonify({"message": "Body deleted successfully"})


@body_bp.route('/view', methods=['GET'])
@handle_errors
def view_bodies():
    """
    This route is for the web interface.
    It renders the body.html template with the body data.
    """
    # Query all bodies ordered by name
    bodies = Body.query.order_by(Body.name).all()

    # Create a CSRF form
    form = CSRFForm()

    # Render the template with the "bodies" data and the form
    return render_template("body.html", bodies=bodies, form=form)


@body_bp.route('/create_html', methods=['POST'])
@handle_errors
def create_body_html():
    """
    Create a new body from the web interface.
    This route handles form submissions and redirects to the view page.
    """
    name = request.form.get('name')
    mission = request.form.get('mission')
    precedence = request.form.get('precedence')

    if not name:
        flash('Name is required', 'danger')
        return redirect(url_for('body.view_bodies'))

    new_body = Body(
        name=name,
        mission=mission,
        body_precedence=float(precedence) if precedence else 0
    )

    db.session.add(new_body)
    db.session.commit()

    flash(f'Body "{name}" created successfully!', 'success')
    return redirect(url_for('body.view_bodies'))


@body_bp.route('/update_html', methods=['POST'])
@handle_errors
def update_body_html():
    """
    Update an existing body from the web interface.
    This route handles form submissions and redirects to the view page.
    """
    body_id = request.form.get('id')
    name = request.form.get('name')
    mission = request.form.get('mission')
    precedence = request.form.get('precedence')

    if not body_id:
        flash('Body ID is required', 'danger')
        return redirect(url_for('body.view_bodies'))

    body = db.session.get(Body, body_id)
    if not body:
        flash('Body not found', 'danger')
        return redirect(url_for('body.view_bodies'))

    body.name = name
    body.mission = mission
    body.body_precedence = float(precedence) if precedence else 0

    db.session.commit()

    flash(f'Body "{name}" updated successfully!', 'success')
    return redirect(url_for('body.view_bodies'))


@body_bp.route('/delete_html', methods=['POST'])
@handle_errors
def delete_body_html():
    """
    Delete a body from the web interface.
    This route handles form submissions and redirects to the view page.
    """
    body_id = request.form.get('id')

    if not body_id:
        flash('Body ID is required', 'danger')
        return redirect(url_for('body.view_bodies'))

    body = db.session.get(Body, body_id)
    if not body:
        flash('Body not found', 'danger')
        return redirect(url_for('body.view_bodies'))

    # Check if there are any offices associated with this body
    from models.office import Office
    offices = Office.query.filter_by(office_body_id=body.body_id).all()
    if offices:
        flash(f'Cannot delete body "{body.name}" because it has {len(offices)} office(s) associated with it. Please delete or reassign these offices first.', 'danger')
        return redirect(url_for('body.view_bodies'))

    name = body.name
    db.session.delete(body)
    db.session.commit()

    flash(f'Body "{name}" deleted successfully!', 'success')
    return redirect(url_for('body.view_bodies'))

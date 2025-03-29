from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models.letters import LetterTemplate

# Define a blueprint for the "letters" feature
letters_bp = Blueprint('letters', __name__)


@letters_bp.route('/get', methods=['GET'])
def get_letters():
    """
    This route handles both the API endpoint and the web interface.
    When accessed via /api/letters/get, it returns JSON.
    When accessed via a web browser, it renders the template.
    """
    # Return JSON for API requests (when accessed via /api/letters/get)
    return jsonify({"message": "This is the letters endpoint"})


@letters_bp.route('/', methods=['GET'])
def get_letters_html():
    """
    This route is for the web interface.
    It renders the letters.html template with the letter template data.
    """
    # Get the letter template from the database
    template = LetterTemplate.get_singleton()

    # Render the template with the letter template data
    return render_template("letters.html", template=template)


@letters_bp.route('/update_template', methods=['POST'])
def update_template():
    # Get the form data
    header = request.form.get('header')
    body = request.form.get('body')

    # Get the existing template
    template = LetterTemplate.get_singleton()

    if template:
        # Update the template
        template.header = header
        template.body = body
        db.session.commit()
        flash('Template updated successfully!', 'success')
    else:
        flash('No template found to update.', 'danger')

    return redirect(url_for('letters.get_letters'))


@letters_bp.route('/create_template', methods=['POST'])
def create_template():
    # Check if a template already exists
    if not LetterTemplate.can_add_record():
        flash('A template already exists. Please use the edit function instead.', 'warning')
        return redirect(url_for('letters.get_letters'))

    # Get the form data
    header = request.form.get('header')
    body = request.form.get('body')

    # Create a new template
    template = LetterTemplate(header=header, body=body)
    db.session.add(template)
    db.session.commit()

    flash('Template created successfully!', 'success')
    return redirect(url_for('letters.get_letters'))


@letters_bp.route('/generate_letter', methods=['POST'])
def generate_letter():
    # Get the form data
    recipient = request.form.get('recipient')
    subject = request.form.get('subject')
    content = request.form.get('content')

    # Get the template
    template = LetterTemplate.get_singleton()

    if not template:
        flash('No template found. Please create a template first.', 'danger')
        return redirect(url_for('letters.get_letters'))

    # In a real application, you would generate the letter here
    # For now, we'll just return a success message
    flash(f'Letter to {recipient} about "{subject}" generated successfully!', 'success')
    return redirect(url_for('letters.get_letters'))

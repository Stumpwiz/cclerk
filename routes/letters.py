from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import os
import subprocess
import re
from extensions import db
from models.letters import LetterTemplate
from forms import CSRFForm
from routes.decorators import handle_errors


def sanitize_latex(content):
    """
    Sanitize LaTeX content to ensure it's properly formatted and doesn't contain problematic characters.
    """
    # Replace problematic characters with their LaTeX equivalents
    replacements = {
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
        '\\': '\\textbackslash{}',  # This needs to be handled carefully
    }

    # Don't replace characters that are already escaped
    for char, replacement in replacements.items():
        if char != '\\':  # Skip backslash as it's special
            # Replace the character only if it's not preceded by a backslash
            content = re.sub(r'(?<!\\)' + re.escape(char), replacement, content)

    # Ensure proper line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    return content


# Define a blueprint for the "letters" feature
letters_bp = Blueprint('letters', __name__)


@letters_bp.route('/', methods=['GET'])
@handle_errors
def get_letters_html():
    """
    This route is for the web interface.
    It renders the letters.html template with the letter template data.
    """
    # Get the letter template from the database
    template = LetterTemplate.get_singleton()

    # Get the list of PDF files in the files_letters directory
    files_letters_dir = os.path.join(current_app.root_path, "files_letters")
    pdf_files = []

    if os.path.exists(files_letters_dir):
        # Get all PDF files and sort them alphabetically
        pdf_files = [f for f in os.listdir(files_letters_dir) if f.endswith('.pdf')]
        pdf_files.sort()

    # Create a CSRF form
    form = CSRFForm()

    # Render the template with the letter template data and PDF files
    # No most_recent_pdf is passed to ensure no file is selected by default
    return render_template("letters.html", template=template, pdf_files=pdf_files, form=form)


@letters_bp.route('/update_template', methods=['POST'])
@handle_errors
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

    return redirect(url_for('letters.get_letters_html'))


@letters_bp.route('/create_template', methods=['POST'])
@handle_errors
def create_template():
    # Check if a template already exists
    if not LetterTemplate.can_add_record():
        flash('A template already exists. Please use the edit function instead.', 'warning')
        return redirect(url_for('letters.get_letters_html'))

    # Get the form data
    header = request.form.get('header')
    body = request.form.get('body')

    # Create a new template
    template = LetterTemplate(header=header, body=body)
    db.session.add(template)
    db.session.commit()

    flash('Template created successfully!', 'success')
    return redirect(url_for('letters.get_letters_html'))


@letters_bp.route('/view_pdf', methods=['POST'])
@handle_errors
def view_pdf():
    """
    View the selected PDF file directly in the browser.
    """
    pdf_file = request.form.get('pdf_file')
    if not pdf_file:
        flash('No PDF file selected.', 'danger')
        return redirect(url_for('letters.get_letters_html'))

    files_letters_dir = os.path.join(current_app.root_path, "files_letters")
    pdf_path = os.path.join(files_letters_dir, pdf_file)

    if not os.path.exists(pdf_path):
        flash(f'PDF file {pdf_file} not found.', 'danger')
        return redirect(url_for('letters.get_letters_html'))

    # Serve the PDF file directly to the browser
    try:
        from flask import send_file
        return send_file(pdf_path, mimetype='application/pdf')
    except Exception as e:
        flash(f'Error opening PDF: {e}', 'danger')
        return redirect(url_for('letters.get_letters_html'))


@letters_bp.route('/delete_pdf', methods=['POST'])
@handle_errors
def delete_pdf():
    """
    Delete the selected PDF file.
    """
    pdf_file = request.form.get('pdf_file')
    if not pdf_file:
        flash('No PDF file selected.', 'danger')
        return redirect(url_for('letters.get_letters_html'))

    files_letters_dir = os.path.join(current_app.root_path, "files_letters")
    pdf_path = os.path.join(files_letters_dir, pdf_file)

    if not os.path.exists(pdf_path):
        flash(f'PDF file {pdf_file} not found.', 'danger')
        return redirect(url_for('letters.get_letters_html'))

    # Delete the PDF file
    try:
        os.remove(pdf_path)
        flash(f'Deleted {pdf_file}.', 'success')
    except Exception as e:
        flash(f'Error deleting PDF: {e}', 'danger')

    return redirect(url_for('letters.get_letters_html'))


@letters_bp.route('/generate_letter', methods=['POST'])
@handle_errors
def generate_letter():
    # Get the form data
    recipient = request.form.get('recipient')
    salutation = request.form.get('salutation')
    apartment = request.form.get('apartment')

    # Get the template
    template = LetterTemplate.get_singleton()

    if not template:
        return {'success': False, 'error': 'No template found. Please create a template first.'}

    # Extract the last name from the recipient field (last word)
    last_name = recipient.split()[-1]

    # Sanitize the input fields to ensure they don't contain problematic LaTeX characters
    recipient_safe = sanitize_latex(recipient)
    salutation_safe = sanitize_latex(salutation)
    apartment_safe = sanitize_latex(apartment)

    # Create the LaTeX commands for the input fields
    recipient_command = f"\\newcommand{{\\names}}{{{recipient_safe}}}"
    salutation_command = f"\\newcommand{{\\salutation}}{{{salutation_safe}}}"
    apartment_command = f"\\newcommand{{\\apartment}}{{{apartment_safe}}}"

    # Sanitize the template header and body
    header_safe = re.sub(r"(\r\n|\r|\n)+", "\n", template.header.strip())
    body_safe = re.sub(r"(\r\n|\r|\n)+", "\n", template.body.strip())

    # Combine the header, commands, and body into a complete LaTeX document
    tex_content = f"{header_safe}\n{recipient_command}\n{salutation_command}\n{apartment_command}\n{body_safe}"

    # Use the dedicated files_letters directory
    # This avoids creating and cleaning up temporary directories for each letter generation
    files_letters_dir = os.path.join(current_app.root_path, "files_letters")
    if not os.path.exists(files_letters_dir):
        os.makedirs(files_letters_dir, exist_ok=True)
        # print(f"Created files_letters directory: {files_letters_dir}")

    # Path to the final PDF file
    final_pdf_path = os.path.join(files_letters_dir, f"{last_name}.pdf")

    try:
        # Create the .tex file
        tex_file_path = os.path.join(files_letters_dir, f"{last_name}.tex")
        with open(tex_file_path, 'w', encoding='utf-8') as tex_file:
            tex_file.write(tex_content)

        # Path to the output PDF file
        temp_pdf_path = os.path.join(files_letters_dir, f"{last_name}.pdf")

        try:
            # Use xelatex from the system PATH instead of hard-coding the path
            # print(f"Running xelatex...")
            result = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-output-directory", files_letters_dir, tex_file_path],
                cwd=files_letters_dir,
                capture_output=True,
                text=True
            )

            # Check if the PDF was generated
            if os.path.exists(temp_pdf_path):
                # print(f"PDF file generated successfully.")
                pass
            else:
                current_app.logger.error("PDF file not generated. Check LaTeX logs for errors.")
                if result.returncode != 0:
                    current_app.logger.error(f"xelatex failed with return code: {result.returncode}")
                    # Extract error messages from the output
                    if "! " in result.stdout:
                        error_lines = [line for line in result.stdout.split('\n') if "! " in line]
                        for error_line in error_lines:
                            current_app.logger.error(f"LaTeX error: {error_line.strip()}")

            # Now check if we have a PDF file
            if os.path.exists(temp_pdf_path):

                # Clean up LaTeX auxiliary files
                # print("Cleaning up LaTeX auxiliary files...")
                # the .tex file is no longer needed, so it can be deleted as well.
                aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk',
                                  '.synctex.gz', '.dvi', '.tex']

                # Get all files in the files_letters directory
                for file in os.listdir(files_letters_dir):
                    file_path = os.path.join(files_letters_dir, file)
                    # Check if the file is a LaTeX auxiliary file
                    if os.path.isfile(file_path) and any(file.endswith(ext) for ext in aux_extensions):
                        try:
                            os.remove(file_path)
                        except Exception as del_error:
                            current_app.logger.error(f"Error deleting auxiliary file {file}: {del_error}")

                # If we reach here, the PDF was generated successfully
                return {'success': True, 'filename': f"{last_name}.pdf"}
            else:
                # Check for log files that might contain error information
                log_files = [f for f in os.listdir(files_letters_dir) if f.endswith('.log')]
                for log_file in log_files:
                    log_path = os.path.join(files_letters_dir, log_file)
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='replace') as log:
                            log_content = log.read()
                            # Look for common LaTeX errors in the log file
                            if "! LaTeX Error:" in log_content:
                                error_lines = [line for line in log_content.split('\n') if "! LaTeX Error:" in line]
                                for error_line in error_lines:
                                    current_app.logger.error(f"Found LaTeX error: {error_line}")
                    except Exception:
                        pass

                return {'success': False, 'error': 'Failed to generate PDF. Please check the LaTeX template and server logs for more information.'}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': f'Error generating PDF: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {e}'}
        # No need to clean up the files_letters directory as it's a permanent directory
        # The LaTeX files will be overwritten on later letter generations

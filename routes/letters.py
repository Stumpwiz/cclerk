from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
import os
import subprocess
import shutil
import re
from extensions import db
from models.letters import LetterTemplate


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

    # Get the list of PDF files in the files_letters directory
    files_letters_dir = os.path.join(current_app.root_path, "files_letters")
    pdf_files = []

    if os.path.exists(files_letters_dir):
        # Get all PDF files and sort them alphabetically
        pdf_files = [f for f in os.listdir(files_letters_dir) if f.endswith('.pdf')]
        pdf_files.sort()

    # Render the template with the letter template data and PDF files
    # No most_recent_pdf is passed to ensure no file is selected by default
    return render_template("letters.html", template=template, pdf_files=pdf_files)


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

    return redirect(url_for('letters.get_letters_html'))


@letters_bp.route('/create_template', methods=['POST'])
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
def generate_letter():
    # Get the form data
    recipient = request.form.get('recipient')
    salutation = request.form.get('salutation')
    apartment = request.form.get('apartment')

    # Get the template
    template = LetterTemplate.get_singleton()

    if not template:
        flash('No template found. Please create a template first.', 'danger')
        return redirect(url_for('letters.get_letters_html'))

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
        print(f"Created files_letters directory: {files_letters_dir}")

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
            # Run xelatex to generate the PDF
            xelatex_path = r"D:\texlive\texlive\2024\bin\windows\xelatex.exe"

            # First run of xelatex
            print(f"Running first xelatex pass...")
            try:
                result1 = subprocess.run(
                    [xelatex_path, "-interaction=nonstopmode", "-output-directory", files_letters_dir, tex_file_path],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=files_letters_dir)
                print(f"First xelatex run completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"First xelatex run failed with return code: {e.returncode}")
                # Only log errors in case of failure
                if "! " in e.stdout.decode('utf-8', errors='replace'):
                    error_lines = [line for line in e.stdout.decode('utf-8', errors='replace').split('\n') if
                                   "! " in line]
                    for error_line in error_lines:
                        print(f"LaTeX error: {error_line.strip()}")
                # Continue with the second run even if the first run fails
                print("Continuing with second xelatex run despite first run failure")

            # Second run of xelatex to resolve references
            print(f"Running second xelatex pass...")
            try:
                result2 = subprocess.run(
                    [xelatex_path, "-interaction=nonstopmode", "-output-directory", files_letters_dir, tex_file_path],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=files_letters_dir)
                print(f"Second xelatex run completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Second xelatex run failed with return code: {e.returncode}")
                # Only log errors in case of failure
                if "! " in e.stdout.decode('utf-8', errors='replace'):
                    error_lines = [line for line in e.stdout.decode('utf-8', errors='replace').split('\n') if
                                   "! " in line]
                    for error_line in error_lines:
                        print(f"LaTeX error: {error_line.strip()}")
                # Continue even if the second run fails
                print("Continuing despite second xelatex run failure")

            # Check if the PDF was generated
            if os.path.exists(temp_pdf_path):
                print(f"PDF file generated successfully.")
            else:
                print(f"Expected PDF file not found. Looking for alternatives...")
                # If not found, look for any PDF file in the files_letters directory
                pdf_files = [f for f in os.listdir(files_letters_dir) if f.endswith('.pdf')]
                if pdf_files:
                    # Use the first PDF file found
                    temp_pdf_path = os.path.join(files_letters_dir, pdf_files[0])
                    print(f"Using alternative PDF file: {os.path.basename(temp_pdf_path)}")
                else:
                    print("No PDF files found in the files_letters directory")

                    # Check for log files that might contain error information
                    log_files = [f for f in os.listdir(files_letters_dir) if f.endswith('.log')]
                    for log_file in log_files:
                        log_path = os.path.join(files_letters_dir, log_file)
                        try:
                            with open(log_path, 'r', encoding='utf-8', errors='replace') as log:
                                log_content = log.read()
                                # Look for LaTeX errors in the log file
                                if "! " in log_content:
                                    error_lines = [line for line in log_content.split('\n') if "! " in line]
                                    for error_line in error_lines:
                                        print(f"LaTeX error in log: {error_line.strip()}")
                        except Exception as log_error:
                            print(f"Error reading log file: {log_error}")

                    # Try running pdflatex as an alternative
                    try:
                        print("Trying pdflatex as an alternative...")
                        pdflatex_path = r"D:\texlive\texlive\2024\bin\windows\pdflatex.exe"
                        if os.path.exists(pdflatex_path):
                            subprocess.run(
                                [pdflatex_path, "-interaction=nonstopmode", "-output-directory", files_letters_dir,
                                 tex_file_path],
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=files_letters_dir)

                            # Check again for PDF files
                            pdf_files = [f for f in os.listdir(files_letters_dir) if f.endswith('.pdf')]
                            if pdf_files:
                                temp_pdf_path = os.path.join(files_letters_dir, pdf_files[0])
                                print(f"PDF generated using pdflatex.")
                        else:
                            print(f"pdflatex not found at {pdflatex_path}")
                    except Exception as pdf_error:
                        print(f"Error running pdflatex: {pdf_error}")

            # Now check again if we have a PDF file to copy
            if os.path.exists(temp_pdf_path):
                # Check if the PDF file is valid (not empty)
                temp_pdf_size = os.path.getsize(temp_pdf_path)
                if temp_pdf_size == 0:
                    print("Warning: PDF file is empty (0 bytes)")

                # Ensure the destination directory exists
                os.makedirs(os.path.dirname(final_pdf_path), exist_ok=True)

                # Copy the PDF to the permanent location
                print(f"Copying PDF to {os.path.basename(final_pdf_path)}...")
                try:
                    shutil.copy2(temp_pdf_path, final_pdf_path)
                    if os.path.exists(final_pdf_path):
                        print(f"PDF file successfully copied.")
                    else:
                        print(f"Failed to copy PDF file. Trying alternative methods...")
                        # Try an alternative copy method
                        try:
                            shutil.copyfile(temp_pdf_path, final_pdf_path)
                            if os.path.exists(final_pdf_path):
                                print(f"PDF file copied using alternative method.")
                        except Exception as copy_error:
                            print(f"Alternative copy method failed: {copy_error}")

                            # Try a third copy method using raw file operations
                            try:
                                with open(temp_pdf_path, 'rb') as src_file, open(final_pdf_path, 'wb') as dst_file:
                                    dst_file.write(src_file.read())
                                if os.path.exists(final_pdf_path):
                                    print(f"PDF file copied using raw file operations.")
                            except Exception as raw_copy_error:
                                print(f"All copy methods failed: {raw_copy_error}")
                except Exception as copy_error:
                    print(f"Copy operation failed: {copy_error}")
                    # Try alternative copy methods
                    try:
                        shutil.copyfile(temp_pdf_path, final_pdf_path)
                        if os.path.exists(final_pdf_path):
                            print(f"PDF file copied using alternative method.")
                    except Exception as alt_copy_error:
                        print(f"All copy methods failed: {alt_copy_error}")

                # Success message without opening the PDF
                flash(
                    f'Letter for {recipient} generated successfully! Use the buttons above to view, print, or delete the PDF.',
                    'success')

                # Clean up LaTeX auxiliary files as well as the generated .tex file
                try:
                    print("Cleaning up LaTeX auxiliary files...")
                    # List of LaTeX auxiliary file extensions to delete
                    # aux_extensions = ['.tex', '.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk',
                    #                   '.synctex.gz', '.dvi']
                    aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk',
                                      '.synctex.gz', '.dvi']
                    base_name = os.path.splitext(os.path.basename(tex_file_path))[0]

                    # Get all files in the files_letters directory
                    for file in os.listdir(files_letters_dir):
                        file_path = os.path.join(files_letters_dir, file)
                        # Check if the file is a LaTeX auxiliary file
                        if os.path.isfile(file_path) and any(file.endswith(ext) for ext in aux_extensions):
                            try:
                                os.remove(file_path)
                                print(f"Deleted auxiliary file: {file}")
                            except Exception as del_error:
                                print(f"Error deleting auxiliary file {file}: {del_error}")
                except Exception as cleanup_error:
                    print(f"Error during cleanup of LaTeX auxiliary files: {cleanup_error}")
            else:
                print("No PDF file found to copy. Checking for error information...")

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
                                    print(f"Found LaTeX error: {error_line}")
                    except Exception as log_error:
                        print(f"Error reading log file: {log_error}")

                flash('Failed to generate PDF. Please check the LaTeX template and server logs for more information.',
                      'danger')
        except subprocess.CalledProcessError as e:
            flash(f'Error generating PDF: {e}', 'danger')
        except Exception as e:
            flash(f'Unexpected error: {e}', 'danger')
    except Exception as e:
        flash(f'Unexpected error: {e}', 'danger')
        # No need to clean up the files_letters directory as it's a permanent directory
        # The LaTeX files will be overwritten on later letter generations

    return redirect(url_for('letters.get_letters_html'))

from flask import Blueprint, render_template, redirect, url_for, session, send_from_directory, jsonify, request, flash, \
    current_app
import os
import subprocess
from extensions import db, csrf
from utils.file_handlers import get_file_path, validate_file_exists, serve_file, check_directory_for_files
from forms import CSRFForm
from routes.decorators import handle_errors

# Define a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
@handle_errors
def index():
    # Redirect to log in if the user is not authenticated
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    # Get the list of PDF files from the reports directory
    pdf_files = []
    # Check the reports directory
    pdfs_dir = os.path.join(current_app.root_path, current_app.config['REPORTS_DIR'])
    if os.path.exists(pdfs_dir):
        for file in os.listdir(pdfs_dir):
            if file.endswith(".pdf"):
                pdf_files.append(file)

    # Create a CSRF form
    form = CSRFForm()

    return render_template("home.html", items=[], pdf_files=pdf_files, form=form)


@main_bp.route("/view_file", methods=["POST"])
@handle_errors
def view_file():
    try:
        # Check if request contains valid JSON data
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400

        filename = request.json.get("filename")
        if not filename:
            return jsonify({"success": False, "error": "Filename is required"}), 400

        valid, result = validate_file_exists(filename)

        if not valid:
            return jsonify({"success": False, "error": result}), 400

        file_path = result
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext == '.pdf':
            # Return a URL for the client to open the PDF in a new browser tab
            file_url = url_for('main.serve_pdf', filename=filename)
            return jsonify({"success": True, "file_url": file_url})


        elif file_ext == '.txt':
            # For now, still open text files with the default application
            subprocess.Popen(["cmd", "/c", "start", "", file_path], shell=True)
            return jsonify({"success": True})

        else:
            return jsonify({"success": False, "error": f"Unsupported file type: {file_ext}"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route("/serve_pdf/<filename>")
@handle_errors
def serve_pdf(filename):
    """
    Serve a PDF file directly to the browser.
    """
    valid, result = validate_file_exists(filename)

    if not valid:
        flash(result, 'danger')
        return redirect(url_for('main.index'))

    try:
        return serve_file(result, 'application/pdf')
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('main.index'))


@main_bp.route("/view_pdf", methods=["POST"])
@handle_errors
def view_pdf():
    """
    View the selected PDF file directly in the browser.
    """
    # Check if the reports directory exists and has PDF files
    pdfs_dir = os.path.join(current_app.root_path, current_app.config['REPORTS_DIR'])
    success, result = check_directory_for_files(
        pdfs_dir, 
        '.pdf', 
        f'No PDF files found. The {current_app.config["REPORTS_DIR"]} directory does not exist.'
    )

    if not success:
        flash(result, 'info')
        return redirect(url_for('main.index'))

    pdf_files = result

    pdf_file = request.form.get('pdf_file')
    if not pdf_file:
        flash('No PDF file selected.', 'danger')
        return redirect(url_for('main.index'))

    # Check if the requested file is actually in the list of PDF files in the directory
    if pdf_file not in pdf_files:
        flash(f'PDF file {pdf_file} is not in the {current_app.config["REPORTS_DIR"]} directory.', 'danger')
        return redirect(url_for('main.index'))

    valid, result = validate_file_exists(pdf_file)
    if not valid:
        flash(result, 'danger')
        return redirect(url_for('main.index'))

    # Serve the PDF file directly to the browser
    try:
        return serve_file(result, 'application/pdf')
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('main.index'))



@main_bp.route("/delete_file", methods=["POST"])
@handle_errors
def delete_file():
    try:
        # Check if the Content-Type header indicates JSON
        content_type = request.headers.get('Content-Type', '')
        is_json_content = 'application/json' in content_type

        # Try to get the filename from different sources based on content type
        filename = None
        if is_json_content and request.is_json:
            # Get filename from JSON body
            filename = request.json.get("filename")
        elif request.form:
            # Get filename from form data
            filename = request.form.get("filename")
        elif request.data:
            # Try to parse the raw data as JSON
            try:
                data = json.loads(request.data)
                filename = data.get("filename")
            except:
                pass

        if not filename:
            return jsonify({"success": False, "error": "Filename is required"}), 400

        valid, result = validate_file_exists(filename)

        if not valid:
            return jsonify({"success": False, "error": result}), 400

        file_path = result

        # Delete the file
        os.remove(file_path)
        return jsonify({"success": True, "message": f"File {filename} deleted successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@main_bp.route("/favicon.ico")
@handle_errors
def favicon():
    return send_from_directory(
        "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )

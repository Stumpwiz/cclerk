from flask import Blueprint, render_template, redirect, url_for, session, send_from_directory, jsonify, request, flash, \
    current_app
import os
import subprocess
import datetime
import time
import shutil
from extensions import db
from utils.file_handlers import get_file_path, validate_file_exists, serve_file, check_directory_for_files
from forms import CSRFForm

# Database restoration helper functions
def backup_current_database(db_path, temp_backup):
    """
    Create a backup of the current database.
    """
    if os.path.exists(db_path):
        if os.path.exists(temp_backup):
            os.remove(temp_backup)
        shutil.copy2(db_path, temp_backup)

def create_empty_database(temp_new_db):
    """
    Create a new empty database file.
    """
    if os.path.exists(temp_new_db):
        os.remove(temp_new_db)
    open(temp_new_db, 'a').close()

def restore_from_sql(temp_new_db, sql_path):
    """
    Restore from the SQL file to the new database.
    """
    command = f"sqlite3 {temp_new_db} < {sql_path}"
    # On Windows, we need to use shell=True to handle the redirection
    subprocess.run(command, shell=True, check=True)

def replace_database(db_path, temp_new_db):
    """
    Replace the current database with the new one.
    """
    # First try to remove the current database
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            break
        except PermissionError:
            if attempt < max_attempts - 1:
                # Wait a bit and try again
                time.sleep(0.5)
            else:
                raise

    # Now move the new database to the correct location
    shutil.move(temp_new_db, db_path)

def cleanup_backup(temp_backup):
    """
    Clean up the temporary backup file.
    """
    if os.path.exists(temp_backup):
        try:
            os.remove(temp_backup)
        except PermissionError:
            # If we can't remove the backup, that's okay
            pass

def restore_backup_on_error(temp_backup, db_path):
    """
    Restore the original database from backup in case of error.
    """
    if os.path.exists(temp_backup) and not os.path.exists(db_path):
        try:
            shutil.copy2(temp_backup, db_path)
        except Exception:
            # If we can't restore the backup, there's nothing we can do
            pass

# Define a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    # Redirect to log in if the user is not authenticated
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    # Get the list of backup files
    backup_files = []
    backup_dir = os.path.join(current_app.root_path, current_app.config['BACKUP_DIR'])
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.startswith("backup") and file.endswith(".sql"):
                backup_files.append(file)

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

    return render_template("home.html", items=[], backup_files=backup_files, pdf_files=pdf_files, form=form)

@main_bp.route("/backup", methods=["POST"])
def backup_database():
    # Create the timestamp for the backup filename exactly as specified
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
    backup_filename = f"backup{timestamp}.sql"

    # Create the backup directory if it doesn't exist
    backup_dir = os.path.join(current_app.root_path, current_app.config['BACKUP_DIR'])
    os.makedirs(backup_dir, exist_ok=True)

    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        # Execute the SQLite backup command
        db_path = os.path.join(current_app.root_path, current_app.config['DB_PATH'])
        command = f"sqlite3 {db_path} .dump > {backup_path}"

        # On Windows, we need to use shell=True to handle the redirection
        subprocess.run(command, shell=True, check=True)

        return jsonify({"success": True, "filename": backup_filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route("/view_file", methods=["POST"])
def view_file():
    try:
        filename = request.json.get("filename")
        valid, result = validate_file_exists(filename)

        if not valid:
            return jsonify({"success": False, "error": result}), 400

        file_path = result
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext == '.pdf':
            # Return a URL for the client to open the PDF in a new browser tab
            file_url = url_for('main.serve_pdf', filename=filename)
            return jsonify({"success": True, "file_url": file_url})

        elif file_ext == '.sql':
            # Return a URL for the client to open the SQL file in a new browser tab
            file_url = url_for('main.serve_sql', filename=filename)
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

@main_bp.route("/serve_sql/<filename>")
def serve_sql(filename):
    """
    Serve an SQL file directly to the browser as a text file.
    """
    valid, result = validate_file_exists(filename)

    if not valid:
        flash(result, 'danger')
        return redirect(url_for('main.index'))

    try:
        return serve_file(result, 'text/plain')
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('main.index'))

@main_bp.route("/view_pdf", methods=["POST"])
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

@main_bp.route("/view_sql", methods=["POST"])
def view_sql():
    """
    View the selected SQL file directly in the browser as a text file.
    """
    # Check if the backup directory exists and has SQL files
    backup_dir = os.path.join(current_app.root_path, current_app.config['BACKUP_DIR'])
    success, result = check_directory_for_files(
        backup_dir, 
        '.sql', 
        f'No SQL files found. The {current_app.config["BACKUP_DIR"]} directory does not exist.'
    )

    if not success:
        flash(result, 'info')
        return redirect(url_for('main.index'))

    sql_files = result

    sql_file = request.form.get('sql_file')
    if not sql_file:
        flash('No SQL file selected.', 'danger')
        return redirect(url_for('main.index'))

    valid, result = validate_file_exists(sql_file)
    if not valid:
        flash(result, 'danger')
        return redirect(url_for('main.index'))

    # Serve the SQL file directly to the browser as a text file
    try:
        return serve_file(result, 'text/plain')
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('main.index'))

@main_bp.route("/restore", methods=["POST"])
def restore_database():
    """
    Restore the database from a selected SQL backup file.
    """
    # Get the selected SQL file from the request
    sql_file = request.json.get("filename")
    valid, result = validate_file_exists(sql_file)

    if not valid:
        return jsonify({"success": False, "error": result}), 400

    sql_path = result

    # Database path
    db_path = os.path.join(current_app.root_path, current_app.config['DB_PATH'])
    temp_backup = f"{db_path}.bak"
    temp_new_db = f"{db_path}.new"

    try:
        # Close all database connections
        db.engine.dispose()

        # Step 1: Create a new empty database file
        create_empty_database(temp_new_db)

        # Step 2: Restore from the SQL file to the new database
        restore_from_sql(temp_new_db, sql_path)

        # Step 3: Create a backup of the current database
        backup_current_database(db_path, temp_backup)

        # Step 4: Replace the current database with the new one
        replace_database(db_path, temp_new_db)

        # Step 5: Clean up the temporary backup
        cleanup_backup(temp_backup)

        return jsonify({"success": True, "message": f"Database restored successfully from {sql_file}"})
    except Exception as e:
        # If there was an error, try to restore the original database
        restore_backup_on_error(temp_backup, db_path)

        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route("/delete_file", methods=["POST"])
def delete_file():
    try:
        filename = request.json.get("filename")
        valid, result = validate_file_exists(filename)

        if not valid:
            return jsonify({"success": False, "error": result}), 400

        file_path = result

        # Delete the file
        os.remove(file_path)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )

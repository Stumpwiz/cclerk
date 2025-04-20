from flask import Blueprint, render_template, redirect, url_for, session, send_from_directory, jsonify, request, flash, send_file
import os
import subprocess
import datetime
import time
import shutil
from extensions import db

# Define a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    # Redirect to log in if the user is not authenticated
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    # Get the list of backup files
    backup_files = []
    backup_dir = os.path.join("files_db_backups")
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.startswith("backup") and file.endswith(".sql"):
                backup_files.append(file)

    # Get the list of PDF files from the files_roster_reports directory
    pdf_files = []
    # Check the files_roster_reports directory
    pdfs_dir = os.path.join("files_roster_reports")
    if os.path.exists(pdfs_dir):
        for file in os.listdir(pdfs_dir):
            if file.endswith(".pdf"):
                pdf_files.append(file)

    return render_template("home.html", items=[], backup_files=backup_files, pdf_files=pdf_files)

@main_bp.route("/backup", methods=["POST"])
def backup_database():
    # Create the timestamp for the backup filename exactly as specified
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
    backup_filename = f"backup{timestamp}.sql"

    # Create the files_db_backups directory if it doesn't exist
    backup_dir = os.path.join("files_db_backups")
    os.makedirs(backup_dir, exist_ok=True)

    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        # Execute the SQLite backup command exactly as specified
        command = f"sqlite3 instance/clerk.sqlite3 .dump > {backup_path}"

        # On Windows, we need to use shell=True to handle the redirection
        subprocess.run(command, shell=True, check=True)

        return jsonify({"success": True, "filename": backup_filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route("/view_file", methods=["POST"])
def view_file():
    try:
        filename = request.json.get("filename")
        if not filename:
            return jsonify({"success": False, "error": "No filename provided"}), 400

        # Determine file type and location based on extension
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext == '.pdf':
            # PDF files are in the files_roster_reports directory
            if os.path.exists(os.path.join("files_roster_reports", filename)):
                file_path = os.path.join("files_roster_reports", filename)
            else:
                return jsonify({"success": False, "error": f"File not found: {filename}"}), 404

            # Return a URL for the client to open the PDF in a new browser tab
            file_url = url_for('main.serve_pdf', filename=filename)
            return jsonify({"success": True, "file_url": file_url})

        elif file_ext in ['.txt', '.sql']:
            # SQL backup files are in files_db_backups
            if file_ext == '.sql' and os.path.exists(os.path.join("files_db_backups", filename)):
                file_path = os.path.join("files_db_backups", filename)
                # Return a URL for the client to open the SQL file in a new browser tab
                file_url = url_for('main.serve_sql', filename=filename)
                return jsonify({"success": True, "file_url": file_url})
            # Text files might be in instance/letter_template
            elif file_ext == '.txt' and os.path.exists(os.path.join("instance", "letter_template", filename)):
                file_path = os.path.join("instance", "letter_template", filename)
                # For now, still open text files with the default application
                subprocess.Popen(["cmd", "/c", "start", "", file_path], shell=True)
            else:
                return jsonify({"success": False, "error": f"File not found: {filename}"}), 404

        else:
            return jsonify({"success": False, "error": f"Unsupported file type: {file_ext}"}), 400

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route("/serve_pdf/<filename>")
def serve_pdf(filename):
    """
    Serve a PDF file directly to the browser.
    """
    pdf_path = os.path.join("files_roster_reports", filename)

    if not os.path.exists(pdf_path):
        flash(f'PDF file {filename} not found.', 'danger')
        return redirect(url_for('main.index'))

    try:
        return send_file(pdf_path, mimetype='application/pdf')
    except Exception as e:
        flash(f'Error opening PDF: {e}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route("/serve_sql/<filename>")
def serve_sql(filename):
    """
    Serve an SQL file directly to the browser as a text file.
    """
    sql_path = os.path.join("files_db_backups", filename)

    if not os.path.exists(sql_path):
        flash(f'SQL file {filename} not found.', 'danger')
        return redirect(url_for('main.index'))

    try:
        return send_file(sql_path, mimetype='text/plain')
    except Exception as e:
        flash(f'Error opening SQL file: {e}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route("/view_pdf", methods=["POST"])
def view_pdf():
    """
    View the selected PDF file directly in the browser.
    """
    # Check if the files_roster_reports directory exists and has PDF files
    pdfs_dir = os.path.join("files_roster_reports")
    if not os.path.exists(pdfs_dir):
        flash('No PDF files found. The files_roster_reports directory does not exist.', 'info')
        return redirect(url_for('main.index'))

    # Check if there are any PDF files in the directory
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
    if not pdf_files:
        flash('There are currently no files in the files_roster_reports directory.', 'info')
        return redirect(url_for('main.index'))

    pdf_file = request.form.get('pdf_file')
    if not pdf_file:
        flash('No PDF file selected.', 'danger')
        return redirect(url_for('main.index'))

    # Check if the requested file is actually in the list of PDF files in the directory
    if pdf_file not in pdf_files:
        flash(f'PDF file {pdf_file} is not in the files_roster_reports directory.', 'danger')
        return redirect(url_for('main.index'))

    pdf_path = os.path.join("files_roster_reports", pdf_file)

    if not os.path.exists(pdf_path):
        flash(f'PDF file {pdf_file} not found.', 'danger')
        return redirect(url_for('main.index'))

    # Serve the PDF file directly to the browser
    try:
        return send_file(pdf_path, mimetype='application/pdf')
    except Exception as e:
        flash(f'Error opening PDF: {e}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route("/view_sql", methods=["POST"])
def view_sql():
    """
    View the selected SQL file directly in the browser as a text file.
    """
    # Check if the files_db_backups directory exists and has SQL files
    backup_dir = os.path.join("files_db_backups")
    if not os.path.exists(backup_dir):
        flash('No SQL files found. The files_db_backups directory does not exist.', 'info')
        return redirect(url_for('main.index'))

    # Check if there are any SQL files in the directory
    sql_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]
    if not sql_files:
        flash('There are currently no files in the files_db_backups directory.', 'info')
        return redirect(url_for('main.index'))

    sql_file = request.form.get('sql_file')
    if not sql_file:
        flash('No SQL file selected.', 'danger')
        return redirect(url_for('main.index'))

    sql_path = os.path.join("files_db_backups", sql_file)

    if not os.path.exists(sql_path):
        flash(f'SQL file {sql_file} not found.', 'danger')
        return redirect(url_for('main.index'))

    # Serve the SQL file directly to the browser as a text file
    try:
        return send_file(sql_path, mimetype='text/plain')
    except Exception as e:
        flash(f'Error opening SQL file: {e}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route("/restore", methods=["POST"])
def restore_database():
    """
    Restore the database from a selected SQL backup file.
    """
    # Get the selected SQL file from the request
    sql_file = request.json.get("filename")
    if not sql_file:
        return jsonify({"success": False, "error": "No SQL file selected"}), 400

    # Check if the file exists
    backup_dir = os.path.join("files_db_backups")
    sql_path = os.path.join(backup_dir, sql_file)

    if not os.path.exists(sql_path):
        return jsonify({"success": False, "error": f"SQL file {sql_file} not found"}), 404

    # Database path
    db_path = os.path.join("instance", "clerk.sqlite3")
    temp_backup = f"{db_path}.bak"
    temp_new_db = f"{db_path}.new"

    try:
        # Close all database connections
        db.engine.dispose()

        # Create a new empty database file
        if os.path.exists(temp_new_db):
            os.remove(temp_new_db)
        open(temp_new_db, 'a').close()

        # Restore from the SQL file to the new database
        command = f"sqlite3 {temp_new_db} < {sql_path}"

        # On Windows, we need to use shell=True to handle the redirection
        subprocess.run(command, shell=True, check=True)

        # Create a backup of the current database
        # Use copy2 instead of rename to avoid file lock issues
        if os.path.exists(db_path):
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
            shutil.copy2(db_path, temp_backup)

        # Replace the current database with the new one
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

        # If successful, remove the temporary backup
        if os.path.exists(temp_backup):
            try:
                os.remove(temp_backup)
            except PermissionError:
                # If we can't remove the backup, that's okay
                pass

        return jsonify({"success": True, "message": f"Database restored successfully from {sql_file}"})
    except Exception as e:
        # If there was an error, try to restore the original database
        if os.path.exists(temp_backup) and not os.path.exists(db_path):
            try:
                shutil.copy2(temp_backup, db_path)
            except Exception:
                # If we can't restore the backup, there's nothing we can do
                pass

        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route("/delete_file", methods=["POST"])
def delete_file():
    try:
        filename = request.json.get("filename")
        if not filename:
            return jsonify({"success": False, "error": "No filename provided"}), 400

        # Determine file type and location based on extension
        file_ext = os.path.splitext(filename)[1].lower()
        file_path = None  # Initialize file_path to None

        if file_ext == '.pdf':
            # PDF files are in the files_roster_reports directory
            file_path = os.path.join("files_roster_reports", filename)
        elif file_ext == '.sql':
            # SQL backup files are in files_db_backups
            file_path = os.path.join("files_db_backups", filename)
        elif file_ext == '.txt':
            # Text files are in instance/letter_template
            file_path = os.path.join("instance", "letter_template", filename)
        else:
            return jsonify({"success": False, "error": f"Unsupported file type: {file_ext}"}), 400

        if not file_path or not os.path.exists(file_path):
            return jsonify({"success": False, "error": f"File not found: {filename}"}), 404

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
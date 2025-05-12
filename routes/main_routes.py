from flask import Blueprint, render_template, redirect, url_for, session, send_from_directory, jsonify, request, flash, \
    current_app
import os
import subprocess
import datetime
import time
import shutil
import json
from extensions import db, csrf
from utils.file_handlers import get_file_path, validate_file_exists, serve_file, check_directory_for_files
from forms import CSRFForm
from routes.decorators import handle_errors

# Database restoration helper functions
def backup_current_database(db_path, temp_backup):
    """
    Create a backup of the current database.
    """
    if os.path.exists(db_path):
        if os.path.exists(temp_backup):
            os.remove(temp_backup)
        shutil.copy2(db_path, temp_backup)



def replace_database(db_path, temp_new_db):
    """
    Replace the current database with the new one.
    """
    # First try to remove the current database
    max_attempts = 10  # Increased from 5 to 10
    for attempt in range(max_attempts):
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            break
        except PermissionError:
            if attempt < max_attempts - 1:
                # Wait a bit longer and try again
                time.sleep(1.0)  # Increased from 0.5 to 1.0 seconds
                # Force Python garbage collection to release any file handles
                import gc
                gc.collect()
            else:
                raise Exception("Unable to replace database file because it is locked by another process. Please stop the server before restoring the database.")

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
@handle_errors
def index():
    # Redirect to log in if the user is not authenticated
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    # Check if a database restore has been completed
    restore_completed_path = os.path.join(current_app.root_path, 'instance', 'restore_completed.json')
    if os.path.exists(restore_completed_path):
        try:
            # Read the restore information from the file
            with open(restore_completed_path, 'r') as f:
                restore_info = json.load(f)

            # Get the backup file name and timestamp
            backup_file = restore_info.get('backup_file')
            timestamp = restore_info.get('timestamp')

            # Format the timestamp for display
            formatted_timestamp = timestamp
            try:
                # Try to parse the ISO format timestamp and format it more nicely
                import datetime
                dt = datetime.datetime.fromisoformat(timestamp)
                formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                # If parsing fails, just use the original timestamp
                pass

            # Flash a message to the user
            flash(f"The database has been restored from backup file '{backup_file}' at {formatted_timestamp}.", 'success')

            # Delete the file to ensure the message is only shown once
            os.remove(restore_completed_path)
            current_app.logger.info("Removed restore_completed.json file after displaying notification")
        except Exception as e:
            current_app.logger.error(f"Error reading restore_completed.json: {str(e)}")
            # Try to delete the file even if there was an error
            try:
                os.remove(restore_completed_path)
            except:
                pass

    # Get the list of backup files
    backup_files = []
    backup_dir = os.path.join(current_app.root_path, current_app.config['BACKUP_DIR'])
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            # Match files with the pattern YY.MM.DD.HH.mm.SS.db
            if file.endswith(".db") and file.count('.') == 6 and len(file.split('.')[0]) == 2:
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
@handle_errors
def backup_database():
    # Create the timestamp for the backup filename exactly as specified
    timestamp = datetime.datetime.now().strftime("%y.%m.%d.%H.%M.%S")
    backup_filename = f"{timestamp}.db"

    # Create the backup directory if it doesn't exist
    backup_dir = os.path.join(current_app.root_path, current_app.config['BACKUP_DIR'])
    os.makedirs(backup_dir, exist_ok=True)

    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        # Get the path to the current database
        db_path = os.path.join(current_app.root_path, current_app.config['DB_PATH'])

        # Copy the database file
        shutil.copy2(db_path, backup_path)

        return jsonify({"success": True, "filename": backup_filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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


@main_bp.route("/restore", methods=["POST"])
@handle_errors
def restore_database():
    """
    Restore the database from a selected database backup file.

    If the database is locked by the running server, this will schedule
    a restore operation to be performed on the next server start.
    """
    # Check if request contains valid JSON data
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    # Get the selected backup file from the request
    backup_file = request.json.get("filename")
    if not backup_file:
        return jsonify({"success": False, "error": "Filename is required"}), 400

    valid, result = validate_file_exists(backup_file)

    if not valid:
        return jsonify({"success": False, "error": result}), 400

    backup_path = result

    # Database path
    db_path = os.path.join(current_app.root_path, current_app.config['DB_PATH'])
    temp_backup = f"{db_path}.bak"

    try:
        # Close all database connections
        db.engine.dispose()

        # Force Python garbage collection to release any file handles
        import gc
        gc.collect()

        # Step 1: Create a backup of the current database
        backup_current_database(db_path, temp_backup)

        # Step 2: Replace the current database with the backup
        try:
            # Try to copy the backup file directly to the database location
            if os.path.exists(db_path):
                os.remove(db_path)
            shutil.copy2(backup_path, db_path)

            # Step 3: Clean up the temporary backup
            cleanup_backup(temp_backup)

            return jsonify({"success": True, "message": f"Database restored successfully from {backup_file}"})
        except Exception as e:
            if "locked by another process" in str(e):
                # Schedule the restore operation for the next server start
                schedule_restore_operation(backup_file)

                # Provide a clear error message to the user with accurate instructions
                return jsonify({
                    "success": False, 
                    "error": "The database file is locked by the running server.",
                    "scheduled": True,
                    "message": "A restore operation has been scheduled. The database will be restored from this backup the next time the server starts."
                }), 202  # 202 Accepted
            else:
                # Re-raise the exception for other errors
                raise
    except Exception as e:
        # If there was an error, try to restore the original database
        restore_backup_on_error(temp_backup, db_path)

        return jsonify({"success": False, "error": str(e)}), 500

def schedule_restore_operation(backup_file):
    """
    Schedule a database restore operation to be performed on the next server start.

    This creates a file in the instance directory that will be checked when the server starts.
    If the file exists, the restore operation will be performed.
    """
    # Create the restore info file in the instance directory
    restore_info_path = os.path.join(current_app.root_path, 'instance', 'restore_scheduled.json')

    # Write the restore information to the file
    with open(restore_info_path, 'w') as f:
        json.dump({
            'backup_file': backup_file,
            'timestamp': datetime.datetime.now().isoformat()
        }, f)

    current_app.logger.info(f"Scheduled restore operation from {backup_file}")

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

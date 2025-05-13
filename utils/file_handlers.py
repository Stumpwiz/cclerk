import os
from flask import send_file, current_app

def get_file_path(filename):
    """
    Determine the file path based on the file extension.
    Returns the full path and None if the file type is not supported.
    """
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext == '.pdf':
        # PDF files are in the reports directory
        return os.path.join(current_app.root_path, current_app.config['REPORTS_DIR'], filename)
    elif file_ext == '.txt':
        # Text files are in instance/letter_template
        return os.path.join(current_app.root_path, "instance", "letter_template", filename)
    else:
        return None

def validate_file_exists(filename, file_path=None):
    """
    Validate that the file exists.
    Returns (True, file_path) if the file exists, (False, error_message) otherwise.
    """
    if not filename:
        return False, "No filename provided"

    if file_path is None:
        file_path = get_file_path(filename)

    if not file_path:
        file_ext = os.path.splitext(filename)[1].lower()
        return False, f"Unsupported file type: {file_ext}"

    if not os.path.exists(file_path):
        return False, f"File not found: {filename}"

    return True, file_path

def serve_file(file_path, mimetype):
    """
    Serve a file with the specified mimetype.
    Returns a Flask response object or raises an exception.
    """
    try:
        return send_file(file_path, mimetype=mimetype)
    except Exception as e:
        raise Exception(f"Error opening file: {e}")

def check_directory_for_files(directory, extension, error_message):
    """
    Check if a directory exists and contains files with the specified extension.
    Returns (True, file_list) if files exist, (False, error_message) otherwise.
    """
    if not os.path.exists(directory):
        return False, error_message

    files = [f for f in os.listdir(directory) if f.endswith(extension)]
    if not files:
        return False, f"There are currently no files with extension {extension} in the directory."

    return True, files

from flask import Blueprint, render_template, redirect, url_for, session, send_from_directory

# Define a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    # Redirect to log in if user is not authenticated
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    return render_template("home.html", items=[])

@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from forms import CSRFForm
from routes.decorators import handle_errors

# Define a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
@handle_errors
def login():
    if request.method == "POST":  # Handle login submission
        username = request.form["username"]
        password = request.form["password"]

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.permanent = False  # Make session expire when browser is closed
            session["user_id"] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("auth.login"))

    # Handle GET request to render the login form
    form = CSRFForm()
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@handle_errors
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("auth.login"))

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
)
import os
from config import Config
from models import db, User
from flask_migrate import Migrate

# Initialize Flask app
app = Flask(__name__, instance_relative_config=True)

# Configure app using config.py
app.config.from_object(Config)

# Ensure the instance folder exists
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# Initialize the database with the Flask app
db.init_app(app)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()  # Create all tables (like the users table)


# Routes
@app.route("/")
def index():
    # Redirect to log in if user is not authenticated
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("home.html", items=[])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":  # Handle login submission
        username = request.form["username"]
        password = request.form["password"]

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    # Handle GET request to render the login form
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


@app.route("/crud", methods=["GET", "POST"])
def crud():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    items = []  # Placeholder for item list
    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description")
        # Placeholder logic for item creation (to be implemented later)
        flash("Item added successfully!", "success")
        return redirect(url_for("crud"))
    return render_template("crud.html", items=items)


@app.route("/delete/<int:item_id>")
def delete_item(item_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))
    # Placeholder deletion logic (to be implemented later)
    flash("Item deleted successfully!", "success")
    return redirect(url_for("crud"))


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


if __name__ == "__main__":
    app.run(debug=True)

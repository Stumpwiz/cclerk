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
from config import Config
from extensions import db, migrate
from models.user import User
from routes import register_blueprints
from commands.init_db import init_db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    register_blueprints(app)
    # Register CLI command
    app.cli.add_command(init_db)

    # Load configuration
    app.config.from_object(Config)
    if app.config["SQLALCHEMY_DATABASE_URI"] == "DATABASE_URL not set.":
        raise ValueError("DATABASE_URL is not set!")
    if not app.config.get("SECRET_KEY"):
        raise ValueError("SECRET_KEY is not set! Please configure it properly in the environment or config.")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Routes
    @app.route("/")
    def index():
        # Redirect to log in if user is not authenticated
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return render_template("home.html", items=[])

    # ToDo add error message for incorrect credentials.
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

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
        )

    with app.app_context():
        db.create_all()  # Create all tables (like the users table)

    return app


if __name__ == "__main__":
    application = create_app()  # Renaming 'app' to 'application' in the outer scope
    application.run(debug=True)

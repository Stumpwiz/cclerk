from .letters import letters_bp
from .users import users_bp
from .auth_routes import auth_bp
from .main_routes import main_bp
from .body import body_bp
from .office import office_bp
from .person import person_bp
from .term import term_bp
from routes.report import report_bp


def register_blueprints(app):
    # Register API blueprints with URL prefixes
    app.register_blueprint(letters_bp, url_prefix='/api/letters')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(body_bp, url_prefix='/api/body')
    app.register_blueprint(office_bp, url_prefix='/api/office')
    app.register_blueprint(person_bp, url_prefix='/api/person')
    app.register_blueprint(term_bp, url_prefix='/api/term')

    # Register main application blueprints without URL prefixes
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)  # ✅ Add this

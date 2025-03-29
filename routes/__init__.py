from .letters import letters_bp
from .minutes import minutes_bp
from .reports import reports_bp
from .rosters import rosters_bp
from .users import users_bp


def register_blueprints(app):
    app.register_blueprint(letters_bp, url_prefix='/api/letters')
    app.register_blueprint(minutes_bp, url_prefix='/api/minutes')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(rosters_bp, url_prefix='/api/rosters')
    app.register_blueprint(users_bp, url_prefix='/api/users')


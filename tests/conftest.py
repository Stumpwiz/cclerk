# tests/conftest.py
import os
import tempfile
import pytest
from app import create_app  # assuming create_app is defined in app.py

@pytest.fixture
def app():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Create the Flask app with test configuration
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test_secret_key',
        'WTF_CSRF_ENABLED': False  # optional: if you use Flask-WTF
    })

    with app.app_context():
        # Initialize the database schema
        from extensions import db
        db.create_all()

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

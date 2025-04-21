# tests/conftest.py
import os
import tempfile
import pytest
import sqlite3
from datetime import date
from app import create_app
from extensions import db
from models.body import Body
from models.office import Office
from models.person import Person
from models.term import Term
from models.report_record import ReportRecord

@pytest.fixture
def app():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Create the Flask app with test configuration
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test_secret_key',
        'WTF_CSRF_ENABLED': False,  # optional: if you use Flask-WTF
        'DATABASE': db_path  # Add this for init_db to work
    })

    with app.app_context():
        # Initialize the database schema
        from extensions import db
        db.create_all()

        # Initialize the database with schema.sql to create the report_record view
        with sqlite3.connect(db_path) as conn:
            with open('schema.sql', 'r', encoding='utf-16') as f:
                conn.executescript(f.read())

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

@pytest.fixture
def authenticated_client(app, client):
    """A client that is authenticated as a user."""
    with app.app_context():
        from models.user import User
        from werkzeug.security import generate_password_hash

        # Create a test user
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password'),
            role='admin'
        )
        db.session.add(user)
        db.session.commit()

    # Log in the user
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password'
    })

    return client

@pytest.fixture
def test_data(app):
    """Create test data for the database."""
    with app.app_context():
        # Create test bodies
        body1 = Body(body_id=1, name='Test Body 1', mission='Test Mission 1', body_precedence=1.0)
        body2 = Body(body_id=2, name='Test Body 2', mission='Test Mission 2', body_precedence=2.0)
        db.session.add_all([body1, body2])
        db.session.commit()

        # Create test offices
        office1 = Office(office_id=1, title='Test Office 1', office_precedence=1.0, office_body_id=1)
        office2 = Office(office_id=2, title='Test Office 2', office_precedence=2.0, office_body_id=1)
        office3 = Office(office_id=3, title='Test Office 3', office_precedence=1.0, office_body_id=2)
        db.session.add_all([office1, office2, office3])
        db.session.commit()

        # Create test persons
        person1 = Person(person_id=1, first='John', last='Doe', email='john@example.com', phone='123-456-7890', apt='101')
        person2 = Person(person_id=2, first='Jane', last='Smith', email='jane@example.com', phone='987-654-3210', apt='202')
        person3 = Person(person_id=3, first='Bob', last='Johnson', email='bob@example.com', phone='555-555-5555', apt='303')
        db.session.add_all([person1, person2, person3])
        db.session.commit()

        # Create test terms
        term1 = Term(term_person_id=1, term_office_id=1, start=date(2020, 1, 1), end=date(2022, 12, 31), ordinal='1st')
        term2 = Term(term_person_id=2, term_office_id=2, start=date(2021, 1, 1), end=date(2023, 12, 31), ordinal='2nd')
        term3 = Term(term_person_id=3, term_office_id=3, start=date(2019, 1, 1), end=date(2021, 12, 31), ordinal='3rd')
        db.session.add_all([term1, term2, term3])
        db.session.commit()

        return {
            'bodies': [body1, body2],
            'offices': [office1, office2, office3],
            'persons': [person1, person2, person3],
            'terms': [term1, term2, term3]
        }

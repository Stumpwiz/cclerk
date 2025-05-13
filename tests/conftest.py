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
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Enable foreign key constraints for all SQLite connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
        'DATABASE': db_path,  # Add this for init_db to work
        'REPORTS_DIR': 'files_roster_reports'
    })

    with app.app_context():
        # Initialize the database schema
        from extensions import db
        db.drop_all()  # Drop all tables first to ensure a clean state
        db.create_all()

        # Initialize only the report_record view from schema.sql
        try:
            # Extract just the CREATE VIEW statement from schema.sql
            view_sql = """
CREATE VIEW report_record AS
SELECT
    person.personid AS person_id,
    person.first AS first,
    person.last AS last,
    person.email AS email,
    person.phone AS phone,
    person.apt AS apt,
    term.start AS start,
    term.end AS end,
    term.ordinal AS ordinal,
    term.termpersonid AS term_person_id,
    term.termofficeid AS term_office_id,
    office.office_id AS office_id,
    office.title AS title,
    office.office_precedence AS office_precedence,
    office.office_body_id AS office_body_id,
    body.body_id AS body_id,
    body.name AS name,
    body.body_precedence AS body_precedence
FROM term
JOIN office ON office.office_id = term.termofficeid
JOIN body ON body.body_id = office.office_body_id
JOIN person ON person.personid = term.termpersonid
ORDER BY body.body_precedence;
"""
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys=ON")
                try:
                    # Try to drop it as a table first (if it was created as a table)
                    conn.execute("DROP TABLE IF EXISTS report_record")
                    print("Dropped report_record table")
                except sqlite3.OperationalError as e:
                    # If it's not a table, try to drop it as a view
                    try:
                        conn.execute("DROP VIEW IF EXISTS report_record")
                        print("Dropped report_record view")
                    except sqlite3.OperationalError as e:
                        print(f"Error dropping report_record: {e}")
                # Create the view
                conn.executescript(view_sql)
        except Exception as e:
            print(f"Error creating report_record view: {e}")

    yield app

    # Cleanup
    try:
        # Ensure all database connections are closed
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

        os.close(db_fd)
        os.unlink(db_path)
    except Exception as e:
        print(f"Error during cleanup: {e}")
        # If we can't delete the file now, it will be cleaned up by the OS later

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
            password='password'
        )
        user.role = 'admin'  # Set role after creation
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
        person1 = Person(person_id=1, first='John', last='Doe', email='john@example.com', phone='(123) 456-7890', apt='101')
        person2 = Person(person_id=2, first='Jane', last='Smith', email='jane@example.com', phone='(987) 654-3210', apt='202')
        person3 = Person(person_id=3, first='Bob', last='Johnson', email='bob@example.com', phone='(555) 555-5555', apt='303')
        db.session.add_all([person1, person2, person3])
        db.session.commit()

        # Create test terms
        term1 = Term(term_person_id=1, term_office_id=1, start=date(2020, 1, 1), end=date(2022, 12, 31), ordinal='1st')
        term2 = Term(term_person_id=2, term_office_id=2, start=date(2021, 1, 1), end=date(2023, 12, 31), ordinal='2nd')
        term3 = Term(term_person_id=3, term_office_id=3, start=date(2019, 1, 1), end=date(2021, 12, 31), ordinal='3rd')
        db.session.add_all([term1, term2, term3])
        db.session.commit()

        # Recreate the report_record view after data is inserted
        db_path = app.config['DATABASE']
        try:
            # Extract just the CREATE VIEW statement from schema.sql
            view_sql = """
CREATE VIEW report_record AS
SELECT
    person.personid AS person_id,
    person.first AS first,
    person.last AS last,
    person.email AS email,
    person.phone AS phone,
    person.apt AS apt,
    term.start AS start,
    term.end AS end,
    term.ordinal AS ordinal,
    term.termpersonid AS term_person_id,
    term.termofficeid AS term_office_id,
    office.office_id AS office_id,
    office.title AS title,
    office.office_precedence AS office_precedence,
    office.office_body_id AS office_body_id,
    body.body_id AS body_id,
    body.name AS name,
    body.body_precedence AS body_precedence
FROM term
JOIN office ON office.office_id = term.termofficeid
JOIN body ON body.body_id = office.office_body_id
JOIN person ON person.personid = term.termpersonid
ORDER BY body.body_precedence;
"""
            # First, drop the view or table if it exists
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys=ON")
                try:
                    # Try to drop it as a table first (if it was created as a table)
                    conn.execute("DROP TABLE IF EXISTS report_record")
                    conn.commit()
                    print("Dropped report_record table")
                except sqlite3.OperationalError as e:
                    # If it's not a table, try to drop it as a view
                    try:
                        conn.execute("DROP VIEW IF EXISTS report_record")
                        conn.commit()
                        print("Dropped report_record view")
                    except sqlite3.OperationalError as e:
                        print(f"Error dropping report_record: {e}")

            # Then create the view
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys=ON")
                conn.executescript(view_sql)
                conn.commit()

            # Verify the view was created by querying it
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys=ON")
                cursor = conn.execute("SELECT COUNT(*) FROM report_record;")
                count = cursor.fetchone()[0]
                print(f"report_record view created with {count} records")

        except Exception as e:
            print(f"Error creating report_record view: {e}")
            raise  # Re-raise the exception to fail the test

        return {
            'bodies': [body1, body2],
            'offices': [office1, office2, office3],
            'persons': [person1, person2, person3],
            'terms': [term1, term2, term3]
        }

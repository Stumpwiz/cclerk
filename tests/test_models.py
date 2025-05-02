# tests/test_models.py

import pytest
from datetime import date
from extensions import db
from models.body import Body
from models.office import Office
from models.person import Person
from models.term import Term
from models.report_record import ReportRecord
from sqlalchemy.exc import IntegrityError


class TestBodyModel:
    def test_create_body(self, app):
        """Test creating a Body."""
        with app.app_context():
            body = Body(body_id=100, name='Test Body', mission='Test Mission', body_precedence=1.0)
            db.session.add(body)
            db.session.commit()

            # Retrieve the body from the database
            retrieved_body = Body.query.filter_by(body_id=100).first()
            assert retrieved_body is not None
            assert retrieved_body.name == 'Test Body'
            assert retrieved_body.mission == 'Test Mission'
            assert retrieved_body.body_precedence == 1.0

    def test_update_body(self, app):
        """Test updating a Body."""
        with app.app_context():
            # Create a body
            body = Body(body_id=101, name='Original Name', mission='Original Mission', body_precedence=1.0)
            db.session.add(body)
            db.session.commit()

            # Update the body
            body.name = 'Updated Name'
            body.mission = 'Updated Mission'
            body.body_precedence = 2.0
            db.session.commit()

            # Retrieve the updated body
            updated_body = Body.query.filter_by(body_id=101).first()
            assert updated_body.name == 'Updated Name'
            assert updated_body.mission == 'Updated Mission'
            assert updated_body.body_precedence == 2.0

    def test_delete_body(self, app):
        """Test deleting a Body."""
        with app.app_context():
            # Create a body
            body = Body(body_id=102, name='Body to Delete', mission='Mission', body_precedence=1.0)
            db.session.add(body)
            db.session.commit()

            # Delete the body
            db.session.delete(body)
            db.session.commit()

            # Verify the body is deleted
            deleted_body = Body.query.filter_by(body_id=102).first()
            assert deleted_body is None


class TestOfficeModel:
    def test_create_office(self, app, test_data):
        """Test creating an Office."""
        with app.app_context():
            office = Office(office_id=100, title='Test Office', office_precedence=1.0, office_body_id=1)
            db.session.add(office)
            db.session.commit()

            # Retrieve the office from the database
            retrieved_office = Office.query.filter_by(office_id=100).first()
            assert retrieved_office is not None
            assert retrieved_office.title == 'Test Office'
            assert retrieved_office.office_precedence == 1.0
            assert retrieved_office.office_body_id == 1

    def test_office_body_relationship(self, app, test_data):
        """Test the relationship between Office and Body."""
        with app.app_context():
            # Get the first office from test data
            office = Office.query.filter_by(office_id=1).first()

            # Check that the office has a body
            assert office.body is not None
            assert office.body.name == 'Test Body 1'

    def test_office_foreign_key_constraint(self, app):
        """Test that the foreign key constraint is enforced for office_body_id."""
        with app.app_context():
            # Try to create an office with a non-existent body_id
            office = Office(office_id=103, title='Invalid Office', office_precedence=1.0, office_body_id=999)
            db.session.add(office)

            # This should raise an IntegrityError
            with pytest.raises(IntegrityError):
                db.session.commit()

            # Rollback the session
            db.session.rollback()


class TestPersonModel:
    def test_create_person(self, app):
        """Test creating a Person."""
        with app.app_context():
            person = Person(person_id=100, first='Test', last='Person', email='test@example.com', phone='(123) 456-7890', apt='101')
            db.session.add(person)
            db.session.commit()

            # Retrieve the person from the database
            retrieved_person = Person.query.filter_by(person_id=100).first()
            assert retrieved_person is not None
            assert retrieved_person.first == 'Test'
            assert retrieved_person.last == 'Person'
            assert retrieved_person.email == 'test@example.com'
            assert retrieved_person.phone == '(123) 456-7890'
            assert retrieved_person.apt == '101'

    def test_unique_constraint(self, app):
        """Test the unique constraint on first and last name."""
        with app.app_context():
            # Create a person
            person1 = Person(person_id=101, first='Unique', last='Name', email='unique@example.com')
            db.session.add(person1)
            db.session.commit()

            # Try to create another person with the same first and last name
            person2 = Person(person_id=102, first='Unique', last='Name', email='another@example.com')
            db.session.add(person2)

            # This should raise an IntegrityError
            with pytest.raises(IntegrityError):
                db.session.commit()

            # Rollback the session
            db.session.rollback()


class TestTermModel:
    def test_create_term(self, app, test_data):
        """Test creating a Term."""
        with app.app_context():
            # Use a different person-office combination to avoid unique constraint violation
            term = Term(
                term_person_id=1, 
                term_office_id=2, 
                start=date(2023, 1, 1), 
                end=date(2025, 12, 31), 
                ordinal='4th'
            )
            db.session.add(term)
            db.session.commit()

            # Retrieve the term from the database
            retrieved_term = Term.query.filter_by(term_person_id=1, term_office_id=2).first()
            assert retrieved_term is not None
            assert retrieved_term.start == date(2023, 1, 1)
            assert retrieved_term.end == date(2025, 12, 31)
            assert retrieved_term.ordinal == '4th'

    def test_term_relationships(self, app, test_data):
        """Test the relationships between Term, Person, and Office."""
        with app.app_context():
            # Get the first term from test data
            term = Term.query.filter_by(term_person_id=1, term_office_id=1).first()

            # Check that the term has a person and an office
            assert term.person is not None
            assert term.office is not None
            assert term.person.first == 'John'
            assert term.person.last == 'Doe'
            assert term.office.title == 'Test Office 1'

    def test_term_foreign_key_constraints(self, app):
        """Test that the foreign key constraints are enforced for term_person_id and term_office_id."""
        with app.app_context():
            # Try to create a term with non-existent person_id
            term1 = Term(term_person_id=999, term_office_id=1, start=date(2023, 1, 1), end=date(2025, 12, 31))
            db.session.add(term1)

            # This should raise an IntegrityError
            with pytest.raises(IntegrityError):
                db.session.commit()

            # Rollback the session
            db.session.rollback()

            # Try to create a term with non-existent office_id
            term2 = Term(term_person_id=1, term_office_id=999, start=date(2023, 1, 1), end=date(2025, 12, 31))
            db.session.add(term2)

            # This should raise an IntegrityError
            with pytest.raises(IntegrityError):
                db.session.commit()

            # Rollback the session
            db.session.rollback()


class TestReportRecordView:
    def test_report_record_view(self, app, test_data):
        """Test querying the report_record view."""
        with app.app_context():
            # Query all records from the view
            records = ReportRecord.query.all()

            # Check that we have the expected number of records
            assert len(records) == 3

            # Check that the records contain the expected data
            for record in records:
                # Verify that the record has all the expected fields
                assert record.person_id is not None
                assert record.first is not None
                assert record.last is not None
                assert record.email is not None
                assert record.term_person_id is not None
                assert record.term_office_id is not None
                assert record.office_id is not None
                assert record.title is not None
                assert record.body_id is not None
                assert record.name is not None

                # Verify that the data matches what we expect
                if record.term_person_id == 1 and record.term_office_id == 1:
                    assert record.first == 'John'
                    assert record.last == 'Doe'
                    assert record.title == 'Test Office 1'
                    assert record.name == 'Test Body 1'
                elif record.term_person_id == 2 and record.term_office_id == 2:
                    assert record.first == 'Jane'
                    assert record.last == 'Smith'
                    assert record.title == 'Test Office 2'
                    assert record.name == 'Test Body 1'
                elif record.term_person_id == 3 and record.term_office_id == 3:
                    assert record.first == 'Bob'
                    assert record.last == 'Johnson'
                    assert record.title == 'Test Office 3'
                    assert record.name == 'Test Body 2'

    def test_report_record_ordering(self, app, test_data):
        """Test that the report_record view orders records by body_precedence and office_precedence."""
        with app.app_context():
            # Query records ordered by body_precedence and office_precedence
            records = ReportRecord.query.order_by(
                ReportRecord.body_precedence,
                ReportRecord.office_precedence
            ).all()

            # Check that the records are in the expected order
            assert records[0].name == 'Test Body 1'
            assert records[0].title == 'Test Office 1'
            assert records[1].name == 'Test Body 1'
            assert records[1].title == 'Test Office 2'
            assert records[2].name == 'Test Body 2'
            assert records[2].title == 'Test Office 3'

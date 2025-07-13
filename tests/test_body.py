import pytest
from flask import url_for
from models.body import Body
from extensions import db

def test_update_body_api(authenticated_client, test_data):
    """Test the POST /api/body/update route."""
    # Get a body from test_data
    with authenticated_client.application.app_context():
        body = Body.query.first()
        body_id = body.body_id

    # Update the body
    response = authenticated_client.post("/api/body/update", json={
        "id": body_id,
        "name": "Updated Body Name",
        "mission": "Updated Mission",
        "precedence": 5.0
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["id"] == body_id
    assert json_data["name"] == "Updated Body Name"
    assert json_data["mission"] == "Updated Mission"
    assert json_data["precedence"] == 5.0

    # Check that the body was updated in the database
    with authenticated_client.application.app_context():
        updated_body = db.session.get(Body, body_id)
        assert updated_body.name == "Updated Body Name"
        assert updated_body.mission == "Updated Mission"
        assert updated_body.body_precedence == 5.0

def test_delete_body_api(authenticated_client, test_data, app):
    """Test the POST /api/body/delete route."""
    # Create a body to delete
    with app.app_context():
        body = Body(name="Body to Delete", mission="Delete Me", body_precedence=10.0)
        db.session.add(body)
        db.session.commit()
        body_id = body.body_id

    # Delete the body
    response = authenticated_client.post("/api/body/delete", json={"id": body_id})

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["message"] == "Body deleted successfully"

    # Check that the body was deleted from the database
    with app.app_context():
        deleted_body = db.session.get(Body, body_id)
        assert deleted_body is None

def test_delete_body_with_offices_api(authenticated_client, test_data, app):
    """Test the POST /api/body/delete route when body has associated offices."""
    # Create a body to delete
    with app.app_context():
        from models.office import Office

        body = Body(name="Body with Offices", mission="Try to Delete Me", body_precedence=12.0)
        db.session.add(body)
        db.session.commit()
        body_id = body.body_id

        # Create an office associated with this body
        office = Office(title="Test Office", office_precedence=1.0, office_body_id=body_id)
        db.session.add(office)
        db.session.commit()

    # Try to delete the body
    response = authenticated_client.post("/api/body/delete", json={"id": body_id})

    # Should fail with 400 status code
    assert response.status_code == 400
    json_data = response.get_json()
    assert "error" in json_data
    assert "Cannot delete body with associated offices" == json_data["error"]
    assert "details" in json_data

    # Check that the body was not deleted from the database
    with app.app_context():
        body = db.session.get(Body, body_id)
        assert body is not None
        assert body.name == "Body with Offices"

def test_view_bodies(authenticated_client, test_data):
    """Test the GET /api/body/view route."""
    response = authenticated_client.get("/api/body/view")

    assert response.status_code == 200
    assert b"<h2" in response.data  # Check for HTML content
    assert b"Test Body 1" in response.data  # Check for body name from test_data
    assert b"Test Body 2" in response.data  # Check for body name from test_data

def test_create_body_html(authenticated_client, app):
    """Test the POST /api/body/create_html route."""
    # Create a body using the HTML form
    with authenticated_client.session_transaction() as session:
        # Set up the session with a CSRF token
        session['_csrf_token'] = 'test_csrf_token'

    response = authenticated_client.post("/api/body/create_html", data={
        "name": "New Body from HTML",
        "mission": "Created via HTML form",
        "precedence": "7.5",
        "csrf_token": "test_csrf_token"
    }, follow_redirects=True)

    assert response.status_code == 200

    # Check for the presence of an alert div that would contain the flash message
    assert b'<div class="alert alert-success' in response.data
    assert b'New Body from HTML' in response.data

    # Check that the body was created in the database
    with app.app_context():
        body = Body.query.filter_by(name="New Body from HTML").first()
        assert body is not None
        assert body.mission == "Created via HTML form"
        assert body.body_precedence == 7.5

def test_update_body_html(authenticated_client, test_data):
    """Test the POST /api/body/update_html route."""
    # Get a body from test_data
    with authenticated_client.application.app_context():
        body = Body.query.first()
        body_id = body.body_id

    # Set up CSRF token
    with authenticated_client.session_transaction() as session:
        session['_csrf_token'] = 'test_csrf_token'

    # Update the body using the HTML form
    response = authenticated_client.post("/api/body/update_html", data={
        "id": body_id,
        "name": "Updated via HTML",
        "mission": "Updated via HTML form",
        "precedence": "8.5",
        "csrf_token": "test_csrf_token"
    }, follow_redirects=True)

    assert response.status_code == 200

    # Check for the presence of an alert div that would contain the flash message
    assert b'<div class="alert alert-success' in response.data
    assert b'Updated via HTML' in response.data

    # Check that the body was updated in the database
    with authenticated_client.application.app_context():
        updated_body = db.session.get(Body, body_id)
        assert updated_body.name == "Updated via HTML"
        assert updated_body.mission == "Updated via HTML form"
        assert updated_body.body_precedence == 8.5

def test_delete_body_html(authenticated_client, app):
    """Test the POST /api/body/delete_html route."""
    # Create a body to delete
    with app.app_context():
        body = Body(name="HTML Body to Delete", mission="Delete Me via HTML", body_precedence=11.0)
        db.session.add(body)
        db.session.commit()
        body_id = body.body_id

    # Set up CSRF token
    with authenticated_client.session_transaction() as session:
        session['_csrf_token'] = 'test_csrf_token'

    # Delete the body using the HTML form
    response = authenticated_client.post("/api/body/delete_html", data={
        "id": body_id,
        "csrf_token": "test_csrf_token"
    }, follow_redirects=True)

    assert response.status_code == 200

    # Check for the presence of an alert div that would contain the flash message
    assert b'<div class="alert alert-success' in response.data
    assert b'HTML Body to Delete' in response.data

    # Check that the body was deleted from the database
    with app.app_context():
        deleted_body = db.session.get(Body, body_id)
        assert deleted_body is None

def test_delete_body_with_offices_html(authenticated_client, app):
    """Test the POST /api/body/delete_html route when body has associated offices."""
    # Create a body to delete
    with app.app_context():
        from models.office import Office

        body = Body(name="HTML Body with Offices", mission="Try to Delete Me via HTML", body_precedence=13.0)
        db.session.add(body)
        db.session.commit()
        body_id = body.body_id

        # Create an office associated with this body
        office = Office(title="Test HTML Office", office_precedence=2.0, office_body_id=body_id)
        db.session.add(office)
        db.session.commit()

    # Set up CSRF token
    with authenticated_client.session_transaction() as session:
        session['_csrf_token'] = 'test_csrf_token'

    # Try to delete the body using the HTML form
    response = authenticated_client.post("/api/body/delete_html", data={
        "id": body_id,
        "csrf_token": "test_csrf_token"
    }, follow_redirects=True)

    assert response.status_code == 200

    # Check for the presence of an alert div that would contain the error flash message
    assert b'<div class="alert alert-danger' in response.data
    assert b'Cannot delete body' in response.data
    assert b'HTML Body with Offices' in response.data
    assert b'office(s) associated with it' in response.data

    # Check that the body was not deleted from the database
    with app.app_context():
        body = db.session.get(Body, body_id)
        assert body is not None
        assert body.name == "HTML Body with Offices"

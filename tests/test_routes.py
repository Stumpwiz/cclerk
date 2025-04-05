# tests/test_routes.py

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_home_route(client):
    # Scenario 1: User is NOT authenticated
    response = client.get("/")  # Simulate GET request to the home route
    assert response.status_code == 302  # Check for redirect
    assert response.location.endswith("/login")  # Ensure redirect is to the login page

    # Scenario 2: User IS authenticated
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # Simulate a user being logged in

    response = client.get("/")  # Simulate another GET request
    assert response.status_code == 200  # Check for a successful response
    assert b"Welcome to Clerk App" in response.data  # Check that the response's HTML contains expected content


def test_login_route_get(client):
    # Test GET request to login route
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_route_post_invalid(client):
    # Test POST request to login route with invalid credentials
    response = client.post("/login", data={
        "username": "nonexistent_user",
        "password": "wrong_password"
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check that we're still on the login page (login form is present)
    assert b'<form method="POST">' in response.data
    assert b'<input type="text" class="form-control" id="username" name="username" required>' in response.data
    assert b'<input type="password" class="form-control" id="password" name="password" required>' in response.data


def test_logout_route(client):
    # First, simulate a logged-in user
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    # Test logout route
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200

    # Check that user_id is removed from session
    with client.session_transaction() as sess:
        assert "user_id" not in sess

    # Check that we're redirected to login page
    assert b"Login" in response.data


def test_favicon_route(client):
    # Test favicon route
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.mimetype == "image/vnd.microsoft.icon"


def test_letters_route(client):
    # Test the letters API endpoint
    response = client.get("/api/letters/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data == {"message": "This is the letters endpoint"}


def test_rosters_route(client):
    # Test the rosters API endpoint
    response = client.get("/api/rosters/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data == {"message": "This is the rosters endpoint"}


def test_users_route(client):
    # Test the users API endpoint
    response = client.get("/api/users/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data == {"message": "This is the users endpoint"}


def test_body_route(client):
    # Test the body API endpoint
    response = client.get("/api/body/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)


def test_office_route(client):
    # Test the office API endpoint
    response = client.get("/api/office/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)


def test_person_route(client):
    # Test the person API endpoint
    response = client.get("/api/person/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)


def test_term_route(client):
    # Test the term API endpoint
    response = client.get("/api/term/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)

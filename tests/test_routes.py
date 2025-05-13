# tests/test_routes.py

import pytest
import json
import os
import tempfile
from flask import url_for


def test_home_route(client):
    """Test the home route for unauthenticated users."""
    # Scenario 1: User is NOT authenticated
    response = client.get("/")  # Simulate GET request to the home route
    assert response.status_code == 302  # Check for redirect
    assert response.location.endswith("/login")  # Ensure redirect is to the login page


def test_home_route_authenticated(authenticated_client):
    """Test the home route for authenticated users."""
    # Scenario 2: User IS authenticated
    response = authenticated_client.get("/")  # Simulate another GET request
    assert response.status_code == 200  # Check for a successful response
    assert b"Refresh and View Reports" in response.data  # Check that the response's HTML contains expected content


def test_login_route_get(client):
    """Test GET request to login route."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_route_post_invalid(client):
    """Test POST request to login route with invalid credentials."""
    response = client.post("/login", data={
        "username": "nonexistent_user",
        "password": "wrong_password"
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check that we're still on the login page (login form is present)
    assert b'<form method="POST">' in response.data
    assert b'<input type="text" class="form-control" id="username" name="username" required>' in response.data
    assert b'<input type="password" class="form-control" id="password" name="password" required>' in response.data


def test_login_route_post_valid(client, app):
    """Test POST request to login route with valid credentials."""
    with app.app_context():
        from models.user import User
        from werkzeug.security import generate_password_hash
        from extensions import db

        # Create a test user
        user = User(
            username='loginuser',
            email='login@example.com',
            password='password'
        )
        user.role = 'admin'  # Set role after creation
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", data={
        "username": "loginuser",
        "password": "password"
    }, follow_redirects=True)
    assert response.status_code == 200

    # Check that we're redirected to the home page
    assert b"Refresh and View Reports" in response.data


def test_logout_route(authenticated_client):
    """Test logout route."""
    response = authenticated_client.get("/logout", follow_redirects=True)
    assert response.status_code == 200

    # Check that we're redirected to login page
    assert b"Login" in response.data


def test_favicon_route(client):
    """Test favicon route."""
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.mimetype == "image/vnd.microsoft.icon"


def test_protected_routes_unauthenticated(client):
    """Test that protected routes redirect to login when user is not authenticated."""
    protected_routes = [
        "/api/body/get",
        "/api/office/get",
        "/api/person/get",
        "/api/term/get",
        "/report/long",
        "/report/short",
        "/report/expirations",
        "/report/vacancies"
    ]

    for route in protected_routes:
        response = client.get(route)
        assert response.status_code == 302
        assert response.location.endswith("/login")


def test_api_routes_authenticated(authenticated_client, test_data):
    """Test API routes for authenticated users."""
    # Test body API endpoint
    response = authenticated_client.get("/api/body/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) == 2

    # Test office API endpoint
    response = authenticated_client.get("/api/office/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) == 3

    # Test person API endpoint
    response = authenticated_client.get("/api/person/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) == 3

    # Test term API endpoint
    response = authenticated_client.get("/api/term/get")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) == 3


def test_post_routes(authenticated_client, test_data):
    """Test POST requests to API routes."""
    # Test creating a new body
    response = authenticated_client.post("/api/body/add", json={
        "name": "New Test Body",
        "mission": "New Test Mission",
        "body_precedence": 3.0
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data.get("success") is True

    # Test creating a new office
    response = authenticated_client.post("/api/office/create", json={
        "title": "New Test Office",
        "office_precedence": 3.0,
        "office_body_id": 1
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data.get("success") is True

    # Test creating a new person
    response = authenticated_client.post("/api/person/add", json={
        "first": "New",
        "last": "Person",
        "email": "new@example.com",
        "phone": "(555) 123-4567",
        "apt": "404"
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data.get("success") is True

    # Test creating a new term
    response = authenticated_client.post("/api/term/add", json={
        "term_person_id": 1,
        "term_office_id": 3,
        "start": "2023-01-01",
        "end": "2025-12-31",
        "ordinal": "5th"
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data.get("success") is True


def test_report_routes(authenticated_client, test_data, app):
    """Test report routes."""
    # Define the report routes to test
    report_routes = [
        "/report/long",
        "/report/short",
        "/report/expirations",
        "/report/vacancies"
    ]

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create template files needed for testing in the temporary directory
        template_files = {
            "lfr_template.tex": "\\documentclass{article}\n\\begin{document}\n\\VAR{title}\n\\end{document}",
            "sfr_template.tex": "\\documentclass{article}\n\\begin{document}\n\\VAR{title}\n\\end{document}",
            "expirations_template.tex": "\\documentclass{article}\n\\begin{document}\n\\VAR{title}\n\\end{document}",
            "vacancies_template.tex": "\\documentclass{article}\n\\begin{document}\n\\VAR{title}\n\\end{document}"
        }

        for filename, content in template_files.items():
            with open(os.path.join(temp_dir, filename), "w", encoding="utf-8") as f:
                f.write(content)

        # Mock the app's config to use the temporary directory
        original_reports_dir = app.config['REPORTS_DIR']
        app.config['REPORTS_DIR'] = temp_dir

        # Mock the subprocess.run function to avoid actually running xelatex
        import subprocess
        original_run = subprocess.run

        def mock_run(*args, **kwargs):
            # Create a mock PDF file
            report_name = args[0][-1].split("\\")[-1].replace(".tex", ".pdf")
            with open(os.path.join(temp_dir, report_name), "w") as f:
                f.write("Mock PDF content")

            # Return a mock CompletedProcess object
            class MockCompletedProcess:
                def __init__(self):
                    self.returncode = 0
                    self.stdout = "Mock stdout"
                    self.stderr = "Mock stderr"

            return MockCompletedProcess()

        # Replace subprocess.run with our mock function
        subprocess.run = mock_run

        try:
            # Test each report route
            for route in report_routes:
                response = authenticated_client.get(route)
                assert response.status_code == 200
                json_data = response.get_json()
                assert json_data.get("success") is True
                assert "filename" in json_data

                # Check that the .tex file was created
                tex_filename = json_data["filename"].replace(".pdf", ".tex")
                tex_path = os.path.join(temp_dir, tex_filename)
                assert os.path.exists(tex_path)

                # Check the content of the .tex file
                with open(tex_path, "r", encoding="utf-8") as f:
                    tex_content = f.read()
                    assert "\\documentclass{article}" in tex_content
                    assert "\\begin{document}" in tex_content
                    assert "\\end{document}" in tex_content

        finally:
            # Restore the original subprocess.run function
            subprocess.run = original_run
            # Restore the original reports directory
            app.config['REPORTS_DIR'] = original_reports_dir

            # No need to clean up files as the temporary directory will be automatically deleted

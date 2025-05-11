import pytest
from flask import url_for
import os
import re
from models.letters import LetterTemplate
from extensions import db


def test_get_letters_html(authenticated_client):
    """Test the GET /api/letters/ route."""
    response = authenticated_client.get("/api/letters/")
    assert response.status_code == 200
    assert b"Letters And Template Management" in response.data
    assert b"Generate Letter" in response.data
    assert b"Available Letters" in response.data
    assert b"Current Template" in response.data

def test_create_template(authenticated_client, app):
    """Test the POST /api/letters/create_template route."""
    with app.app_context():
        # Make sure no template exists
        template = LetterTemplate.query.first()
        if template:
            db.session.delete(template)
            db.session.commit()

    # Create a new template
    response = authenticated_client.post("/api/letters/create_template", data={
        "header": "\\documentclass{article}\n\\begin{document}",
        "body": "\\end{document}"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Template created successfully!" in response.data

    # Check that the template was created in the database
    with app.app_context():
        template = LetterTemplate.query.first()
        assert template is not None
        assert template.header == "\\documentclass{article}\n\\begin{document}"
        assert template.body == "\\end{document}"

def test_update_template(authenticated_client, app):
    """Test the POST /api/letters/update_template route."""
    with app.app_context():
        # Make sure a template exists
        template = LetterTemplate.query.first()
        if not template:
            template = LetterTemplate(header="\\documentclass{article}\n\\begin{document}", body="\\end{document}")
            db.session.add(template)
            db.session.commit()

    # Update the template
    response = authenticated_client.post("/api/letters/update_template", data={
        "header": "\\documentclass{article}\n\\usepackage{geometry}\n\\begin{document}",
        "body": "\\section{Test}\nThis is a test.\n\\end{document}"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Template updated successfully!" in response.data

    # Check that the template was updated in the database
    with app.app_context():
        template = LetterTemplate.query.first()
        assert template is not None
        assert template.header == "\\documentclass{article}\n\\usepackage{geometry}\n\\begin{document}"
        assert template.body == "\\section{Test}\nThis is a test.\n\\end{document}"

def test_generate_letter(authenticated_client, app):
    """Test the POST /api/letters/generate_letter route."""
    import tempfile
    import unittest.mock as mock
    import subprocess

    with app.app_context():
        # Make sure a template exists
        template = LetterTemplate.query.first()
        if not template:
            template = LetterTemplate(header="\\documentclass{article}\n\\begin{document}", body="\\end{document}")
            db.session.add(template)
            db.session.commit()

    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define paths for the temporary files
        tex_path = os.path.join(temp_dir, "Smith.tex")
        pdf_path = os.path.join(temp_dir, "Smith.pdf")

        # Mock the subprocess.run function to avoid actually running xelatex
        def mock_run(*args, **kwargs):
            # Create a mock PDF file in our temporary directory
            with open(pdf_path, "w") as f:
                f.write("Mock PDF content")

            # Return a mock CompletedProcess object
            class MockCompletedProcess:
                def __init__(self):
                    self.returncode = 0
                    self.stdout = "Mock stdout"
                    self.stderr = "Mock stderr"

            return MockCompletedProcess()

        # Mock the os.path.join function to return our temporary file paths
        original_join = os.path.join
        def mock_join(*args, **kwargs):
            if args and args[-1] == "Smith.tex":
                return tex_path
            elif args and args[-1] == "Smith.pdf":
                return pdf_path
            return original_join(*args, **kwargs)

        # Apply the mocks
        with mock.patch('subprocess.run', side_effect=mock_run):
            with mock.patch('os.path.join', side_effect=mock_join):
                # Create a mock TEX file to simulate the letter generation
                with open(tex_path, "w") as f:
                    f.write("Mock TEX content")

                # Generate a letter
                response = authenticated_client.post("/api/letters/generate_letter", data={
                    "recipient": "John Smith",
                    "salutation": "Dear John",
                    "apartment": "101"
                }, follow_redirects=True)

                assert response.status_code == 200
                assert b"Letter for John Smith generated successfully!" in response.data

                # Check that the PDF file was created
                assert os.path.exists(pdf_path)

                # Check that the TEX file was created
                assert os.path.exists(tex_path)

                # No need to clean up as the temporary directory will be automatically removed

def test_view_pdf(authenticated_client, app):
    """Test the POST /api/letters/view_pdf route."""
    import unittest.mock as mock
    import io
    from flask import send_file

    # Create a mock PDF content in memory
    pdf_content = io.BytesIO(b"Mock PDF content")

    # Mock the os.path.exists function to always return True for any path
    def mock_exists(path):
        return True

    # Mock the send_file function to return our in-memory PDF content
    def mock_send_file(path, mimetype):
        return send_file(
            pdf_content,
            mimetype=mimetype,
            as_attachment=False,
            download_name="test.pdf"
        )

    # Apply the mocks
    with mock.patch('os.path.exists', side_effect=mock_exists):
        with mock.patch('flask.send_file', side_effect=mock_send_file):
            # View the PDF
            response = authenticated_client.post("/api/letters/view_pdf", data={
                "pdf_file": "test.pdf"
            })

            assert response.status_code == 200
            assert response.mimetype == "application/pdf"

def test_delete_pdf(authenticated_client, app):
    """Test the POST /api/letters/delete_pdf route."""
    import tempfile
    import unittest.mock as mock

    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock PDF file in the temporary directory
        pdf_path = os.path.join(temp_dir, "test_delete.pdf")
        with open(pdf_path, "w") as f:
            f.write("Mock PDF content")

        # Mock the os.path.join and os.remove functions
        original_join = os.path.join
        original_remove = os.remove

        def mock_join(*args, **kwargs):
            if args and args[-1] == "test_delete.pdf":
                return pdf_path
            return original_join(*args, **kwargs)

        def mock_remove(path):
            if path == pdf_path:
                # Actually remove the file to simulate the delete operation
                original_remove(path)
            else:
                original_remove(path)

        # Apply the mocks
        with mock.patch('os.path.join', side_effect=mock_join):
            with mock.patch('os.remove', side_effect=mock_remove):
                # Delete the PDF
                response = authenticated_client.post("/api/letters/delete_pdf", data={
                    "pdf_file": "test_delete.pdf"
                }, follow_redirects=True)

                assert response.status_code == 200
                assert b"Deleted test_delete.pdf" in response.data

                # Check that the PDF file was deleted
                assert not os.path.exists(pdf_path)

# tests/test_models.py

import pytest
from app import create_app
from extensions import db


@pytest.fixture
def client_with_db():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.testing = True
    with app.app_context():
        db.create_all()  # Set up tables
        yield app.test_client()
        db.drop_all()

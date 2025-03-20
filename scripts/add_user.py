from app import app
from models import db, User

with app.app_context():
    # Add a sample user
    if User.query.filter_by(username='testuser').first() is None:  # Avoid duplicates
        test_user = User(username='testuser', email='testuser@example.com', password='testpassword')
        db.session.add(test_user)
        db.session.commit()
        print("Test user added!")
    else:
        print("Test user already exists!")


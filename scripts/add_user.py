import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models.user import db, User

app = create_app()
with app.app_context():
    # Add a sample user
    if User.query.filter_by(username='geo@loyola.edu').first() is None:  # Avoid duplicates
        test_user = User(username='geo@loyola.edu', email='geo@loyola.edu', password='e/a0X2ZqT&1f1Y4~clSz')
        test_user.role = 'admin'  # Set role to admin
        db.session.add(test_user)
        db.session.commit()
        print("Test admin user added!")
    else:
        # Update existing user to admin role if not already
        test_user = User.query.filter_by(username='geo@loyola.edu').first()
        if test_user.role != 'admin':
            test_user.role = 'admin'
            db.session.commit()
            print("Existing user updated to admin role!")
        else:
            print("Test admin user already exists!")

import unittest
import sys
import os
import json
from flask import url_for

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from extensions import db
from models.user import User

class DualRoutesTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        import tempfile
        self.db_fd, self.db_path = tempfile.mkstemp()

        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.db_path}',
            'SECRET_KEY': 'test_key',
            'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
            'DATABASE': self.db_path,  # Add this for init_db to work
            'BACKUP_DIR': 'files_db_backups',  # Add these for the index route
            'REPORTS_DIR': 'files_roster_reports',
            'DB_PATH': 'instance/clerk.sqlite3'  # Add this for database operations
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create tables
        db.create_all()

        # Create a test user and log in
        self.create_test_user()
        self.login()

        # Create a test body for office tests
        self.create_test_body()

        # Create a test person and office for term tests
        self.create_test_person()
        self.create_test_office()

    def tearDown(self):
        # Ensure all database connections are closed
        db.session.remove()
        db.engine.dispose()
        self.app_context.pop()

        # Clean up the temporary database file
        import os
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            # On Windows, sometimes the file is still in use
            # We'll just leave it for the OS to clean up later
            pass

    def create_test_user(self):
        """Create a test user for authentication"""
        user = User(username='testuser', email='test@example.com', password='password')
        user.role = 'admin'  # Give admin role to access all endpoints
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id

    def login(self):
        """Log in as the test user"""
        response = self.client.post('/login', 
                                  data={'username': 'testuser', 'password': 'password'},
                                  follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def create_test_body(self):
        """Create a test body for office tests"""
        response = self.client.post('/api/body/add', 
                                   json={'name': 'Test Body', 'mission': 'Test Mission', 'precedence': 1},
                                   content_type='application/json')
        print(f"Body add response: {response.data}")
        data = json.loads(response.data)
        # Check if we got a success response
        if 'success' in data and data['success']:
            self.body_id = data.get('id')
        else:
            print(f"Failed to create test body: {data}")
            raise Exception(f"Failed to create test body: {data}")
        return data

    def create_test_person(self):
        """Create a test person for term tests"""
        response = self.client.post('/api/person/add', 
                                   json={'first': 'Test', 'last': 'Person', 'email': 'test@example.com'},
                                   content_type='application/json')
        data = json.loads(response.data)
        self.person_id = data['id']
        return data

    def create_test_office(self):
        """Create a test office for term tests"""
        response = self.client.post('/api/office/add', 
                                   json={'title': 'Test Office', 'body_id': self.body_id, 'precedence': 1},
                                   content_type='application/json')
        data = json.loads(response.data)
        self.office_id = data['id']
        return data

    def test_office_add_create_routes(self):
        """Test that /add and /create routes for office behave identically"""
        # Test /add route
        add_response = self.client.post('/api/office/add', 
                                      json={'title': 'Office Add', 'body_id': self.body_id, 'precedence': 2},
                                      content_type='application/json')
        self.assertEqual(add_response.status_code, 200)
        add_data = json.loads(add_response.data)
        self.assertTrue(add_data['success'])
        self.assertEqual(add_data['title'], 'Office Add')

        # Test /create route
        create_response = self.client.post('/api/office/create', 
                                         json={'title': 'Office Create', 'body_id': self.body_id, 'precedence': 3},
                                         content_type='application/json')
        self.assertEqual(create_response.status_code, 200)
        create_data = json.loads(create_response.data)
        self.assertTrue(create_data['success'])
        self.assertEqual(create_data['title'], 'Office Create')

        # Verify both were added by checking the /get route
        get_response = self.client.get('/api/office/get')
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.data)

        # Should have 3 offices (test_office, office_add, office_create)
        self.assertEqual(len(get_data), 3)

        # Verify the titles are present
        titles = [office['title'] for office in get_data]
        self.assertIn('Office Add', titles)
        self.assertIn('Office Create', titles)

    def test_term_add_create_routes(self):
        """Test that /add and /create routes for term behave identically"""
        # Test /add route
        add_response = self.client.post('/api/term/add', 
                                      json={
                                          'person_id': self.person_id, 
                                          'office_id': self.office_id,
                                          'start': '2023-01-01',
                                          'end': '2023-12-31'
                                      },
                                      content_type='application/json')
        self.assertEqual(add_response.status_code, 200)
        add_data = json.loads(add_response.data)
        self.assertTrue(add_data['success'])

        # Create a new person and office for the create route test
        new_person = self.client.post('/api/person/add', 
                                    json={'first': 'Another', 'last': 'Person', 'email': 'another@example.com'},
                                    content_type='application/json')
        new_person_data = json.loads(new_person.data)
        new_person_id = new_person_data['id']

        new_office = self.client.post('/api/office/add', 
                                    json={'title': 'Another Office', 'body_id': self.body_id, 'precedence': 4},
                                    content_type='application/json')
        new_office_data = json.loads(new_office.data)
        new_office_id = new_office_data['id']

        # Test /create route
        create_response = self.client.post('/api/term/create', 
                                         json={
                                             'person_id': new_person_id, 
                                             'office_id': new_office_id,
                                             'start': '2023-01-01',
                                             'end': '2023-12-31'
                                         },
                                         content_type='application/json')
        self.assertEqual(create_response.status_code, 200)
        create_data = json.loads(create_response.data)
        self.assertTrue(create_data['success'])

        # Verify both were added by checking the /get route
        get_response = self.client.get('/api/term/get')
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.data)

        # Should have 2 terms
        self.assertEqual(len(get_data), 2)

    def test_get_routes(self):
        """Test all /get routes to ensure they return expected data"""
        # Test body/get
        body_response = self.client.get('/api/body/get')
        self.assertEqual(body_response.status_code, 200)
        body_data = json.loads(body_response.data)
        self.assertEqual(len(body_data), 1)  # Should have our test body

        # Test office/get
        office_response = self.client.get('/api/office/get')
        self.assertEqual(office_response.status_code, 200)
        office_data = json.loads(office_response.data)
        self.assertEqual(len(office_data), 1)  # Should have our test office

        # Test person/get
        person_response = self.client.get('/api/person/get')
        self.assertEqual(person_response.status_code, 200)
        person_data = json.loads(person_response.data)
        self.assertEqual(len(person_data), 1)  # Should have our test person

        # Test term/get
        term_response = self.client.get('/api/term/get')
        self.assertEqual(term_response.status_code, 200)
        term_data = json.loads(term_response.data)
        self.assertEqual(len(term_data), 0)  # No terms yet

    def test_get_by_id(self):
        """Test /get routes with ID parameters"""
        # Test body/get with ID
        body_response = self.client.get(f'/api/body/get?id={self.body_id}')
        self.assertEqual(body_response.status_code, 200)
        body_data = json.loads(body_response.data)
        self.assertEqual(body_data['name'], 'Test Body')

        # Test office/get with ID
        office_response = self.client.get(f'/api/office/get?id={self.office_id}')
        self.assertEqual(office_response.status_code, 200)
        office_data = json.loads(office_response.data)
        self.assertEqual(office_data['title'], 'Test Office')

        # Test person/get with ID
        person_response = self.client.get(f'/api/person/get?id={self.person_id}')
        self.assertEqual(person_response.status_code, 200)
        person_data = json.loads(person_response.data)
        self.assertEqual(person_data['last'], 'Person')

if __name__ == '__main__':
    unittest.main()

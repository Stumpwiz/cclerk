import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from flask import url_for

class RouteIntegrityTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test_key'
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_all_routes(self):
        """Test all routes to verify they return a valid response."""
        # Dictionary to store routes and their status codes
        route_results = {}

        # Auth routes
        route_results['/login'] = self.client.get('/login').status_code
        route_results['/logout'] = self.client.get('/logout').status_code

        # Main routes
        route_results['/'] = self.client.get('/').status_code
        route_results['/favicon.ico'] = self.client.get('/favicon.ico').status_code

        # API routes - Letters
        route_results['/api/letters/'] = self.client.get('/api/letters/').status_code

        # API routes - Body
        route_results['/api/body/get'] = self.client.get('/api/body/get').status_code
        route_results['/api/body/view'] = self.client.get('/api/body/view').status_code

        # API routes - Office
        route_results['/api/office/get'] = self.client.get('/api/office/get').status_code
        route_results['/api/office/view'] = self.client.get('/api/office/view').status_code

        # API routes - Person
        route_results['/api/person/get'] = self.client.get('/api/person/get').status_code
        route_results['/api/person/view'] = self.client.get('/api/person/view').status_code

        # API routes - Term
        route_results['/api/term/get'] = self.client.get('/api/term/get').status_code
        route_results['/api/term/view'] = self.client.get('/api/term/view').status_code

        # Report routes
        route_results['/report/long'] = self.client.get('/report/long').status_code
        route_results['/report/short'] = self.client.get('/report/short').status_code
        route_results['/report/expirations'] = self.client.get('/report/expirations').status_code
        route_results['/report/vacancies'] = self.client.get('/report/vacancies').status_code

        # Admin routes
        route_results['/admin/users'] = self.client.get('/admin/users').status_code

        # Print results
        print("\nRoute Integrity Test Results:")
        print("============================")
        for route, status_code in route_results.items():
            status = "OK" if status_code in [200, 302, 401, 403] else "FAIL"
            print(f"{route}: {status_code} - {status}")

        # Check if any routes failed
        failed_routes = {route: status for route, status in route_results.items() 
                         if status not in [200, 302, 401, 403]}

        if failed_routes:
            print("\nFailed Routes:")
            for route, status in failed_routes.items():
                print(f"{route}: {status}")

        self.assertEqual(len(failed_routes), 0, f"Failed routes: {failed_routes}")

if __name__ == '__main__':
    unittest.main()

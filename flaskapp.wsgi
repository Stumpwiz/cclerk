# Required for production environment on Oberhaus.

import sys
import os
from dotenv import load_dotenv

# Ensure the app directory is in the Python path
sys.path.insert(0, "C:/FlaskApp")
os.environ['PYTHONUNBUFFERED'] = '1'

load_dotenv("C:/FlaskApp/.env")
from app import create_app

try:
    application = create_app()
except Exception as e:
    import traceback
    with open("C:/FlaskApp/wsgi_error.log", "w") as f:
        traceback.print_exc(file=f)
    raise

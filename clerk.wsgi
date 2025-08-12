# /var/www/clerk-app/clerk.wsgi
import os, sys, logging
sys.path.insert(0, "/var/www/clerk-app")

# Load env vars from .env
try:
    from dotenv import load_dotenv
    load_dotenv("/var/www/clerk-app/.env")
except Exception:
    pass  # keep going even if dotenv isn't installed

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])

from app import create_app  # adjust if your factory lives elsewhere
application = create_app()
logging.info("WSGI app loaded")

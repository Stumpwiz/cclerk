import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    INSTANCE_PATH = os.getenv("INSTANCE_PATH", "instance")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


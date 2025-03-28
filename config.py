import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_PATH = os.getenv("INSTANCE_PATH", "instance")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "DATABASE_URL not set.")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

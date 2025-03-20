import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3

# Ensure the directory for the database exists
db_directory = "instance"
db_file = "clerk.sqlite3"
db_path = os.path.join(db_directory, db_file)

# Create the directory if it does not exist
if not os.path.exists(db_directory):
    os.makedirs(db_directory)

# Ensure a proper connection string
try:
    # Use an absolute path for SQLite database for reliability
    engine = create_engine(f"sqlite:///{os.path.abspath(db_path)}")
    Session = sessionmaker(bind=engine)
    session = Session()
    print(f"Database initialized successfully at {db_path}")
except sqlite3.OperationalError as e:
    print(f"An error occurred while initializing the database: {e}")
    print("Ensure the path is correct and the application has proper permissions.")

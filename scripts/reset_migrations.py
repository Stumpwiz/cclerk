import os
import shutil
import sqlite3

def reset_migrations():
    """
    Reset the Flask-Migrate/Alembic migration process by:
    1. Deleting all migration version files
    2. Providing instructions to reset the database
    """
    print("Starting migration reset process...")
    
    # Path to the migrations versions directory
    versions_dir = os.path.join('migrations', 'versions')
    
    # Check if the directory exists
    if os.path.exists(versions_dir):
        # Delete all files in the versions directory
        for filename in os.listdir(versions_dir):
            file_path = os.path.join(versions_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"Deleted: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Deleted directory: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        
        print(f"\nSuccessfully cleared all migration version files from {versions_dir}")
    else:
        # Create the directory if it doesn't exist
        os.makedirs(versions_dir)
        print(f"Created new versions directory at {versions_dir}")
    
    # Path to the SQLite database
    db_path = os.path.join('instance', 'clerk.sqlite3')
    
    # Check if the database exists
    if os.path.exists(db_path):
        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if alembic_version table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';")
            if cursor.fetchone():
                # Drop the alembic_version table
                cursor.execute("DROP TABLE alembic_version;")
                conn.commit()
                print("\nSuccessfully dropped the alembic_version table from the database.")
            else:
                print("\nThe alembic_version table does not exist in the database.")
            
            conn.close()
        except sqlite3.Error as e:
            print(f"\nError working with the database: {e}")
            print("You may need to manually delete the alembic_version table from the database.")
    else:
        print(f"\nDatabase file not found at {db_path}")
    
    print("\n=== Migration Reset Complete ===")
    print("\nNext steps:")
    print("1. Initialize a new migration with: flask db init")
    print("2. Create a new migration with: flask db migrate -m 'Initial migration'")
    print("3. Apply the migration with: flask db upgrade")
    print("\nNote: If you encounter any issues, you may need to manually delete the alembic_version table from the database.")

if __name__ == "__main__":
    reset_migrations()
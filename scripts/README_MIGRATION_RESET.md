# Migration Reset Process

This document provides instructions for resetting the Flask-Migrate/Alembic migration process when the database and migrations have become out of sync.

## Background

When working with Flask applications that use SQLAlchemy and Flask-Migrate (Alembic), sometimes the database schema and migration history can become out of sync. This can happen due to:

- Manual changes to the database schema
- Failed migrations
- Changes in model specifications
- Development across multiple branches

## Reset Process

We've created a script to help reset the migration process. The script will:

1. Delete all existing migration version files
2. Remove the `alembic_version` table from the database (if it exists)
3. Provide instructions for reinitializing the migration process

## Steps to Reset Migrations

1. **Backup your database**
   ```
   # You can use SQLite's .backup command or simply copy the file
   cp instance/clerk.sqlite3 instance/clerk_backup.sqlite3
   ```

2. **Run the reset script**
   ```
   python scripts/reset_migrations.py
   ```

3. **Initialize a new migration repository**
   ```
   flask db init
   ```
   Note: If you get an error saying the migrations directory already exists, you can safely delete the entire migrations directory and run `flask db init` again.

4. **Create a new migration based on current models**
   ```
   flask db migrate -m "Initial migration"
   ```

5. **Apply the migration to the database**
   ```
   flask db upgrade
   ```

## Troubleshooting

If you encounter issues:

1. **Database locked**: Make sure no other processes are using the database.

2. **Tables already exist**: If you get errors about tables already existing, you may need to drop and recreate the database:
   ```
   # Delete the database file
   rm instance/clerk.sqlite3
   
   # Run the application to create a new database with tables
   flask run
   
   # Then initialize migrations
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **Migration directory issues**: If you have problems with the migrations directory:
   ```
   # Remove the entire migrations directory
   rm -rf migrations
   
   # Reinitialize
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## After Reset

After successfully resetting the migrations:

1. Make sure all your models are correctly defined
2. Verify that the database schema matches your models
3. Test your application to ensure everything works correctly

## Future Migrations

For future schema changes, continue using the normal Flask-Migrate workflow:

1. Update your models
2. Generate a migration: `flask db migrate -m "Description of changes"`
3. Review the generated migration script
4. Apply the migration: `flask db upgrade`
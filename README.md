# MRRA Residents Council Clerk
This project supports clerical tasks assigned to the administrative assistant of the 
[Mercy Ridge Residents Council](https://mrra.online/).

![Build Status](https://img.shields.io/badge/status-passing-success)

## Description
The project is a web application that supports the administrative assistant of the MRRA Residents Council. The
administrative assistant is responsible for the following tasks:
- Welcome Letters Generation and Management;
- Management of the Database That Supports Committee Rosters;
- Generation of Rosters, Vacancy Report, and Expiring Terms Report.

This application supports all these tasks via a web interface.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Usage](#usage)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features
- Welcome Letters Generation and Management
- Management of the Database That Supports Committee Rosters
- Generation of Rosters, Vacancy Report, and Expiring Terms Report

## Getting Started
This project will first be hosted on a local server, using mod_wsgi on Apache.  The server will be hosted on a Windows 
server.  The server will be accessed via a web browser. More will be added as the project progresses.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Stumpwiz/cclerk
   ```
2. Navigate into the directory and set up the environment:
   ```bash
   cd repo
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage
Run the Flask app:
```bash
flask run
```
Visit [http://localhost:5000](http://localhost:5000).

## Database Migrations
This project uses Flask-Migrate (Alembic) to manage database migrations. The database is managed using SQLAlchemy, but
it is out of sync.  This needs to be fixed.

### Basic Migration Commands
- Initialize migrations: `flask db init`
- Create a migration: `flask db migrate -m "Description of changes"`
- Apply migrations: `flask db upgrade`

### Resetting Migrations
This needs to be fixed.

```bash
python scripts/reset_migrations.py
```

For detailed instructions on resetting migrations, see [scripts/README_MIGRATION_RESET.md](scripts/README_MIGRATION_RESET.md).

## Testing
Run all tests:
```bash
pytest
```

## Contributing
I'm not prepared to accept contributions at this time.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements
- [Flask](https://flask.palletsprojects.com)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [JetBrains' PyCharm with Junie](https://www.jetbrains.com/pycharm/)
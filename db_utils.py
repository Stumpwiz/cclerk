# db_utils.py

import sqlite3
from flask import current_app
import click
from flask.cli import with_appcontext


def init_db():
    db_path = current_app.config['DATABASE']
    with sqlite3.connect(db_path) as db:
        with open('schema.sql', 'r', encoding='utf-16') as f:
            db.executescript(f.read())



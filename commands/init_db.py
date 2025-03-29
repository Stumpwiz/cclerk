# commands/init_db.py

from flask.cli import with_appcontext
import click
from extensions import db
from models.letters import LetterTemplate
import os


@click.command("init-db")
@with_appcontext
def init_db():
    """Initialize the database with starter data for all models."""

    if LetterTemplate.query.count() == 0:
        from flask import current_app
        instance_path = os.path.join(current_app.instance_path, "letter_template")
        header_path = os.path.abspath(os.path.join(instance_path, "header.txt"))
        body_path = os.path.abspath(os.path.join(instance_path, "body.txt"))

        try:
            with open(header_path, "r", encoding="utf-8") as f:
                header = f.read()
            with open(body_path, "r", encoding="utf-8") as f:
                body = f.read()
        except FileNotFoundError:
            click.echo("ERROR: Could not find header.txt or body.txt in instance/letter_template/")
            return

        db.session.add(LetterTemplate(header=header, body=body))
        db.session.commit()
        click.echo("Letter template initialized from instance/letter_template .txt files.")
    else:
        click.echo("Letter template already exists. No action taken.")

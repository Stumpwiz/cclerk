# init_letter_template.py

from flask.cli import with_appcontext
import click
from extensions import db
from models.letters import LetterTemplate

@click.command("init-letter-template")
@with_appcontext
def init_letter_template():
    """Initialize the letters table with one placeholder template."""
    if LetterTemplate.query.count() == 0:
        template = LetterTemplate(
            header='\\Header Placeholder',
            body='\\Body Placeholder'
        )
        db.session.add(template)
        db.session.commit()
        click.echo("Letter template initialized with placeholder values.")
    else:
        click.echo("Letter template already exists. No action taken.")

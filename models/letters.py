# models/letters.py

from extensions import db

class LetterTemplate(db.Model):
    __tablename__ = 'letters'

    id = db.Column(db.Integer, primary_key=True)
    header = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)

    @staticmethod
    def get_singleton():
        """
        Fetch the single letter template record, or None if not present.
        """
        return LetterTemplate.query.first()

    @staticmethod
    def can_add_record():
        """
        Return True if the table is empty, i.e., no template exists yet.
        """
        return LetterTemplate.query.count() == 0

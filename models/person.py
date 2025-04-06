# models/person.py. An incumbent in a given office.

from extensions import db

class Person(db.Model):
    __tablename__ = 'person'

    person_id = db.Column('personid', db.Integer, primary_key=True, autoincrement=True)
    first = db.Column(db.String(15), nullable=True, default=None)
    last = db.Column(db.String(30), nullable=True, default=None)
    email = db.Column(db.String(45), nullable=True, default=None)
    phone = db.Column(db.String(19), nullable=True, default=None)
    apt = db.Column(db.String(4), nullable=True, default=None)
    person_image = db.Column('personimage', db.String(45), nullable=True, default=None)

    def __repr__(self):
        return f'<Person {self.first} {self.last}>'

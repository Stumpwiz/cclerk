# models/term.py.  The tenure of a given person in a given office, the junction record in the database to resolve
# the many-to-many relationship between persons and offices.

from extensions import db
from models.person import Person
from models.office import Office

class Term(db.Model):
    __tablename__ = 'term'

    # Composite primary key
    term_person_id = db.Column('termpersonid', db.Integer, db.ForeignKey('person.personid'), primary_key=True)
    term_office_id = db.Column('termofficeid', db.Integer, db.ForeignKey('office.office_id'), primary_key=True)
    
    # Other fields
    start = db.Column(db.Date, nullable=True, default=None)
    end = db.Column(db.Date, nullable=True, default=None)
    ordinal = db.Column(db.String(7), nullable=True, default=None)
    
    # Relationships
    person = db.relationship('Person', backref=db.backref('terms', lazy=True))
    office = db.relationship('Office', backref=db.backref('terms', lazy=True))
    
    def __repr__(self):
        return f'<Term {self.term_person_id}-{self.term_office_id}>'
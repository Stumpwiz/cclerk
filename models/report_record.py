# models/report_record.py — read-only SQLAlchemy model mapped to the report_record view

from extensions import db

class ReportRecord(db.Model):
    __tablename__ = 'report_record'
    __table_args__ = {'extend_existing': True}

    person_id = db.Column(db.Integer)
    first = db.Column(db.String)
    last = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    apt = db.Column(db.String)
    start = db.Column(db.Date)
    end = db.Column(db.Date)
    ordinal = db.Column(db.String)
    term_person_id = db.Column(db.Integer, primary_key=True)
    term_office_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer)
    title = db.Column(db.String)
    office_precedence = db.Column(db.Float)
    office_body_id = db.Column(db.Integer)
    body_id = db.Column(db.Integer)
    name = db.Column(db.String)
    body_precedence = db.Column(db.Float)

    def __repr__(self):
        return f'<ReportRecord {self.name} - {self.title} - {self.first} {self.last}>'

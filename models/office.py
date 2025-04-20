# models/office.py.  An area of responsibility for a given body.

from extensions import db

class Office(db.Model):
    __tablename__ = 'office'

    office_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(45), nullable=True, default=None)
    office_precedence = db.Column(db.Float, nullable=True, default=None)
    office_body_id = db.Column(db.BigInteger, db.ForeignKey('body.body_id'), nullable=False)
    
    # Relationship to easily fetch the related Body object
    body = db.relationship('Body', backref=db.backref('offices', lazy=True))

    def __repr__(self):
        return f'<Office {self.title}>'
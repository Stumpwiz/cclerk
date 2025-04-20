# models/body.py.  An administrative body that comprises various offices.

from extensions import db

class Body(db.Model):
    __tablename__ = 'body'

    body_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False)
    mission = db.Column(db.String(512), nullable=True, default=None)
    body_precedence = db.Column(db.Float, nullable=False,
                               comment="Used for ordering in reports and on web pages")

    def __repr__(self):
        return f'<Body {self.name}>'

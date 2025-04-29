from flask_wtf import FlaskForm

class CSRFForm(FlaskForm):
    """A form that only contains a CSRF token."""
    pass
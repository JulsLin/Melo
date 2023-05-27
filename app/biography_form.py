from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class BiographyForm(FlaskForm):
    """Form for adding artist biography

    Args:
        FlaskForm: Base class for creating forms in Flask.
    """
    biography = TextAreaField('Biography', validators=[DataRequired()])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(BiographyForm, self).__init__(*args, **kwargs)
        if 'obj' in kwargs and kwargs['obj'] is not None:
            self.biography.data = kwargs['obj'].artist_biography

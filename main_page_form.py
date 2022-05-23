from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import SubmitField, FileField


class MainForm(FlaskForm):
    load_inventory = FileField(validators=[FileAllowed(['txt', 'pdf', 'docx'], 'Text only!')])
    submit = SubmitField('Искать')
    logout = SubmitField('Выйти')
    items = []

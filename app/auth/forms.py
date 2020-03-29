from flask_wtf import FlaskForm
from wtforms import PasswordField,  SubmitField
from wtforms.validators import InputRequired


class LoginForm(FlaskForm):
    password = PasswordField('Password', validators=[InputRequired('Please enter your password')])
    submit = SubmitField('Login')

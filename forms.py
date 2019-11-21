from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import Email, Length, InputRequired, DataRequired

"""
[VARIABLE] = [FIELD TYPE]('[LABEL]', [
    validators=[VALIDATOR TYPE](message='[ERROR MESSAGE]')
])
"""
class RegisterForm(FlaskForm):
    email = StringField('email', [
        InputRequired(),
        Email(message='Invalid email'),
        Length(max=30, message='Your email is too long')
    ])
    password = PasswordField('password', [
        InputRequired(),
        Length(min=8, max=20, message='Your password is either too short or too long.')
    ])

class LoginForm(FlaskForm):
    email = StringField('email',  [
        InputRequired(),
        Email(message='Invalid email'),
        Length(max=30, message='Your email is too long')
    ])
    password = PasswordField('password', [
        InputRequired(),
        Length(min=8, max=20, message='Your password is either too short or too long.')
    ])

class CommentForm(FlaskForm):
    body = TextAreaField('Message', [
        DataRequired(),
        Length(min=4, message='Your message is too short.')
    ])
    submit = SubmitField('Submit')
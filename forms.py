from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import Email, Length, InputRequired, DataRequired, EqualTo

"""
[VARIABLE] = [FIELD TYPE]('[LABEL]', [
    validators=[VALIDATOR TYPE](message='[ERROR MESSAGE]')
])
"""


class RegisterForm(FlaskForm):
    name = StringField('name', [
        InputRequired(),
        Length(min=5, max=30)
    ])
    email = StringField('email', [
        InputRequired(),
        Email(message='Invalid email'),
        Length(max=30)
    ])
    password = PasswordField('password', [
        InputRequired(),
        EqualTo('confirm', message='Passwords must match'),
        Length(min=5, max=30, message='Your password is either too short or too long.')
    ])
    confirm = PasswordField('Repeat Password', [
        InputRequired()
    ])


class LoginForm(FlaskForm):
    email = StringField('email', [
        InputRequired(),
        Email(message='Invalid email'),
        Length(max=30, message='Your email is too long')
    ])
    password = PasswordField('password', [
        InputRequired(),
        Length(min=5, max=30, message='Your password is either too short or too long.')
    ])


class CommentForm(FlaskForm):
    body = TextAreaField('Message', [
        DataRequired(),
        Length(min=4, message='Your message is too short.')
    ])
    submit = SubmitField('Submit')

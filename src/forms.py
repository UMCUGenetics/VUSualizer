from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import Email, Length, InputRequired, DataRequired, EqualTo


class RegisterForm(FlaskForm):
    email = StringField('email', [
        InputRequired(),
        Email(message='Invalid email'),
        Length(max=60)
    ])
    password = PasswordField('password', [
        InputRequired(),
        EqualTo('confirm', message='Passwords must match'),
        Length(min=5, max=60, message='Your password is either too short or too long.')
    ])
    confirm = PasswordField('Repeat Password', [
        InputRequired()
    ])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('email', [
        InputRequired(),
        Email(message='Invalid email'),
        Length(max=60, message='Your email is too long')
    ])
    password = PasswordField('password', [
        InputRequired(),
        Length(min=5, max=30, message='Your password is either too short or too long.')
    ])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class CommentForm(FlaskForm):
    body = TextAreaField('Message', [
        DataRequired(),
        Length(min=4, message='Your message is too short.')
    ])
    submit = SubmitField('Submit')

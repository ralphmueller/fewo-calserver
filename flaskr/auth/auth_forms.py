'''
Created on 20.09.2021

WTF for auth

@author: ralph
'''
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length


class LoginForm(FlaskForm):
    """ Login form"""
    user = StringField(
        'Benutzer',
        [DataRequired()]
    )
    password = PasswordField(
        'password',
        [DataRequired()]
    )


class RegisterForm(FlaskForm):
    """ Login form"""
    user = StringField(
        'Benutzer',
        [DataRequired()]
    )
    password = PasswordField(
        'Password',
        [DataRequired()]
    )


class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('Neues Password', [
        DataRequired(),
        Length(min=8, message='Mindestens 8 Zeichen'),
        EqualTo('confirm', message='Passwörter müssen gleich sein!')
    ])
    confirm = PasswordField('Wiederholen')

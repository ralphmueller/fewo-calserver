'''
Created on 23.09.2021

WTF for auth

@author: ralph
'''
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField
from wtforms.fields.html5 import EmailField, DateField
from wtforms.validators import DataRequired, Email


class CreateBesucherForm(FlaskForm):
    """ Create form"""

    # TODO
    anrede = SelectField(
        'Anrede',
        [DataRequired()],
        choices=[
            (1, 'Familie'),
            (2, 'Herr'),
            (3, 'Frau'),
            (4, 'Firma')
        ]
    )

    name = StringField(
        'Name',
        [DataRequired()]
    )

    vorname = StringField(
        'Vorname',
        [DataRequired()]
    )

    firmenname = StringField(
        'Firmenname'
    )

    email = EmailField(
        'Email',
        [DataRequired(), Email()]
    )
    tel = StringField(
        'Telefon'
    )

    strasse = StringField(
        'Strasse',
        []
    )

    plz = StringField(
        'PLZ',
        []
    )

    stadt = StringField(
        'Stadt',
        []
    )

    land = StringField(
        'Land',
        []
    )

    vermerk = StringField(
        'Vermerk',
        []
    )

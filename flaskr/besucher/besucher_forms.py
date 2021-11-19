'''
Created on 23.09.2021

WTF for auth

@author: ralph
'''
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email
from flaskr.api import ANREDE, LANGUAGE


class BesucherForm(FlaskForm):
    """ Create/update form"""

    user_id = HiddenField()      # user of the app

    besucher_id = HiddenField()

    anrede = SelectField(
        'Anrede',
        [DataRequired()],
        choices=ANREDE
    )

    language = SelectField(
        'Bevorzugte Sprache',
        [DataRequired()],
        choices=LANGUAGE
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

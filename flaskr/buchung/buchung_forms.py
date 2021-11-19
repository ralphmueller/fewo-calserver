'''
Created on 04.10.2021

WTF for buchungen

@author: ralph
'''
from datetime import date, timedelta
from flask_wtf import FlaskForm
from wtforms import SelectField, HiddenField, TextAreaField, StringField
from wtforms.fields.html5 import (
    DateField,
    DecimalField,
    IntegerField)
from wtforms.validators import DataRequired
from bkormlib import Portal, Apartment, StaticValuesBuchung


class BuchungForm(FlaskForm):
    """ Create buchung form, step 1"""

    mwstsatz = HiddenField(
        'MwStSatz',
        default=StaticValuesBuchung.mwstsatz()
    )

    ktsatz_vz = HiddenField(
        'KTSatzVZ',
        default=StaticValuesBuchung.ktsatz_vz()
    )

    ktsatz_hz = HiddenField(
        'KTSatzHZ',
        default=StaticValuesBuchung.ktsatz_hz()
    )

    id = HiddenField()

    besucher_id = HiddenField()

    apartment_id = SelectField(
        'Apartment',
        [DataRequired()],
        choices=Apartment.choices()
    )

    portal_id = SelectField(
        'Portal',
        [DataRequired()],
        choices=Portal.choices()
    )

    anreise = DateField(
        'Anreise',
        [DataRequired()],
        default=date.today()
    )

    abreise = DateField(
        'Abreise',
        [DataRequired()],
        default=date.today() + timedelta(days=2)
    )

    kurtaxe_vz = IntegerField(
        'Erwachsene / Jugendliche ab 15J',
        default=2
    )

    kurtaxe_hz = IntegerField(
        'Kinder 10-15J',
        default=0
    )

    kurtaxe_kinder = IntegerField(
        'Kinder unter 10J',
        default=0
    )
    kurtaxe_nz = IntegerField(
        'Kurtaxe befreit',
        default=0
    )

    preis_nacht = DecimalField(
        'Preis/Nacht',
        default=0.0
    )

    rabatt = DecimalField(
        'Rabatt(%)',
        default=0
    )

    zusatzkosten = DecimalField(
        'Zusatzkosten',
        default=0.0
    )

    vorauszahlung = DecimalField(
        'Vorauszahlung',
        default=0.0
    )

    notiz = TextAreaField(
        'Notiz',
        default=''
    )


class Buchung2Form(FlaskForm):
    """
        Create buchung form, step 2
    """

    email_text = TextAreaField(
        'Buchungsbestätigung',
        render_kw={'rows': "50", 'cols': "80"}
    )


class MeldescheinForm(FlaskForm):
    """
        Erfassen Meldeschein Nr
    """

    meldeschein_nummer = StringField(
        'Meldeschein',
        default=''
    )

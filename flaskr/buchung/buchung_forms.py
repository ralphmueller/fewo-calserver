'''
Created on 04.10.2021

WTF for buchungen

@author: ralph
'''
from datetime import date, timedelta
from flask_wtf import FlaskForm
from wtforms import SelectField, HiddenField
from wtforms.fields.html5 import (
    DateField,
    DecimalField,
    IntegerField)

from wtforms.validators import DataRequired

from bkormlib import Portal, Apartment, StaticValuesBuchung


class BuchungForm(FlaskForm):
    """ Create/update form"""

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
    besucher_id = HiddenField(
        [DataRequired()]
    )

    apartment = SelectField(
        'Apartment',
        [DataRequired()],
        choices=Apartment.choices()
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
        'Erwachsene',
        [DataRequired()],
        default=2
    )

    kurtaxe_hz = IntegerField(
        'Kinder 10-15J',
        [DataRequired()],
        default=0
    )

    kurtaxe_kinder = IntegerField(
        'Kinder',
        [DataRequired()],
        default=0
    )
    kurtaxe_nz = IntegerField(
        'Kurtaxe befreit',
        [DataRequired()],
        default=0,
        render_kw={'class':'myclass','style':'font-size:150%;color:green'}
    )

    kurtaxe = DecimalField(
        'Kurtaxe',
        default=0.0
    )

    preis_nacht = DecimalField(
        'Preis/Nacht',
        default=0.0
    )

    rabatt = DecimalField(
        'Rabatt(%)',
        default=0.0
    )

    zusatzkosten = DecimalField(
        'Zusatzkosten',
        default=0.0
    )

    portal = SelectField(
        'Portal',
        [DataRequired()],
        choices=Portal.choices()
    )

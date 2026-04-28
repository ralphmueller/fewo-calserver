from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional


class WareForm(FlaskForm):
    bezeichnung = StringField('Bezeichnung', [DataRequired()])
    preis = DecimalField('Preis (€)', [DataRequired()], places=2)
    mwst_satz = SelectField(
        'MwSt.-Satz',
        choices=[(19, '19%'), (7, '7%')],
        coerce=int
    )
    mindestbestand = IntegerField('Mindestbestand', default=0)
    lieferant = StringField('Lieferant', [Optional()])
    active = BooleanField('Aktiv')


class WareLieferungForm(FlaskForm):
    zugang = IntegerField('Lieferung (Stück)', default=0)

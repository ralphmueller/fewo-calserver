'''
Created on 23.09.2021

WTF for auth

@author: ralph
'''
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField    # DateField
from wtforms.fields.html5 import EmailField     #  DateField
from wtforms.validators import DataRequired, Email
from flaskr.api import ANREDE, anrede_for_key


class BesucherForm(FlaskForm):
    """ Create/update form"""

    besucher_id = HiddenField()

    anrede = SelectField(
        'Anrede',
        [DataRequired()],
        choices=ANREDE
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

    def update_besucher(self, besucher):
        '''
            update besucher: check which fields need updating

        '''

        if besucher.anrede != anrede_for_key(self.anrede.data):
            besucher.anrede = anrede_for_key(self.anrede.data)
        if besucher.name != self.name.data:
            besucher.name = self.name.data
        if besucher.vorname != self.vorname.data:
            besucher.vorname = self.vorname.data
        if besucher.tel != self.tel.data:
            besucher.tel = self.tel.data
        if besucher.email != self.email.data:
            besucher.email = self.email.data
        if besucher.stadt != self.stadt.data:
            besucher.stadt = self.stadt.data
        if besucher.plz != self.plz.data:
            besucher.plz = self.plz.data
        if besucher.strasse != self.strasse.data:
            besucher.strasse = self.strasse.data
        if besucher.vermerk != self.vermerk.data:
            besucher.vermerk = self.vermerk.data
        if besucher.is_dirty():
            besucher.save()
            return "Daten für {}, {} gespeichert".format(
                besucher.name, besucher.vorname
            )
        return "Keine Änderungen für {}, {}".format(
                besucher.name, besucher.vorname)

'''
Created on 23.09.2021

WTF for auth

@author: ralph
'''
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField    #  DateField
from wtforms.fields.html5 import EmailField     #  DateField
from wtforms.validators import DataRequired, Email
from flaskr.api import ANREDE, fetch_besucher_for_update, anrede_for_key


class BesucherForm(FlaskForm):
    """ Create/update form"""

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

    def data_from_besucher(self, besucher):

        for c in ANREDE:
            if c[1] == besucher.anrede:
                anrede = c[0]

        self.anrede.data = anrede
        self.name.data = besucher.name
        self.vorname.data = besucher.vorname
        self.email.data = besucher.email
        self.tel.data = besucher.tel
        self.strasse.data = besucher.strasse
        self.plz.data = besucher.plz
        self.stadt.data = besucher.stadt
        self.land.data = besucher.land
        self.vermerk.data = besucher.vermerk

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

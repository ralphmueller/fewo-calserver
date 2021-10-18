'''
Created on 19.09.2021

API to models and helper functions

@author: ralph
'''

from peewee import fn
from bkormlib import Besucher, Buchung, Apartment, StaticValuesBuchung, Portal

# choices and helper fucntions for dropdowns in Besucher forms
ANREDE = [('1', 'Fam.'), ('2', 'Herr'), ('3', 'Frau'), ('4', 'Firma')]


class FlaskrTemplate():
    @classmethod
    def get_bestaetigungstemplate(cls):
        return 'Das ist das Bestätigungstemplate'

    @classmethod
    def get_changetemplate(cls):
        return 'Das ist das Changetemplate'

    @classmethod
    def get_stornotemplate(cls):
        return 'Das ist das Stornotemplate'


def anrede_for_key(key):
    # TODO : check for out of index
    return [item for item in ANREDE if item[0] == key][0][1]


def key_for_anrede(anrede):
    # TODO : check for out of index
    return [item for item in ANREDE if item[1] == anrede][0][0]


def fetch_visitors():
    ''' get full list of visitors'''
    query = (
        Besucher
        .select()
        .order_by(Besucher.name)
    )
    if len(list(query)) > 0:
        return list(query)
    return None


def create_besucher_from_form(form):
    ''' create new visitor from form data '''
    besucher = Besucher()
    besucher.anrede = anrede_for_key(form.anrede.data)
    besucher.name = form.name.data
    besucher.vorname = form.vorname.data
    besucher.email = form.email.data
    besucher.tel = form.tel.data
    besucher.plz = form.plz.data
    besucher.name = form.name.data
    besucher.stadt = form.stadt.data
    besucher.strasse = form.strasse.data
    besucher.land = form.land.data
    besucher.vermerk = form.vermerk.data
    besucher.save()
    return besucher.id, besucher.name, besucher.vorname


def create_buchung_from_form(form):
    ''' create new visitor from form data '''
    print('Form data', str(form.data))
    buchung = Buchung()
    buchung.status = 'temp'
    buchung.besucher_id = form.besucher_id
    buchung.portal_id = form.portal_id.data
    buchung.anreise = form.anreise.data
    buchung.abreise = form.abreise.data
    buchung.preis_nacht = form.preis_nacht.data
    buchung.rabatt = form.rabatt.data
    buchung.zusatzkosten = form.zusatzkosten.data
    buchung.kurtaxe_vz = form.kurtaxe_vz.data
    buchung.kurtaxe_hz = form.kurtaxe_hz.data
    buchung.kurtaxe_nz = form.kurtaxe_nz.data
    buchung.kurtaxe_kinder = form.kurtaxe_kinder.data
    nights = (buchung.abreise - buchung.anreise).days
    print(buchung.get_preis_nacht(), buchung.get_rabatt())
    buchung.miete = (
        buchung.get_preis_nacht() * nights *
        (1.0 - buchung.get_rabatt()/100.0) +
        buchung.get_zusatzkosten()
    )
    buchung.kurtaxe = (
        (
            buchung.get_kurtaxe_vz() * form.ktsatz_vz.data +
            buchung.get_kurtaxe_hz() * form.ktsatz_hz.data
        ) * nights
    )

    return buchung


def fetch_besucher_for_update(id):
    """ """
    besucher = Besucher.get(Besucher.id == id)
    buchungen = (
        Buchung
        .select(Buchung, Apartment)
        .join(Apartment)
        .where(Buchung.besucher == besucher).order_by(Buchung.anreise.desc())
    )
    return besucher, list(buchungen)


def update_besucher(form, besucher):
    '''
        update besucher: check which fields need updating

    '''

    if besucher.anrede != anrede_for_key(form.anrede.data):
        besucher.anrede = anrede_for_key(form.anrede.data)
    if besucher.name != form.name.data:
        besucher.name = form.name.data
    if besucher.vorname != form.vorname.data:
        besucher.vorname = form.vorname.data
    if besucher.tel != form.tel.data:
        besucher.tel = form.tel.data
    if besucher.email != form.email.data:
        besucher.email = form.email.data
    if besucher.stadt != form.stadt.data:
        besucher.stadt = form.stadt.data
    if besucher.plz != form.plz.data:
        besucher.plz = form.plz.data
    if besucher.strasse != form.strasse.data:
        besucher.strasse = form.strasse.data
    if besucher.vermerk != form.vermerk.data:
        besucher.vermerk = form.vermerk.data
    if besucher.is_dirty():
        besucher.save()
        return "Daten für {}, {} gespeichert".format(
            besucher.name, besucher.vorname
        )
    return "Keine Änderungen für {}, {}".format(
            besucher.name, besucher.vorname)


def delete_besucher(id):
    """ delete besucher if no related objects exist"""
    besucher = Besucher.get(Besucher.id == id)
    no_buchungen = (
        Buchung
        .select(fn.Count(Buchung.id))
        .alias('count')
        .where(Buchung.besucher == besucher).scalar()
    )

    if no_buchungen > 0:
        return (
            'Besucher {}, {} wurde nicht gelöscht, da {} Buchungen existieren!'
            .format(besucher.name, besucher.vorname, no_buchungen)
        )
    else:
        besucher.delete_instance()
        return (
            'Besucher {}, {} gelöscht'.
            format(besucher.name, besucher.vorname)
        )



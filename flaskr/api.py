'''
Created on 19.09.2021

API to models and helper functions

@author: ralph
'''

from peewee import fn
from bkormlib import Besucher, Buchung, Apartment

ANREDE = {1: 'Fam', 2: 'Herr', 3: 'Frau', 4: 'Firma'}


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
    besucher.anrede = ANREDE[int(form.anrede.data)]
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


def update_besucher_from_form(id, form):
    '''
        update besucher: check which fields need updating

        TODO: move to api.py
    '''
    besucher = Besucher.get(Besucher.id == id)

    if besucher.anrede != form["anrede"]:
        besucher.anrede = form["anrede"]
    if besucher.name != form["name"]:
        besucher.name = form["name"]
    if besucher.vorname != form["vorname"]:
        besucher.vorname = form["vorname"]
    if besucher.tel != form["tel"]:
        besucher.tel = form["tel"]
    if besucher.email != form["email"]:
        besucher.email = form["email"]
    if besucher.stadt != form["stadt"]:
        besucher.stadt = form["stadt"]
    if besucher.plz != form["plz"]:
        besucher.plz = form["plz"]
    if besucher.strasse != form["strasse"]:
        besucher.strasse = form["strasse"]
    if besucher.vermerk != form["vermerk"]:
        besucher.vermerk = form["vermerk"]
    if besucher.is_dirty():
        besucher.save()
        return "Daten für {}, {} gespeichert".format(
            besucher.name, besucher.vorname
        )
    return 'Keine Änderungen'


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

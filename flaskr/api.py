'''
Created on 19.09.2021

API to models and helper functions

@author: ralph
'''

from peewee import fn
from bkormlib import Besucher, Buchung, Apartment

# choices and helper fucntions for dropdowns in Besucher forms
ANREDE = [('1', 'Fam.'), ('2', 'Herr'), ('3', 'Frau'), ('4', 'Firma')]


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


def update_buchung(form, buchung):
    """
        check the relevant buchung fields, recalc and save if needed
        Note: change in vorauszahlung has to be handled differntly
              with an email notice to visitor
    """
    if buchung.anreise != form.anreise.data:
        buchung.anreise = form.anreise.data

    if buchung.abreise != form.abreise.data:
        buchung.abreise = form.abreise.data

    if buchung.get_preis_nacht() != form.get_preis_nacht().data:
        buchung.preis_nacht = form.preis_nacht.data

    if buchung.get_zusatzkosten() != form.get_zusatzkosten().data:
        buchung.zusatzkosten = form.zusatzkosten.data

    if buchung.get_rabatt() != form.get_rabatt().data:
        buchung.rabatt = form.rabatt.data

    if buchung.get_vorauszahlung() != form.get_vorauszahlung().data:
        buchung.vorauszahlung = form.vorauszahlung.data

    if buchung.get_portal() != form.get_portal().data:
        buchung.portal = form.portal.data

    if buchung.get_kurtaxe_vz() != form.get_kurtaxe_vz().data:
        buchung.kurtaxe_vz = form.kurtaxe_vz.data

    if buchung.get_kurtaxe_hz() != form.get_kurtaxe_hz().data:
        buchung.kurtaxe_hz = form.kurtaxe_hz.data

    if buchung.get_kurtaxe_kinder() != form.get_kurtaxe_kinder().data:
        buchung.kurtaxe_kinder = form.kurtaxe_kinder.data

    if buchung.get_kurtaxe_nz() != form.get_kurtaxe_nz().data:
        buchung.kurtaxe_nz = form.kurtaxe_nz.data

    if buchung.get_notiz() != form.get_notiz().data:
        buchung.notiz = form.notiz.data

    if buchung.is_dirty():
        buchung.recalc().save()
        return True
    else:
        return False

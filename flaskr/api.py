'''
Created on 19.09.2021

API to models and helper functions

@author: ralph
'''

from peewee import fn
from bkormlib import Besucher, Buchung, Apartment, Email

from babel.dates import format_date

from flask import current_app, render_template
from flaskr import mailer

# choices and helper fucntions for dropdowns in Besucher forms
ANREDE = [('1', 'Fam.'), ('2', 'Herr'), ('3', 'Frau'), ('4', 'Firma')]
LANGUAGE = [('1', 'DE'), ('2', 'EN'), ('3', 'FR')]


def anrede_for_key(key):
    # TODO : check for out of index
    return [item for item in ANREDE if item[0] == key][0][1]


def language_for_key(key):
    # TODO : check for out of index
    return [item for item in LANGUAGE if item[0] == key][0][1]


def key_for_anrede(anrede):
    # TODO : check for out of index
    return [item for item in ANREDE if item[1] == anrede][0][0]


def key_for_language(language):
    # TODO : check for out of index
    return [item for item in LANGUAGE if item[1] == language][0][0]


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
    besucher.language = form.language.data
    besucher.save()
    return besucher.id, besucher.name, besucher.vorname


def fetch_besucher_for_update(besucher_id):
    """ """
    besucher = Besucher.get_by_id(besucher_id)
    buchungen = (
        Buchung
        .select(Buchung, Apartment)
        .join(Apartment)
        .where(Buchung.besucher == besucher).order_by(Buchung.anreise.desc())
    )
    return besucher, list(buchungen)


def delete_besucher(besucher_id):
    """ delete besucher if no related objects exist"""
    besucher = Besucher.get_by_id(besucher_id)
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
    if besucher.language != form.language.data:
        besucher.language = form.language.data
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

    if buchung.get_preis_nacht() != form.preis_nacht.data:
        buchung.preis_nacht = form.preis_nacht.data

    if buchung.get_zusatzkosten() != form.zusatzkosten.data:
        buchung.zusatzkosten = form.zusatzkosten.data

    if buchung.get_rabatt() != form.rabatt.data:
        buchung.rabatt = form.rabatt.data

    if buchung.get_vorauszahlung() != form.vorauszahlung.data:
        buchung.vorauszahlung = form.vorauszahlung.data

    if buchung.portal_id != int(form.portal_id.data):
        buchung.portal_id = int(form.portal_id.data)

    if buchung.get_kurtaxe_vz() != form.kurtaxe_vz.data:
        buchung.kurtaxe_vz = form.kurtaxe_vz.data

    if buchung.get_kurtaxe_hz() != form.kurtaxe_hz.data:
        buchung.kurtaxe_hz = form.kurtaxe_hz.data

    if buchung.get_kurtaxe_kinder() != form.kurtaxe_kinder.data:
        buchung.kurtaxe_kinder = form.kurtaxe_kinder.data

    if buchung.get_kurtaxe_nz() != form.kurtaxe_nz.data:
        buchung.kurtaxe_nz = form.kurtaxe_nz.data

    if buchung.get_notiz() != form.notiz.data:
        buchung.notiz = form.notiz.data

    if buchung.is_dirty():
        dirty_fields = [df.column_name for df in buchung.dirty_fields]
        buchung.recalc(buchung.status).save()
        return dirty_fields
    else:
        return []


def construct_email_header(starter, buchung):
    return (
            '{} Apartment {}, {} von {} bis {}'
            .format(
                starter,
                buchung.apartment.name,
                buchung.apartment.beschreibung,
                format_date(buchung.anreise, format='short', locale='de_DE'),
                format_date(buchung.abreise, format='short', locale='de_DE')))


def send_confirmation_emails(buchung, email_text):
    # create email record
    besucher_email = Email()
    besucher_email.besucher = buchung.besucher
    besucher_email.buchung = buchung
    besucher_email.header = construct_email_header(
        'Buchungsbestätigung',
        buchung)

    besucher_email.body = email_text
    besucher_email.save()
    # email section
    # prepare email to besucher
    mailer.add_email(
        [buchung.besucher.email],
        current_app.config['EMAILS_TEAM'],
        besucher_email.header,
        besucher_email.body,
        'empty'
    )
    # prepare email to team
    email_html = render_template(
        'emails/buchung_info_team.html',
        buchung=buchung
    )
    header = (
        '[fig:Neue Buchung {}, {} - {}'
        .format(
            buchung.apartment.name,
            format_date(buchung.anreise, locale='de_DE'),
            format_date(buchung.abreise, locale='de_DE')))

    mailer.add_email(
        current_app.config['EMAILS_TEAM'],     # team ...
        [],                                 # nobody in cc
        header,
        email_html,
        'empty'
    )
    # send all emails; email server quits after sending
    mailer.send_emails()


def send_storno_emails(buchung):
    # email to visitor
    email_html = render_template(
        'emails/{}/buchung_storno.html'
        .format(language_for_key(buchung.besucher.language)),
        buchung=buchung
    )
    header = 'Ihre Fewo Buchung bei uns: Storno'
    mailer.add_email(
        [buchung.besucher.email],            # besucher
        current_app.config['INFO_EMAIL'],    # info
        header,
        email_html,
        'empty'
    )
    # email to team
    email_html = render_template(
        'emails/buchung_storno_team.html',
        buchung=buchung
    )
    header = '[fig:Buchung storniert]'

    mailer.add_email(
        current_app.config['EMAILS_TEAM'],     # team ...
        [],                                    # nobody in cc
        header,
        email_html,
        'empty'
    )
    mailer.send_emails()


def send_angebot_emails(buchung, email_text):
    # create email record
    besucher_email = Email()
    besucher_email.besucher = buchung.besucher
    besucher_email.buchung = buchung
    besucher_email.header = construct_email_header('Angebot', buchung)
    besucher_email.body = email_text
    besucher_email.save()
    # email section
    # prepare email to besucher
    mailer.add_email(
        [buchung.besucher.email],
        current_app.config['EMAILS_TEAM'],
        besucher_email.header,
        besucher_email.body,
        'empty'
    )
    # send all emails; email server quits after sending
    mailer.send_emails()


def send_update_emails(buchung, buchung_alt, res):
    # send emails
    if 'vorauszahlung' in res:
        # send payment confirmation to besucher
        email_html = render_template(
            'emails/{}/buchung_vorauszahlung.html'
            .format(language_for_key(buchung.besucher.language)),
            buchung=buchung,
            buchung_alt=buchung_alt
        )
        header = 'Ihre Fewo Buchung bei uns: Vorauszahlung'

        mailer.add_email(
            [buchung.besucher.email],              # besucher
            current_app.config['INFO_EMAIL'],    # info
            header,
            email_html,
            'empty'
        )
    # prepare email to team
    email_html = render_template(
        'emails/buchung_changed_team.html',
        buchung=buchung,
        buchung_alt=buchung_alt
    )
    header = '[fig:Buchung geändert]'
    mailer.add_email(
        current_app.config['EMAILS_TEAM'],     # team ...
        [],                                    # nobody in cc
        header,
        email_html,
        'empty'
    )
    mailer.send_emails()

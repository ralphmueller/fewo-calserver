'''
Created on 19.09.2021

API to models and helper functions

@author: ralph
'''

from typing import ClassVar
from peewee import fn
from bkormlib import Besucher, Buchung, Apartment, Email, User

from babel.dates import format_date

from flask import current_app, render_template
from flaskr import mailer


class SystemInfo():

    version_tag = 'alpha.9'

    letter_types = [
        'angebot',
        'buchung_confirmation',
        'buchung_storno',
        'buchung_vorauszahlung']

    header_strings = {
        'de': {
            'angebot':
                'Angebot {}, {} {} bis {}',
            'buchung_confirmation':
                'Buchungsbestätigung {}, {} {} bis {}',
            'buchung_storno':
                'Storno für Ihre Buchung {}, {} {} bis {}',
            'buchung_vorauszahlung':
                'Vorauszahlung eingegangen für Buchung {}, {} {} bis {}'
        },
        'en': {
            'angebot': 'TBD',
            'buchung_confirmation': 'TBD',
            'buchung_storno': 'TBD',
            'buchung_vorauszahlung': 'TBD'
        },
        'fr': {
            'angebot': 'TBD',
            'buchung_confirmation': 'TBD',
            'buchung_storno': 'TBD',
            'buchung_vorauszahlung': 'TBD'
        }
    }

    @classmethod
    def get_years(cls):
        db = Buchung._meta.database
        cursor = db.execute_sql('SELECT year(anreise), COUNT(*), sum(miete), sum(kurtaxe) from buchung where status in ("abgerechnet", "gebucht") group by year(anreise);')
        res = [row for row in cursor.fetchall()]
        years_in_operation = [year[0] for year in res]
        return years_in_operation

    @classmethod
    def get_versiontag(cls):
        return cls.version_tag

    @classmethod
    def get_email_header(cls, letter_type, buchung):
        if letter_type not in cls.letter_types:
            raise ValueError
        return (
            cls.header_strings[buchung.besucher.language][letter_type]
            .format(
                buchung.apartment.name,
                buchung.apartment.beschreibung,
                format_date(buchung.anreise, format='short', locale='de_DE'),
                format_date(buchung.abreise, format='short', locale='de_DE')))


# choices and helper functions for dropdowns in Besucher forms
ANREDE = [
    ('Fam.', 'Fam.'), ('Herr', 'Herr'), ('Frau', 'Frau'), ('Firma', 'Firma')]
LANGUAGE = [
    ('de', 'de'), ('en', 'en'), ('fr', 'fr')]


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
    besucher.user = User.get_by_id(form.user_id.data)
    besucher.anrede = form.anrede.data
    besucher.name = form.name.data
    besucher.vorname = form.vorname.data
    besucher.firmenname = form.firmenname.data
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
    return besucher


def update_besucher(form, besucher):
    '''
        update besucher: check which fields need updating
    '''
    if besucher.anrede != form.anrede.data:
        besucher.anrede = form.anrede.data
    if besucher.name != form.name.data:
        besucher.name = form.name.data
    if besucher.vorname != form.vorname.data:
        besucher.vorname = form.vorname.data
    if besucher.firmenname != form.firmenname.data:
        besucher.firmenname = form.firmenname.data
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


def send_confirmation_emails(buchung, email_text):
    # create email record
    besucher_email = Email()
    besucher_email.besucher = buchung.besucher
    besucher_email.buchung = buchung
    besucher_email.header = SystemInfo.get_email_header(
        'buchung_confirmation',
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
        .format(buchung.besucher.language.lower()),
        buchung=buchung
    )
    header = SystemInfo.get_email_header(
        'buchung_storno',
        buchung)
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
    besucher_email.header = SystemInfo.get_email_header(
        'angebot',
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
    # send all emails; email server quits after sending
    mailer.send_emails()


def send_update_emails(buchung, buchung_alt, res):
    # send emails
    if 'vorauszahlung' in res:
        # send payment confirmation to besucher
        email_html = render_template(
            'emails/{}/buchung_vorauszahlung.html'
            .format(buchung.besucher.language.lower()),
            buchung=buchung,
            buchung_alt=buchung_alt
        )
        header = SystemInfo.get_email_header(
            'buchung_vorauszahlung',
            buchung)

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

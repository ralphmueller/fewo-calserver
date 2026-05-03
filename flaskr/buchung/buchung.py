'''
Created on 04.10.2021

@author: ralph

* create, delete (storno, dispose), list buchungen, angebote, rechnungen
* change angebote into buchungen
* change buchungen into rechnungen
* initiate emails to team and besucher

'''
from babel.dates import format_date
import datetime
from calendar import monthrange
from flask import (
    Blueprint,
    make_response,
    render_template,
    flash,
    redirect,
    url_for,
    current_app,
    request,
    session
)

from bkormlib import (
    Buchung,
    Besucher,
    Apartment,
    StaticValuesBuchung,
    Ware,
    Verkauf,
    Portal)

from .buchung_forms import (
    BuchungForm, Buchung2Form, MeldescheinForm, VorauszahlungForm)
# Buchung2Form still used by convert_angebot

from flaskr.auth.auth import login_required

from flaskr.utils.api import (
    SystemInfo,
    update_buchung,
    calc_prepayment,
    send_confirmation_emails,
    send_angebot_emails,
    send_update_emails,
    send_storno_emails)

# ToDo - locale abhängige Lösung wäre besser
months = [
    "Jan",
    "Feb",
    "Mär",
    "Apr",
    "Mai",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Okt",
    "Nov",
    "Dez",
    ]

buchung_bp = Blueprint(
    'buchung_bp',
    __name__,
    url_prefix='/buchung',
    template_folder='templates',
    static_folder='static'
)


class _EmailDummy:
    """Platzhalter-Buchung für Email-Vorschau, bevor Buchungsdaten eingetragen sind."""
    def __init__(self, besucher):
        from types import SimpleNamespace
        self.besucher = besucher
        self.apartment = SimpleNamespace(name='[Wohnung]', beschreibung='')
        self.anreise = datetime.date.today()
        self.abreise = datetime.date.today() + datetime.timedelta(days=7)
        self.preis_nacht = 0.0
        self.miete = 0.0
        self.kurtaxe = 0.0
        self.summe = 0.0
        self.vorauszahlung = 0.0
        self.kurtaxe_vz = 2
        self.kurtaxe_kinder = 0
        self.kurtaxe_nz = 0
        self.rabatt = 0.0

    def get_anreise(self): return self.anreise
    def get_abreise(self): return self.abreise
    def get_preis_nacht(self): return self.preis_nacht
    def get_zusatzkosten(self): return 0.0
    def get_rabatt(self): return self.rabatt
    def get_miete(self): return self.miete
    def get_kurtaxe_vz(self): return self.kurtaxe_vz
    def get_kurtaxe_kinder(self): return self.kurtaxe_kinder
    def get_kurtaxe_nz(self): return self.kurtaxe_nz
    def get_kurtaxe(self): return self.kurtaxe
    def get_summe(self): return self.summe


def _build_buchung_query(status_list, year, month_str, apartment_filter='', name_filter=''):
    start_month = months.index(month_str) + 1
    last_day = monthrange(year, start_month)[1]

    if 'abgerechnet' in status_list:
        where_clause = (
            (Buchung.status.in_(status_list)) &
            (Buchung.abreise.between(
                datetime.date(year, start_month, 1),
                datetime.date(year, start_month, last_day)
            )))
        orderby_clause = Buchung.abreise.desc()
    else:
        where_clause = (
            (Buchung.status.in_(status_list)) &
            (Buchung.anreise.between(
                datetime.date(year, start_month, 1),
                datetime.date(year, start_month, last_day)
            )))
        orderby_clause = Buchung.anreise.asc()

    if apartment_filter:
        where_clause = where_clause & (Apartment.name == apartment_filter)

    q = name_filter.strip() if name_filter else ''
    if len(q) >= 2:
        parts = q.lower().split()
        def pat(s):
            return s.replace('*', '%') if '*' in s else s + '%'
        if len(parts) >= 2:
            where_clause = where_clause & (
                (Besucher.name ** pat(parts[0])) & (Besucher.vorname ** pat(parts[1])))
        else:
            p = pat(parts[0])
            where_clause = where_clause & (
                (Besucher.name ** p) | (Besucher.vorname ** p))

    return (
        Buchung
        .select()
        .join(Apartment)
        .switch(Buchung)
        .join(Besucher)
        .where(where_clause)
        .order_by(orderby_clause)
    )


@buchung_bp.route('/')
@login_required
def index():
    today = datetime.date.today()
    status_list = request.args.getlist('status') or \
        (request.args.get('status', '').split(',') if request.args.get('status') else ['gebucht', 'abgerechnet'])
    year = int(request.args.get('year', today.year))
    month = request.args.get('month', months[today.month - 1])
    apartment_filter = request.args.get('apartment', '')
    name_filter = request.args.get('name_filter', '')
    apartments = [a.name for a in Apartment.select().order_by(Apartment.name)]

    buchungen = _build_buchung_query(status_list, year, month, apartment_filter, name_filter)

    return render_template(
        'buchung/index.html',
        buchungen=buchungen,
        year=year,
        month=month,
        status_list=status_list,
        apartment_filter=apartment_filter,
        name_filter=name_filter,
        apartments=apartments,
        years=SystemInfo.get_years(),
        months=months,
        run_mode=current_app.config['ENV'])


@buchung_bp.route('/search')
@login_required
def search():
    today = datetime.date.today()
    status_list = request.args.getlist('status') or ['gebucht', 'abgerechnet']
    year = int(request.args.get('year', today.year))
    month = request.args.get('month', months[today.month - 1])
    apartment_filter = request.args.get('apartment', '')
    name_filter = request.args.get('name_filter', '')

    buchungen = _build_buchung_query(status_list, year, month, apartment_filter, name_filter)

    return render_template('buchung/list_partial.html', buchungen=buchungen)


@buchung_bp.route('/<int:buchung_id>/detail')
@login_required
def detail(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    return render_template('buchung/detail_partial.html', buchung=buchung)


@buchung_bp.route('/<int:buchung_id>/detail_row')
@login_required
def detail_row(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    return render_template('buchung/detail_row_partial.html', buchung=buchung)


@buchung_bp.route('/<int:buchung_id>/edit_inline', methods=['GET', 'POST'])
@login_required
def edit_inline(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    if buchung.status in ['abgerechnet', 'storno', 'verworfen']:
        return render_template('buchung/detail_partial.html', buchung=buchung,
                               error='Buchung mit Status "{}" kann nicht geändert werden.'.format(buchung.status))

    form = BuchungForm(obj=buchung)
    if form.validate_on_submit():
        buchung_alt = Buchung.get_by_id(buchung_id)
        dirty_fields = update_buchung(form, buchung)
        if dirty_fields:
            send_update_emails(buchung, buchung_alt, dirty_fields)
        buchung = Buchung.get_by_id(buchung_id)
        return render_template('buchung/detail_partial.html', buchung=buchung)

    return render_template('buchung/edit_partial.html', form=form, buchung=buchung)


@buchung_bp.route('/schnell')
@login_required
def schnell():
    return render_template('buchung/schnell.html', title='Schnellbuchung',
                           run_mode=current_app.config['ENV'])


@buchung_bp.route('/schnell/verfuegbar')
@login_required
def schnell_verfuegbar():
    anreise_str = request.args.get('anreise', '')
    abreise_str = request.args.get('abreise', '')
    try:
        anreise = datetime.date.fromisoformat(anreise_str)
        abreise = datetime.date.fromisoformat(abreise_str)
    except ValueError:
        return '<div class="alert alert-danger">Bitte gültige Daten eingeben.</div>'
    if abreise <= anreise:
        return '<div class="alert alert-warning">Abreise muss nach Anreise liegen.</div>'
    nights = (abreise - anreise).days
    apartments = [a for a in Apartment.select().where(Apartment.active)
                  if a.check_availability(anreise, abreise)]
    return render_template('buchung/schnell_verfuegbar_partial.html',
                           apartments=apartments, anreise=anreise,
                           abreise=abreise, nights=nights)


@buchung_bp.route('/schnell/gast')
@login_required
def schnell_gast():
    anreise = request.args.get('anreise', '')
    abreise = request.args.get('abreise', '')
    apartment_id = request.args.get('apartment_id', '')
    apartment = Apartment.get_by_id(int(apartment_id))
    return render_template('buchung/schnell_gast_partial.html',
                           apartment=apartment, anreise=anreise, abreise=abreise)


@buchung_bp.route('/schnell/gast_suche')
@login_required
def schnell_gast_suche():
    q = request.args.get('q', '').strip()
    anreise = request.args.get('anreise', '')
    abreise = request.args.get('abreise', '')
    apartment_id = request.args.get('apartment_id', '')
    if len(q) < 2:
        return ''
    parts = q.lower().split()
    def pat(s):
        return s.replace('*', '%') if '*' in s else s + '%'
    if len(parts) >= 2:
        where = (Besucher.name ** pat(parts[0])) & (Besucher.vorname ** pat(parts[1]))
    else:
        p = pat(parts[0])
        where = (Besucher.name ** p) | (Besucher.vorname ** p)
    data = Besucher.select().where(where).order_by(Besucher.name)
    return render_template('buchung/schnell_gast_ergebnis_partial.html',
                           data=data, anreise=anreise, abreise=abreise,
                           apartment_id=apartment_id)


@buchung_bp.route('/schnell/buchen_formular')
@login_required
def schnell_buchen_formular():
    anreise = datetime.date.fromisoformat(request.args.get('anreise'))
    abreise = datetime.date.fromisoformat(request.args.get('abreise'))
    apartment = Apartment.get_by_id(int(request.args.get('apartment_id')))
    besucher = Besucher.get_by_id(int(request.args.get('besucher_id')))
    nights = (abreise - anreise).days
    try:
        preisliste = apartment.get_preisliste_year(anreise.year)
        preis_nacht = preisliste.preis_2p
    except Exception:
        preis_nacht = 0.0
    portale = Portal.choices()
    return render_template('buchung/schnell_buchen_formular_partial.html',
                           apartment=apartment, besucher=besucher,
                           anreise=anreise, abreise=abreise,
                           nights=nights, preis_nacht=preis_nacht,
                           portale=portale,
                           user_id=session.get('user_id'))


@buchung_bp.route('/schnell/neuer_gast', methods=['GET', 'POST'])
@login_required
def schnell_neuer_gast():
    anreise = request.args.get('anreise') or request.form.get('anreise', '')
    abreise = request.args.get('abreise') or request.form.get('abreise', '')
    apartment_id = request.args.get('apartment_id') or request.form.get('apartment_id', '')
    if request.method == 'POST':
        besucher = Besucher()
        besucher.user_id = session.get('user_id')
        besucher.anrede = request.form.get('anrede', 'Fam')
        besucher.name = request.form.get('name', '').strip()
        besucher.vorname = request.form.get('vorname', '').strip()
        besucher.email = request.form.get('email', '').strip()
        besucher.land = request.form.get('land', 'DE').strip()
        besucher.language = 'DE'
        besucher.save()
        apartment = Apartment.get_by_id(int(apartment_id))
        anreise_d = datetime.date.fromisoformat(anreise)
        abreise_d = datetime.date.fromisoformat(abreise)
        nights = (abreise_d - anreise_d).days
        try:
            preisliste = apartment.get_preisliste_year(anreise_d.year)
            preis_nacht = preisliste.preis_2p
        except Exception:
            preis_nacht = 0.0
        portale = Portal.choices()
        return render_template('buchung/schnell_buchen_formular_partial.html',
                               apartment=apartment, besucher=besucher,
                               anreise=anreise_d, abreise=abreise_d,
                               nights=nights, preis_nacht=preis_nacht,
                               portale=portale,
                               user_id=session.get('user_id'))
    return render_template('buchung/schnell_neuer_gast_partial.html',
                           anreise=anreise, abreise=abreise, apartment_id=apartment_id)


@buchung_bp.route('/schnell/vorschau', methods=['POST'])
@login_required
def schnell_vorschau():
    typ = request.form.get('typ', 'gebucht')
    buchung = Buchung()
    buchung.user_id = int(request.form.get('user_id', 0))
    buchung.besucher_id = int(request.form.get('besucher_id'))
    buchung.apartment_id = int(request.form.get('apartment_id'))
    buchung.portal_id = int(request.form.get('portal_id'))
    buchung.anreise = datetime.date.fromisoformat(request.form.get('anreise'))
    buchung.abreise = datetime.date.fromisoformat(request.form.get('abreise'))
    buchung.preis_nacht = float(request.form.get('preis_nacht', 0))
    buchung.zusatzkosten = float(request.form.get('zusatzkosten', 0))
    buchung.rabatt = float(request.form.get('rabatt', 0))
    buchung.vorauszahlung = float(request.form.get('vorauszahlung', 0))
    buchung.kurtaxe_vz = int(request.form.get('kurtaxe_vz', 2))
    buchung.kurtaxe_hz = int(request.form.get('kurtaxe_hz', 0))
    buchung.kurtaxe_kinder = int(request.form.get('kurtaxe_kinder', 0))
    buchung.kurtaxe_nz = int(request.form.get('kurtaxe_nz', 0))
    buchung.kurtaxe_korrekturwert = float(request.form.get('kurtaxe_korrekturwert', 0))
    buchung.notiz = request.form.get('notiz', '')
    buchung.besucher = Besucher.get_by_id(buchung.besucher_id)
    buchung.apartment = Apartment.get_by_id(buchung.apartment_id)

    if not buchung.apartment.check_availability(buchung.anreise, buchung.abreise):
        alternatives = [a for a in Apartment.select().where(Apartment.active)
                        if a.check_availability(buchung.anreise, buchung.abreise)]
        return render_template('buchung/conflict_partial.html',
                               apartment=buchung.apartment,
                               anreise=buchung.anreise, abreise=buchung.abreise,
                               alternatives=alternatives,
                               zurueck_url=url_for('buchung_bp.schnell_buchen_formular',
                                                   anreise=buchung.anreise,
                                                   abreise=buchung.abreise,
                                                   apartment_id=buchung.apartment_id,
                                                   besucher_id=buchung.besucher_id),
                               hx_target='#buchung-panel')

    buchung.recalc(typ)

    if typ == 'angebot':
        days = (buchung.abreise - buchung.anreise).days
        email_text = render_template(
            'emails/{}/angebot.html'.format(buchung.besucher.language.lower()),
            buchung=buchung, days=days)
    else:
        email_text = render_template(
            'emails/{}/buchung_confirmation.html'.format(buchung.besucher.language.lower()),
            buchung=buchung)

    zurueck_url = url_for('buchung_bp.schnell_buchen_formular',
                          anreise=buchung.anreise, abreise=buchung.abreise,
                          apartment_id=buchung.apartment_id,
                          besucher_id=buchung.besucher_id)
    return render_template('buchung/neu_email_partial.html',
                           buchung=buchung, besucher=buchung.besucher,
                           email_text=email_text, typ=typ,
                           hx_target='#buchung-panel', zurueck_url=zurueck_url)


_STATUS_TRANSITIONS = {
    'angebot': ['gebucht', 'verworfen'],
    'gebucht': ['storno'],
}


@buchung_bp.route('/<int:buchung_id>/status', methods=['POST'])
@login_required
def update_status(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    new_status = request.form.get('status')
    if new_status in _STATUS_TRANSITIONS.get(buchung.status, []):
        buchung.recalc(new_status)
        buchung.save()
    return render_template('buchung/tr_partial.html', buchung=buchung)


@buchung_bp.route('/neu')
@login_required
def neu():
    besucher_id = request.args.get('besucher_id', type=int)
    form = None
    besucher = None
    if besucher_id:
        besucher = Besucher.get_by_id(besucher_id)
        form = BuchungForm()
        form.user_id.data = session.get('user_id')
        form.besucher_id.data = besucher_id
    return render_template('buchung/neu.html', title='Neue Buchung',
                           form=form, besucher=besucher,
                           run_mode=current_app.config['ENV'])


@buchung_bp.route('/neu/suche')
@login_required
def neu_suche():
    q = request.args.get('q', '').strip()
    if len(q) < 3:
        return ''
    parts = q.lower().split()
    def pat(s):
        return s.replace('*', '%')
    if len(parts) >= 2:
        where = (Besucher.name ** pat(parts[0])) & (Besucher.vorname ** pat(parts[1]))
    else:
        p = pat(parts[0])
        where = (Besucher.name ** p) | (Besucher.vorname ** p)
    data = Besucher.select().where(where).order_by(Besucher.name)
    return render_template('buchung/gast_auswahl_partial.html', data=data)


@buchung_bp.route('/neu/email_vorschau/<int:besucher_id>')
@login_required
def neu_email_vorschau(besucher_id):
    from types import SimpleNamespace
    besucher = Besucher.get_by_id(besucher_id)
    typ = request.args.get('typ', 'gebucht')
    try:
        buchung = Buchung()
        buchung.besucher_id = besucher_id
        buchung.besucher = besucher
        buchung.apartment_id = int(request.args.get('apartment_id') or 0)
        buchung.apartment = Apartment.get_by_id(buchung.apartment_id)
        buchung.anreise = datetime.date.fromisoformat(request.args.get('anreise', ''))
        buchung.abreise = datetime.date.fromisoformat(request.args.get('abreise', ''))
        buchung.preis_nacht = float(request.args.get('preis_nacht') or 0)
        buchung.zusatzkosten = float(request.args.get('zusatzkosten') or 0)
        buchung.rabatt = float(request.args.get('rabatt') or 0)
        buchung.kurtaxe_vz = int(request.args.get('kurtaxe_vz') or 2)
        buchung.kurtaxe_hz = int(request.args.get('kurtaxe_hz') or 0)
        buchung.kurtaxe_kinder = int(request.args.get('kurtaxe_kinder') or 0)
        buchung.kurtaxe_nz = int(request.args.get('kurtaxe_nz') or 0)
        buchung.kurtaxe_korrekturwert = float(request.args.get('kurtaxe_korrekturwert') or 0)
        buchung.vorauszahlung = 0.0
        buchung.portal = SimpleNamespace(kommission_prozent=0)
        buchung.recalc(typ)
        if typ == 'angebot':
            days = (buchung.abreise - buchung.anreise).days
            return render_template(
                'emails/{}/angebot.html'.format(besucher.language.lower()),
                buchung=buchung, days=days)
        else:
            return render_template(
                'emails/{}/buchung_confirmation.html'.format(besucher.language.lower()),
                buchung=buchung)
    except Exception:
        return ''


@buchung_bp.route('/neu/formular/<int:besucher_id>')
@login_required
def neu_formular(besucher_id):
    besucher = Besucher.get_by_id(besucher_id)
    typ = request.args.get('typ', 'gebucht')
    hx_target = request.args.get('hx_target', '#buchung-panel')
    form = BuchungForm()
    form.user_id.data = session.get('user_id')
    form.besucher_id.data = besucher_id
    return render_template('buchung/neu_formular_partial.html',
                           form=form, besucher=besucher,
                           typ=typ, hx_target=hx_target)


@buchung_bp.route('/neu/vorschau/<int:besucher_id>', methods=['POST'])
@login_required
def neu_vorschau(besucher_id):
    besucher = Besucher.get_by_id(besucher_id)
    typ = request.form.get('typ', 'gebucht')
    hx_target = request.form.get('hx_target', '#buchung-panel')
    form = BuchungForm()

    if not form.validate_on_submit():
        return render_template('buchung/neu_formular_partial.html',
                               form=form, besucher=besucher,
                               typ=typ, hx_target=hx_target)

    buchung = Buchung()
    buchung.user_id = int(form.user_id.data or 0)
    buchung.besucher = besucher
    buchung.besucher_id = besucher_id
    buchung.apartment_id = int(form.apartment_id.data)
    buchung.apartment = Apartment.get_by_id(buchung.apartment_id)
    buchung.portal_id = int(form.portal_id.data)
    buchung.anreise = form.anreise.data
    buchung.abreise = form.abreise.data
    buchung.preis_nacht = float(form.preis_nacht.data or 0)
    buchung.zusatzkosten = float(form.zusatzkosten.data or 0)
    buchung.rabatt = float(form.rabatt.data or 0)
    buchung.vorauszahlung = float(form.vorauszahlung.data or 0)
    buchung.kurtaxe_vz = int(form.kurtaxe_vz.data or 0)
    buchung.kurtaxe_hz = int(form.kurtaxe_hz.data or 0)
    buchung.kurtaxe_kinder = int(form.kurtaxe_kinder.data or 0)
    buchung.kurtaxe_nz = int(form.kurtaxe_nz.data or 0)
    buchung.kurtaxe_korrekturwert = float(form.kurtaxe_korrekturwert.data or 0)
    buchung.notiz = form.notiz.data or ''

    if not buchung.apartment.check_availability(buchung.anreise, buchung.abreise):
        alternatives = [a for a in Apartment.select().where(Apartment.active)
                        if a.check_availability(buchung.anreise, buchung.abreise)]
        return render_template('buchung/conflict_partial.html',
                               apartment=buchung.apartment,
                               anreise=buchung.anreise, abreise=buchung.abreise,
                               alternatives=alternatives,
                               zurueck_url=url_for('buchung_bp.neu_formular',
                                                   besucher_id=besucher_id,
                                                   typ=typ, hx_target=hx_target),
                               hx_target=hx_target)

    buchung.recalc(typ)

    if typ == 'angebot':
        days = (buchung.abreise - buchung.anreise).days
        email_text = render_template(
            'emails/{}/angebot.html'.format(besucher.language.lower()),
            buchung=buchung, days=days)
    else:
        email_text = render_template(
            'emails/{}/buchung_confirmation.html'.format(besucher.language.lower()),
            buchung=buchung)

    zurueck_url = url_for('buchung_bp.neu_formular', besucher_id=besucher_id,
                          typ=typ, hx_target=hx_target)
    return render_template('buchung/neu_email_partial.html',
                           buchung=buchung, besucher=besucher,
                           email_text=email_text, typ=typ,
                           hx_target=hx_target, zurueck_url=zurueck_url)


@buchung_bp.route('/neu/speichern/<int:besucher_id>', methods=['POST'])
@login_required
def neu_speichern(besucher_id):
    typ = request.form.get('typ', 'gebucht')
    buchung = Buchung()
    buchung.user_id = int(request.form.get('user_id'))
    buchung.besucher_id = besucher_id
    buchung.apartment_id = int(request.form.get('apartment_id'))
    buchung.portal_id = int(request.form.get('portal_id'))
    buchung.anreise = datetime.date.fromisoformat(request.form.get('anreise'))
    buchung.abreise = datetime.date.fromisoformat(request.form.get('abreise'))
    buchung.preis_nacht = float(request.form.get('preis_nacht', 0))
    buchung.zusatzkosten = float(request.form.get('zusatzkosten', 0))
    buchung.rabatt = float(request.form.get('rabatt', 0))
    buchung.vorauszahlung = float(request.form.get('vorauszahlung', 0))
    buchung.kurtaxe_vz = int(request.form.get('kurtaxe_vz', 2))
    buchung.kurtaxe_hz = int(request.form.get('kurtaxe_hz', 0))
    buchung.kurtaxe_kinder = int(request.form.get('kurtaxe_kinder', 0))
    buchung.kurtaxe_nz = int(request.form.get('kurtaxe_nz', 0))
    buchung.kurtaxe_korrekturwert = float(request.form.get('kurtaxe_korrekturwert', 0))
    buchung.notiz = request.form.get('notiz', '')
    apartment = Apartment.get_by_id(buchung.apartment_id)
    if not apartment.check_availability(buchung.anreise, buchung.abreise):
        alternatives = [a for a in Apartment.select().where(Apartment.active)
                        if a.check_availability(buchung.anreise, buchung.abreise)]
        hx_target = request.form.get('hx_target', '#buchung-panel')
        return render_template('buchung/conflict_partial.html',
                               apartment=apartment,
                               anreise=buchung.anreise, abreise=buchung.abreise,
                               alternatives=alternatives,
                               zurueck_url=url_for('buchung_bp.neu_formular',
                                                   besucher_id=besucher_id,
                                                   typ=typ,
                                                   hx_target=hx_target),
                               hx_target=hx_target)
    buchung.recalc(typ)
    buchung.save()
    email_text = request.form.get('email_text', '')
    if typ == 'angebot':
        send_angebot_emails(buchung, email_text)
    else:
        send_confirmation_emails(buchung, email_text)
    resp = make_response('', 204)
    resp.headers['HX-Redirect'] = url_for('buchung_bp.anzeigen', buchung_id=buchung.id)
    return resp




@buchung_bp.route('/storno/<int:buchung_id>')
@login_required
def storno(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    buchung.status = 'storno'
    buchung.save()
    send_storno_emails(buchung)

    # done, back to visitor
    flash(
        'Buchung {}, {} storniert'.format(buchung_id, buchung.besucher.name))
    return redirect(
        url_for(
            'besucher_bp.update',
            besucher_id=buchung.besucher.id))


@buchung_bp.route('/abrechnen/<int:buchung_id>', methods=('GET', 'POST'))
@login_required
def abrechnen(buchung_id):
    """
        get:
            - show current details
            - input form for meldeschein data
        post:
            - change buchung status to abgerechnet
            - set meldeschein data
            - reroute to printing invoice
    """
    buchung = Buchung.get_by_id(buchung_id)
    if buchung.status in ['storno', 'verworfen', 'abgerechnet']:
        flash(
            'Buchung {} mit Status {} kann nicht abgerechnet werden!'
            .format(buchung.id, buchung.status), 'error')
        return redirect(url_for('home_bp.index'))
    form = MeldescheinForm()

    if form.validate_on_submit():
        # save meldeschein data
        buchung.meldeschein_nummer = form.meldeschein_nummer.data
        # set status to abgerechnet
        buchung.status = 'abgerechnet'
        buchung.rechnungs_nummer = '{}-{:03}-{}'.format(
            buchung.apartment.name,
            buchung.apartment.get_next_invoice_no(),
            datetime.date.today().year)
        buchung.rechnungsdatum = buchung.anreise
        buchung.save()
        return (
            redirect(
                url_for(
                    'besucher_bp.update',
                    besucher_id=buchung.besucher.id)))

    return render_template(
        'buchung/abrechnen.html',
        form=form,
        buchung=buchung,
        # actions=actions,
        title='Buchung abrechnen',
        besucher=buchung.besucher,
        run_mode=current_app.config['ENV']
    )


@buchung_bp.route('/anzeigen/<int:buchung_id>')
@login_required
def anzeigen(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    verkaeufe = []
    waren = []
    waren_summe = 0
    if buchung.status == 'abgerechnet':
        verkaeufe = list(Verkauf.select(Verkauf, Ware).join(Ware).where(Verkauf.buchung == buchung))
        waren = list(Ware.select().where(Ware.active == True).order_by(Ware.bezeichnung))
        waren_summe = sum(v.menge * v.preis_zum_zeitpunkt for v in verkaeufe)
    return render_template(
        'buchung/anzeigen.html',
        buchung=buchung,
        verkaeufe=verkaeufe,
        waren=waren,
        waren_summe=waren_summe,
        title='{} anzeigen'.format(buchung.status.capitalize()),
        run_mode=current_app.config['ENV']
    )


@buchung_bp.route('/rechnung/<int:buchung_id>')
@login_required
def rechnung(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)

    actions = [
        (
            'Vorauszahlung',
            url_for('buchung_bp.update_vorauszahlung', buchung_id=buchung.id)),
        (
            'Rechnung',
            url_for('buchung_bp.rechnung', buchung_id=buchung.id))
    ]

    verkaeufe = list(buchung.verkaeufe)
    waren_summe = buchung.get_waren_summe()
    waren_mwst = buchung.get_waren_mwst()
    waren_mwst_detail = [
        (rate, brutto, round(brutto * rate / (100 + rate), 2))
        for rate, brutto in sorted(waren_mwst.items())
    ]
    gesamtsumme = buchung.get_summe() + waren_summe
    offener_betrag = gesamtsumme - buchung.get_vorauszahlung()

    return render_template(
        'print/rechnung.html',
        buchung=buchung,
        days=(buchung.abreise - buchung.anreise).days,
        actions=actions,
        mwst_satz=StaticValuesBuchung.mwstsatz(),
        verkaeufe=verkaeufe,
        waren_summe=waren_summe,
        waren_mwst_detail=waren_mwst_detail,
        gesamtsumme=gesamtsumme,
        offener_betrag=offener_betrag,
        title='Buchung anzeigen',
        run_mode=current_app.config['ENV']
    )




@buchung_bp.route('/convert_angebot/<int:buchung_id>', methods=('GET', 'POST'))
@login_required
def convert_angebot(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    besucher = buchung.besucher

    if request.method == 'GET':
        email_text = render_template(
            'emails/{}/buchung_confirmation.html'.format(besucher.language.lower()),
            buchung=buchung)
        return render_template('buchung/convert_angebot_partial.html',
                               buchung=buchung, email_text=email_text)

    email_text = request.form.get('email_text', '')
    buchung.status = 'gebucht'
    buchung.save()
    send_confirmation_emails(buchung, email_text)
    resp = make_response('', 204)
    resp.headers['HX-Redirect'] = url_for('buchung_bp.anzeigen', buchung_id=buchung.id)
    return resp


@buchung_bp.route('/drop_angebot/<int:buchung_id>', methods=('GET', 'POST'))
@login_required
def drop_angebot(buchung_id):
    '''
        Offer was not converted in due time
        - set status to verworfen
    '''

    buchung = Buchung.get_by_id(buchung_id)
    buchung.status = 'verworfen'
    buchung.save()
    # flash message
    flash(
        'Buchung {} Apt {} vom {} - {} für {}, {} verworfen'.format(
            buchung.id,
            buchung.apartment.name,
            format_date(buchung.anreise, format='short', locale='de_DE'),
            format_date(buchung.abreise, format='short', locale='de_DE'),
            buchung.besucher.name,
            buchung.besucher.vorname
        ))
    return (
        redirect(
            url_for(
                'besucher_bp.update',
                besucher_id=buchung.besucher.id)))


@buchung_bp.route('/vorauszahlung/<int:buchung_id>', methods=('GET', 'POST'))
@login_required
def update_vorauszahlung(buchung_id):
    """
        received vorauszahlung for a buchung with status 'abgerechnet'
        - enter repaid amount
        - TODO: enter payment method (transfer, paypal)
        - send receipt email to besucher
        - update buchung
        - actions:
            - print invoice
    """
    buchung = Buchung.get_by_id(buchung_id)
    if buchung.status in ['storno', 'verworfen']:
        flash(
            'Buchung {} mit Status {} kann nicht abgerechnet werden!'
            .format(buchung.id, buchung.status), 'error')
        return redirect(url_for('home_bp.index'))

    form = VorauszahlungForm(obj=buchung)

    if form.validate_on_submit():
        # save and recalc
        # send email to besucher
        buchung_alt = Buchung.get_by_id(buchung_id)              # save copy
        dirty_fields = calc_prepayment(form, buchung)
        if len(dirty_fields) > 0:                                # changes
            send_update_emails(buchung, buchung_alt, dirty_fields)
            # set flash
            flash("Vorauszahlung für {}, {} gespeichert".format(
                buchung.id, buchung.besucher.name
                ))
        else:
            # set flash
            flash("Keine Änderung für {}, {} gespeichert".format(
                buchung.id, buchung.besucher.name
                ))

        return (
            redirect(
                url_for(
                    'besucher_bp.update',
                    besucher_id=buchung.besucher.id)))

    return render_template(
        'buchung/vorauszahlung.html',
        buchung=buchung,
        besucher=buchung.besucher,
        form=form,
        title='Vorauszahlung erfassen',
        run_mode=current_app.config['ENV'],
        template='form-template')


@buchung_bp.route('/feratel_meldeschein/<int:buchung_id>', methods=['POST'])
@login_required
def feratel_meldeschein(buchung_id):
    """Legt einen Feratel-Meldeschein an und speichert die Nummer in der Buchung."""
    from flaskr.feratel.automation import submit_meldeschein
    result = submit_meldeschein(buchung_id)
    if result['success']:
        buchung = Buchung.get_by_id(buchung_id)
        nr = result.get('meldeschein_nr') or ''
        buchung.meldeschein_nummer = nr
        buchung.save()
        msg = f'Feratel Meldeschein angelegt'
        if nr:
            msg += f' (Nr. {nr})'
        flash(msg)
    else:
        flash(f'Feratel Fehler: {result["error"]}', 'error')
    return redirect(url_for('buchung_bp.anzeigen', buchung_id=buchung_id))

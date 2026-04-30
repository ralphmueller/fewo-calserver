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
    User,
    FlaskrSession,
    StaticValuesBuchung,
    Ware,
    Portal)

from .buchung_forms import (
    BuchungForm, Buchung2Form, MeldescheinForm, VorauszahlungForm)

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


@buchung_bp.route('/schnell/buchen', methods=['POST'])
@login_required
def schnell_buchen():
    typ = request.form.get('typ', 'gebucht')
    buchung = Buchung()
    buchung.user_id = int(request.form.get('user_id'))
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
    buchung.recalc(typ)
    buchung.save()
    besucher = Besucher.get_by_id(buchung.besucher_id)
    if typ == 'gebucht':
        email_text = render_template(
            'emails/{}/buchung_confirmation.html'.format(besucher.language.lower()),
            buchung=buchung)
        send_confirmation_emails(buchung, email_text)
    else:
        email_text = render_template(
            'emails/{}/angebot.html'.format(besucher.language.lower()),
            days=(buchung.abreise - buchung.anreise).days, buchung=buchung)
        send_angebot_emails(buchung, email_text)
    resp = make_response('', 204)
    resp.headers['HX-Redirect'] = url_for('buchung_bp.index')
    return resp


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
    return render_template('buchung/neu.html', title='Neue Buchung',
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


@buchung_bp.route('/neu/formular/<int:besucher_id>', methods=['GET', 'POST'])
@login_required
def neu_formular(besucher_id):
    besucher = Besucher.get_by_id(besucher_id)
    form = BuchungForm()
    if request.method == 'GET':
        form.user_id.data = session.get('user_id')
        form.besucher_id.data = besucher_id

    if form.validate_on_submit():
        buchung = Buchung()
        buchung.user_id = int(form.user_id.data)
        buchung.besucher_id = int(form.besucher_id.data)
        buchung.apartment_id = int(form.apartment_id.data)
        buchung.portal_id = int(form.portal_id.data)
        buchung.anreise = form.anreise.data
        buchung.abreise = form.abreise.data
        buchung.preis_nacht = form.preis_nacht.data
        buchung.zusatzkosten = form.zusatzkosten.data
        buchung.rabatt = form.rabatt.data
        buchung.vorauszahlung = form.vorauszahlung.data
        buchung.kurtaxe_vz = form.kurtaxe_vz.data
        buchung.kurtaxe_hz = form.kurtaxe_hz.data
        buchung.kurtaxe_kinder = form.kurtaxe_kinder.data
        buchung.kurtaxe_nz = form.kurtaxe_nz.data
        buchung.kurtaxe_korrekturwert = form.kurtaxe_korrekturwert.data
        buchung.notiz = form.notiz.data
        buchung.recalc('gebucht')
        buchung.save()
        email_text = render_template(
            'emails/{}/buchung_confirmation.html'.format(besucher.language.lower()),
            buchung=buchung)
        send_confirmation_emails(buchung, email_text)
        resp = make_response('', 204)
        resp.headers['HX-Redirect'] = url_for('buchung_bp.index')
        return resp

    return render_template('buchung/neu_formular_partial.html',
                           form=form, besucher=besucher)


@buchung_bp.route('/create/<int:besucher_id>', methods=('GET', 'POST'))
@login_required
def create_buchung(besucher_id):
    '''
        Create new booking, step 1
        - gather booking data
        at the end of this step:
        - validate the information
        - check availability of apartment via 'prüfen' button
        - contiue to second step (create_buchung_finish)
    '''
    form = BuchungForm()
    form.user_id.data = session.get('user_id')
    form.besucher_id.data = besucher_id
    besucher = Besucher.get(besucher_id)
    if form.validate_on_submit():
        form.besucher_id = besucher_id
        session_data = form.data
        session_object = FlaskrSession.from_object(
            User.get(id=session['user_id']),
            session_data
        )
        session['create_buchung'] = session_object.id
        if besucher.email == "":
            flash('Besucher hat keine Email Adresse', 'error')

        return redirect(url_for('buchung_bp.create_buchung_finish'))

    return render_template(
        'buchung/create.html',
        besucher=besucher,
        form=form,
        title='Buchung anlegen',
        run_mode=current_app.config['ENV'],
        template='form-template'
    )


@buchung_bp.route('/create_finish', methods=('GET', 'POST'))
@login_required
def create_buchung_finish():
    '''
        Finalize new booking
        - check availability of apartment
        - prepare confirmation text
        - send emails and finish booking
    '''

    session_id = session['create_buchung']
    buchung = Buchung(**FlaskrSession.get(id=session_id).as_object())
    buchung.recalc(status='gebucht')
    besucher = Besucher.get(buchung.besucher_id)
    # prepare email_confirmation_email
    form = Buchung2Form()
    if request.method == 'GET':
        form.email_text.data = render_template(
            'emails/{}/buchung_confirmation.html'
            .format(besucher.language.lower()),
            buchung=buchung
        )

    if form.validate_on_submit():
        # save booking
        buchung.id = None
        buchung.save()
        # create email record
        send_confirmation_emails(buchung, form.email_text.data)
        # flash message
        flash(
            'Buchung {} Apt {} vom {} - {} für {}, {} gespeichert'.format(
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
                    besucher_id=besucher.id)))

    return render_template(
        'buchung/create_part2.html',
        besucher=besucher,
        buchung=buchung,
        form=form,
        title='Neue Buchung fertigstellen',
        run_mode=current_app.config['ENV'],
        template='form-template')


@buchung_bp.route('/update_check/<int:buchung_id>')
@login_required
def update_check(buchung_id):
    """
        make decisions what to do:
            - if the booking status is abgerechnet, re-route to
              anzeigen
            - if the booking status is gebucht, re-route to update
    """
    buchung = Buchung.get_by_id(buchung_id)
    if buchung.status == 'gebucht':
        return redirect(url_for('buchung_bp.update', buchung_id=buchung_id))
    else:       # abgerechnet
        return redirect(
            url_for('buchung_bp.anzeigen', buchung_id=buchung_id))


@buchung_bp.route('/update/<int:buchung_id>', methods=('GET', 'POST'))
@login_required
def update(buchung_id):

    buchung = Buchung.get_by_id(buchung_id)
    if buchung.status in ['abgerechnet', 'storno', 'verworfen']:
        flash(
            'Buchung {} mit Status {} kann nicht geändert werden!</br> \
            Vorauszahlung siehe linke Seite!'
            .format(buchung.id, buchung.status), 'error')
        return redirect(url_for('home_bp.index'))

    form = BuchungForm(obj=buchung)

    if form.validate_on_submit():
        buchung_alt = Buchung.get_by_id(buchung_id)     # save copy
        dirty_fields = update_buchung(form, buchung)
        if len(dirty_fields) > 0:                                # changes
            send_update_emails(buchung, buchung_alt, dirty_fields)
            # set flash
            flash("Update für {}, {} gespeichert".format(
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

    # left side actions
    actions = [
        (
            'Stornieren',
            url_for('buchung_bp.storno', buchung_id=buchung.id)),
        (
            'Abrechnen',
            url_for('buchung_bp.abrechnen', buchung_id=buchung.id))
    ]
    return render_template(
        'buchung/update.html',
        form=form,
        buchung=buchung,
        actions=actions,
        title='Buchung ändern',
        buchungen=buchung,
        besucher=buchung.besucher,
        waren_choices=Ware.choices(),
        verkaeufe=list(buchung.verkaeufe),
        run_mode=current_app.config['ENV']
    )


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

    # left side actions
    if buchung.status == 'gebucht':
        actions = [
            (
                'Ändern',
                url_for(
                    'buchung_bp.update',
                    buchung_id=buchung.id)),
            (
                'Rechnung',
                url_for('buchung_bp.rechnung', buchung_id=buchung.id))
        ]
    elif buchung.status == 'angebot':  # convert offer -> booking, drop angebot
        actions = [
            (
                'Umwandeln',
                url_for(
                    'buchung_bp.convert_angebot',
                    buchung_id=buchung.id)),
            (
                'Verwerfen',
                url_for(
                    'buchung_bp.drop_angebot',
                    buchung_id=buchung.id))
        ]
    elif buchung.status == 'abgerechnet':   # print or inptut prepayment
        actions = [
            (
                'Drucken',
                url_for(
                    'buchung_bp.rechnung',
                    buchung_id=buchung.id)),
            (
                'Vorauszahlung',
                url_for(
                    'buchung_bp.update_vorauszahlung',
                    buchung_id=buchung.id))
        ]

    return render_template(
        'buchung/anzeigen.html',
        buchung=buchung,
        actions=actions,
        title='{} anzeigen'.format(buchung.status.capitalize()),
        besucher=buchung.besucher,
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


@buchung_bp.route('/create_angebot/<int:besucher_id>', methods=('GET', 'POST'))
@login_required
def create_angebot(besucher_id):
    '''
        Create new offer, step 1
        - gather offer data
        at the end of this step:
        - validate the information
        - check availability of apartment (flash if not)
        - contiue to second step (create_buchung_finish)
    '''
    form = BuchungForm()
    form.user_id.data = session.get('user_id')
    form.besucher_id.data = besucher_id
    besucher = Besucher.get(besucher_id)
    if form.validate_on_submit():
        form.besucher_id = besucher_id
        session_data = form.data
        session_object = FlaskrSession.from_object(
            User.get(id=session['user_id']),
            session_data
        )
        session['create_angebot'] = session_object.id
        if besucher.email == "":
            flash('Besucher hat keine Email Adresse', 'error')
        if (
            Apartment
            .get_by_id(form.apartment_id.data)
            .check_availability(form.anreise.data, form.abreise.data)
        ):
            flash('Apartment is verfügbar')
        else:
            # TODO: Liste der verfügbaren Aprtments
            flash('Apartment ist nicht verfügbar!', 'error')

        return redirect(url_for('buchung_bp.create_angebot_finish'))

    return render_template(
        'buchung/create.html',
        besucher=besucher,
        form=form,
        title='Angebot anlegen',
        run_mode=current_app.config['ENV'],
        template='form-template'
    )


@buchung_bp.route('/create_angebot_finish', methods=('GET', 'POST'))
@login_required
def create_angebot_finish():
    '''
        Finalize new booking
        - check availability of apartment
        - prepare confirmation text
        - send emails and finish booking
    '''

    session_id = session['create_angebot']
    buchung = Buchung(**FlaskrSession.get(id=session_id).as_object())
    buchung.recalc(status='angebot')
    # prepare email_confirmation_email
    form = Buchung2Form()
    if request.method == 'GET':
        form.email_text.data = render_template(
            'emails/{buchung.besucher.language.lower()}/angebot.html',
            days=(buchung.abreise - buchung.anreise).days,
            buchung=buchung
        )

    if form.validate_on_submit():
        # save booking
        buchung.id = None
        buchung.save()
        send_angebot_emails(buchung, form.email_text.data)
        # flash message
        flash(
            'Angebot {} Apt {} vom {} - {} für {}, {} gespeichert'.format(
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

    return render_template(
        'buchung/create_part2.html',
        besucher=buchung.besucher,
        buchung=buchung,
        form=form,
        title='Neues Angebot fertigstellen',
        run_mode=current_app.config['ENV'],
        template='form-template')


@buchung_bp.route('/convert_angebot/<int:buchung_id>', methods=('GET', 'POST'))
@login_required
def convert_angebot(buchung_id):
    '''
        Convert offer to booking
        - prepare confirmation text
        - send emails and finish booking
    '''
    buchung = Buchung.get_by_id(buchung_id)
    besucher = buchung.besucher
    form = Buchung2Form()
    if request.method == 'GET':
        form.email_text.data = render_template(
            'emails/{}/buchung_confirmation.html'
            .format(besucher.language.lower()),
            buchung=buchung
        )

    if form.validate_on_submit():
        # save booking
        buchung.status = 'gebucht'
        buchung.save()
        send_confirmation_emails(buchung, form.email_text.data)
        # flash message
        flash(
            'Buchung {} Apt {} vom {} - {} für {}, {} gespeichert'.format(
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
                    besucher_id=besucher.id)))

    return render_template(
        'buchung/create_part2.html',
        besucher=besucher,
        buchung=buchung,
        form=form,
        title='Angebot umwandeln',
        run_mode=current_app.config['ENV'],
        template='form-template')


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

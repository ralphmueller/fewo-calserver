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
from flask import (
    Blueprint,
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
    StaticValuesBuchung)

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

buchung_bp = Blueprint(
    'buchung_bp',
    __name__,
    url_prefix='/buchung',
    template_folder='templates',
    static_folder='static'
)


@buchung_bp.route('/')
@login_required
def index():
    # list all bookings that have status field as described in request args
    # get only 'limit' bookings if set
    request_params_status = request.args.get('status')
    if request_params_status is not None:
        where_list = request_params_status.split(',')
    else:
        where_list = [
            'gebucht',
            'abgerechnet'
        ]
    if request.args.get('year') is None:
        year = datetime.date.today().year
    else:
        year = int(request.args.get('year'))
    query = (
        Buchung
        .select()
        .join(Apartment)
        .switch(Buchung)
        .join(Besucher)
        .where(
            Buchung.status.in_(where_list) &
            Buchung.anreise.between(
                datetime.date(year, 1, 1),
                datetime.date(year + 1, 1, 1))
        )
        .order_by(Buchung.anreise.desc())
    )

    return render_template(
        'buchung/index.html',
        number_buchung=len(list(query)),
        title='Buchungen (Status = {}, Anzahl = {})'.format(
            request_params_status,
            len(list(query))),
        buchungen=query,
        year=year,
        status=request_params_status,
        years=SystemInfo.get_years(),
        run_mode=current_app.env)


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

        return(redirect(url_for('buchung_bp.create_buchung_finish')))

    return render_template(
        'buchung/create.html',
        besucher=besucher,
        form=form,
        title='Buchung anlegen',
        run_mode=current_app.env,
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
        return(
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
        run_mode=current_app.env,
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
        return(redirect(url_for('home_bp.index')))

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

        return(
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
        run_mode=current_app.env
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
        return(redirect(url_for('home_bp.index')))
    form = MeldescheinForm()

    if form.validate_on_submit():
        # save meldeschein data
        buchung.meldeschein_nummer = form.meldeschein_nummer.data
        # set status to abgrechnet
        buchung.status = 'abgerechnet'
        buchung.rechnungs_nummer = '{}-{:03}-{}'.format(
            buchung.apartment.name,
            buchung.apartment.get_next_invoice_no(),
            datetime.date.today().year)
        buchung.rechnungsdatum = buchung.anreise
        buchung.save()
        return(
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
        run_mode=current_app.env
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
        run_mode=current_app.env
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

    return render_template(
        'print/rechnung.html',
        buchung=buchung,
        days=(buchung.abreise - buchung.anreise).days,
        actions=actions,
        mwst_satz=StaticValuesBuchung.mwstsatz(),
        title='Buchung anzeigen',
        run_mode=current_app.env
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

        return(redirect(url_for('buchung_bp.create_angebot_finish')))

    return render_template(
        'buchung/create.html',
        besucher=besucher,
        form=form,
        title='Angebot anlegen',
        run_mode=current_app.env,
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
            'emails/{}/angebot.html'
            .format(buchung.besucher.language.lower()),
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
        return(
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
        run_mode=current_app.env,
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
        return(
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
        run_mode=current_app.env,
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
    return(
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
        return(redirect(url_for('home_bp.index')))

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

        return(
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
        run_mode=current_app.env,
        template='form-template')

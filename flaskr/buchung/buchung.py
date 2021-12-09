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
    Email,
    StaticValuesBuchung)

from .buchung_forms import BuchungForm, Buchung2Form, MeldescheinForm

from flaskr.auth.auth import login_required
from flaskr.api import update_buchung
from flaskr import mailer

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
    request_params = request.args.get('where')
    if request_params is not None:
        where_list = request_params.split()
    else:
        where_list = [
            'gebucht',
            'abgerechnet'
        ]
    query = (
        Buchung
        .select()
        .join(Apartment)
        .switch(Buchung)
        .join(Besucher)
        .where(Buchung.status.in_(where_list))
        .order_by(Buchung.anreise)
    )
    if len(list(query)) > 0:
        return render_template(
            'buchung/index.html',
            number_buchung=len(list(query)),
            title='Buchungsliste',
            buchungen=query,
            run_mode=current_app.env
        )
    else:
        flash('no bookings found for status ', where_list)
        return(redirect(url_for('home.index')))


@buchung_bp.route('/create/<int:besucher_id>', methods=('GET', 'POST'))
@login_required
def create_buchung(besucher_id):
    '''
        Create new booking, step 1
        - gather booking data
        at the end of this step:
        - validate the information
        - check availability of apartment (flash if not)
        - contiue to second step (create_buchung_finish)
    '''
    form = BuchungForm()
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
        if (
            Apartment
            .get_by_id(form.apartment_id.data)
            .check_availability(form.anreise.data, form.abreise.data)
        ):
            flash('Apartment is verfügbar')
        else:
            # TODO: Liste der verfügbaren Aprtments
            flash('Apartment ist nicht verfügbar!', 'error')

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
            'emails/buchung_confirmation.html',
            buchung=buchung
        )

    if form.validate_on_submit():
        # save booking
        buchung.id = None
        buchung.save()
        # create email record
        besucher_email = Email()
        besucher_email.besucher = besucher
        besucher_email.buchung = buchung
        besucher_email.header = (
            'Buchungsbestätigung Apartment {}, {} vom {} bis {}'
            .format(
                buchung.apartment.name,
                buchung.apartment.beschreibung,
                format_date(buchung.anreise, format='full', locale='de_DE'),
                format_date(buchung.abreise, format='full', locale='de_DE')))
        besucher_email.body = form.email_text.data
        besucher_email.save()
        # email section
        # prepare email to besucher
        mailer.add_email(
            [besucher.email],
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
        # flash message
        flash(
            'Buchung {} Apt {} vom {} - {} für {}, {} gespeichert'.format(
                buchung.id, 
                buchung.apartment.name,
                format_date(buchung.anreise, format='full', locale='de_DE'),
                format_date(buchung.abreise, format='full', locale='de_DE'),
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
        res = update_buchung(form, buchung)
        if len(res) > 0:                                # changes
            # send emails
            if 'vorauszahlung' in res:
                # send payment confirmation to besucher
                email_html = render_template(
                    'emails/buchung_vorauszahlung.html',
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
            'Buchung stornieren',
            url_for('buchung_bp.storno', buchung_id=buchung.id)),
        (
            'Buchung abrechnen',
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
    flash('buchung vorauszahlung not implemented yet')
    return(redirect(url_for('home_bp.index')))


@buchung_bp.route('/storno/<int:buchung_id>')
@login_required
def storno(buchung_id):
    buchung = Buchung.get_by_id(buchung_id)
    buchung.status = 'storno'
    buchung.save()
    # sending emails
    # email to visitor
    email_html = render_template(
        'emails/buchung_storno.html',
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
    # done, back to visitor
    flash('Buchung {} storniert'.format(buchung_id))
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
    actions = [
        (
            'Buchung ändern',
            url_for('buchung_bp.update_vorauszahlung', buchung_id=buchung.id)),
        (
            'Rechnung',
            url_for('buchung_bp.rechnung', buchung_id=buchung.id))
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
            'Rechnung Drucken',
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
    besucher = Besucher.get(buchung.besucher_id)
    # prepare email_confirmation_email
    form = Buchung2Form()
    if request.method == 'GET':
        form.email_text.data = render_template(
            'emails/angebot.html',
            days=(buchung.abreise - buchung.anreise).days,
            buchung=buchung
        )

    if form.validate_on_submit():
        # save booking
        buchung.id = None
        buchung.save()
        # create email record
        besucher_email = Email()
        besucher_email.besucher = besucher
        besucher_email.buchung = buchung
        besucher_email.header = (
            'Angebot Apartment {}, {} vom {} bis {}'
            .format(
                buchung.apartment.name,
                buchung.apartment.beschreibung,
                format_date(buchung.anreise, format='full', locale='de_DE'),
                format_date(buchung.abreise, format='full', locale='de_DE')))
        besucher_email.body = form.email_text.data
        besucher_email.save()
        # email section
        # prepare email to besucher
        mailer.add_email(
            [besucher.email],
            current_app.config['EMAILS_TEAM'],
            besucher_email.header,
            besucher_email.body,
            'empty'
        )
        # send all emails; email server quits after sending
        mailer.send_emails()
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

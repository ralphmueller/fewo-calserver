'''
Created on 04.10.2021

@author: ralph

* create, delete (storno, dispose), list buchungen, angebote, rechnungen
* change angebote into buchungen
* change buchungen into rechnungen
* initiate emails to team and besucher

'''
from babel.dates import format_date
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
from bkormlib import Buchung, Besucher, Apartment, User, FlaskrSession, Email
from rmemaillib import mailer

from .buchung_forms import BuchungForm, Buchung2Form

from flaskr.auth.auth import login_required

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
            'verworfen',
            'angebot',
            'storno',
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
        title='Neue Buchung anlegen',
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
            ['ralph.mueller.de@gmail.com'],
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
                format_date(buchung.anreise, format='full', locale='de_DE'),
                format_date(buchung.abreise, format='full', locale='de_DE')))

        mailer.add_email(
            ['ralph.mueller.de@gmail.com'],     # team ...
            [],                                 # nobody in cc
            header,
            email_html,
            'empty'
        )

        mailer.send_emails()
        mailer.close()
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
        res = form.update_buchung(buchung)
        
        if res:
            # TODO: send email to team

            # set flash
            flash("Update für {}, {} gespeichert".format(
                buchung.id, buchung.besucher.name
                ))
        else:
            # set flash
            flash("Keine Änderung für {}, {} gespeichert".format(
                buchung.id, buchung.besucher.name
                ))

        return(redirect(url_for('home_bp.index')))

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
        'buchung/create.html',
        form=form,
        actions=actions,
        title='{}, {}'.format(
                buchung.besucher.name,
                buchung.besucher.vorname
            ),
        buchungen=buchung,
        besucher=buchung.besucher,
        run_mode=current_app.env
    )


@buchung_bp.route('/vorauszahlung/<int:buchung_id>', methods=('GET', 'POST'))
@login_required
def vorauszahlung(buchung_id):
    flash('buchung vorauszahlung not implemented yet')
    return(redirect(url_for('home_bp.index')))


@buchung_bp.route('/storno/<int:buchung_id>')
@login_required
def storno(buchung_id):
    flash('buchung storno not implemented yet')
    return(redirect(url_for('home_bp.index')))


@buchung_bp.route('/abrechnen/<int:buchung_id>')
@login_required
def abrechnen(buchung_id):
    flash('buchung abrechnen not implemented yet')
    return(redirect(url_for('home_bp.index')))

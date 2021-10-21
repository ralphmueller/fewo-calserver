'''
Created on 04.10.2021

@author: ralph

* create, delete (storno, dispose), list buchungen, angebote, rechnungen
* change angebote into buchungen
* change buchungen into rechnungen
* initiate emails to team and besucher

'''

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
from bkormlib import Buchung, Besucher, Apartment, User, FlaskrSession

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
        print(
            len(list(query)),
            list(query)[0].anreise,
            list(query)[0].besucher.name)
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
        gather data 
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

        flash(
            'Neue Buchung Daten: {}'
            .format(str(form.data))
        )
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
    email_html = render_template(
        'buchung_confirmation_email.html',
        buchung=buchung
    )
    form = Buchung2Form(object=buchung)
    form.email_text.data = email_html

    if form.validate_on_submit():
        # check if apartment is available
        # 
        return(redirect(url_for('besucher_bp.index')))

    return render_template(
        'buchung/create_part2.html',
        besucher=besucher,
        buchung=buchung,
        form=form,
        title='Neue Buchung fertigstellen',
        run_mode=current_app.env,
        template='form-template')


@buchung_bp.route('/update/<int:id>', methods=('GET', 'POST'))
@login_required
def buchung(id):
    if request.method == 'POST':
        print('POST')
        print(request.form)
        flash('Supi!')
        return(redirect(url_for('home.index')))
    else:
        buchung = Buchung.get(Buchung.id == id)
        if buchung.status in ['abgerechnet', 'storno', 'verworfen']:
            print(
                'Buchung {} mit Status {} kann nicht geändert werden!'
                .format(buchung.id, buchung.status))
            flash(
                'Buchung {} mit Status {} kann nicht geändert werden!'
                .format(buchung.id, buchung.status), 'error')
            return(redirect(url_for('home.index')))

        return render_template(
            'buchung_display.html',
            buchung=buchung,
            run_mode=current_app.env
        )

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
    request
)

from bkormlib import Buchung, Besucher, Apartment

from .buchung_forms import BuchungForm

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
    print('where_list: ', where_list)
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

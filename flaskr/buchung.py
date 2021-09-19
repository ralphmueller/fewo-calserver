'''
Created on 9. April 2019

@author: ralph

rest functions buchung

'''
from flask import (
    render_template, flash, redirect, url_for, abort,
    Blueprint, request
    )

from bkormlib import envir
from bkormlib.schema import Buchung, Besucher, Apartment
from flaskr.auth.auth import login_required

bp = Blueprint('buchung', __name__, url_prefix='/buchung')

@bp.route('/')
@login_required
def index():
    request_params = request.args.get('where')
    print('where:', request_params)
    where_list = request_params.split()
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
    print(query.sql())
    print('len:', len(list(query)))
    if len(list(query)) > 0:
        print(len(list(query)), list(query)[0].anreise, list(query)[0].besucher.name)
        return(redirect(url_for('home.index')))
        return render_template(
            'buchung/index.html',
            number_buchung=len(list(query)),
            title='Buchungsliste',
            data=query,
            run_mode=envir
        )
    else:
        flash('no bookings found for status ', where_list)
        return(redirect(url_for('home.index')))


@bp.route('/create', methods=('GET', 'POST'))
def create_buchung():
    abort(404)


@bp.route('/update/<int:id>', methods=('GET', 'POST'))
def buchung(id):
    if request.method == 'POST':
        print('POST')
        print(request.form)
        flash('Supi!')
        return(redirect(url_for('home.index')))
    else:
        buchung = Buchung.get(Buchung.id == id)
        if buchung.status in ['abgerechnet', 'storno', 'verworfen']:
            print('Buchung {} mit Status {} kann nicht geändert werden!'.format(buchung.id, buchung.status))
            flash('Buchung {} mit Status {} kann nicht geändert werden!'.format(buchung.id, buchung.status), 'error')
            return(redirect(url_for('home.index')))
        besucher = buchung.besucher
        return render_template('buchung_display.html',
            buchung=buchung,
            run_mode=envir)

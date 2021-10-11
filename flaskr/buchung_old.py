'''
Created on 9. April 2019

@author: ralph

rest functions buchung

'''
from flask import (
    render_template, flash, redirect, url_for, abort,
    Blueprint, request, current_app
    )

from bkormlib.schema import Buchung, Besucher, Apartment
from flaskr.auth.auth import login_required

bp = Blueprint('buchung', __name__, url_prefix='/buchung')





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

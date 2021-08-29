'''
Created on 9. April 2019

@author: ralph

rest functions buchung

'''
from flask import Blueprint, render_template, request, flash, redirect, url_for
import datetime

from bkormlib import envir
from bkormlib.schema import Buchung, Besucher

bp = Blueprint('buchung', __name__, url_prefix='/buchung')

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
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

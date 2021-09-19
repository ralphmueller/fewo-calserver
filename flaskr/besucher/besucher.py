'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, flash, redirect, url_for, request

from bkormlib import envir

from flaskr.auth import login_required
from flaskr.api import (
    fetch_visitors,
    create_besucher_from_request_form,
    fetch_besucher_for_update,
    update_besucher_from_form,
    delete_besucher
)
besucher_bp = Blueprint(
    'besucher_bp',
    __name__,
    url_prefix='/besucher',
    template_folder='templates',
    static_folder='static'
)


@besucher_bp.route('/')
@login_required
def index():
    '''
        REST: List visitors
    '''
    data = fetch_visitors()

    if data is not None:
        return render_template(
            'besucher_index.jinja2',
            number_besucher=len(data),
            title='Besucherliste',
            data=data,
            run_mode=envir
        )
    else:
        flash('no visitors found')
        return(redirect(url_for('home.index')))


@besucher_bp.route('/find')
@login_required
def besucher_find():
    return render_template(
        'besucher_find.html',
        title="Finde Besucher",
        run_mode=envir)


@besucher_bp.route('/create', methods=('GET', 'POST'))
@login_required
def create_besucher():
    '''
        REST: Create new visitor
    '''
    if request.method == 'POST':
        id, name, vorname = create_besucher_from_request_form(request.form)
        flash(
            'Neuer Besucher gespeichert: {} {}, {}'
            .format(id, name, vorname)
        )
        return(redirect(url_for('besucher_bp.index')))

    return render_template(
        'besucher_create.html',
        title='Neuen Besucher anlegen', run_mode=envir
    )


@besucher_bp.route('/update/<int:id>', methods=('GET', 'POST'))
@login_required
def update(id):

    besucher, buchungen = fetch_besucher_for_update(id)

    if request.method == 'POST':
        action = request.form['button']

        if action == 'update':
            flash(update_besucher_from_form(id, request.form))
            return redirect(url_for('home_bp.index'))

        if action == 'delete':
            flash(delete_besucher(id))
            return redirect(url_for('home_bp.index'))

        if action == 'neues_angebot':
            return redirect('/buchung/create-angebot/besucher/{}'.format(id))
        if action == 'neue_buchung':
            return redirect('/buchung/create-buchung/besucher/{}'.format(id))

    return render_template(
        'besucher_update.jinja2',
        besucher=besucher, title='{}, {}'.format(
                besucher.name,
                besucher.vorname
            ),
        buchungen=buchungen
    )
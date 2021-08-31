'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, flash, redirect, url_for, request

from bkormlib import envir, Besucher

from flaskr.auth import login_required

bp = Blueprint('besucher', __name__, url_prefix='/besucher')

def update_from_form(besucher, form):
    if besucher.anrede != form["anrede"]:
        besucher.anrede = form["anrede"]
    if besucher.name != form["name"]:
        besucher.name = form["name"]
    if besucher.vorname != form["vorname"]:
        besucher.vorname = form["vorname"]
    if besucher.tel != form["tel"]:
        besucher.tel = form["tel"]     
    if besucher.email != form["email"]:
        besucher.email = form["email"]      
    if besucher.stadt != form["stadt"]:
        besucher.stadt = form["stadt"]     
    if besucher.plz != form["plz"]:
        besucher.plz = form["plz"]     
    if besucher.strasse != form["strasse"]:
        besucher.strasse = form["strasse"]    
    if besucher.land != form["land"]:
        besucher.land = form["land"]    
    return besucher

@bp.route('/')
@login_required
def besucher():
    query = (Besucher
        .select()
        .order_by(Besucher.name)
    )
    if len(list(query)) > 0:
        return render_template('besucher/index.html', number_besucher=len(list(query)), title='Besucherliste', data=query, run_mode=envir)
    else:
        flash('no visitors found')
        return(redirect(url_for('home.index')))

@bp.route('/find')
@login_required
def besucher_find():
    return render_template('besucher_find.html', title="Finde Besucher",
        run_mode=envir)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    besucher = Besucher.get(Besucher.id == id)

    if request.method == 'POST':
        name = request.form['name']
        vorname = request.form['vorname']
        email = request.form['email']

        error = None

        if (not name) or (not vorname) or (not email):
            error = 'Name / Vorname / Email fehlen!'

        if error is not None:
            flash(error)
        else:
            besucher = Besucher.get(Besucher.id == id)
            besucher = update_from_form(besucher, request.form)
            print('dirty', besucher.is_dirty())                                                                               
            if besucher.is_dirty():
                besucher.save()
                flash('{}, {} Änderungen gespeichert!'.format(besucher.name, besucher.vorname))
            else:
                flash('{}, {} wurde nicht geändert!'.format(besucher.name, besucher.vorname))
            return redirect(url_for('home.index'))

    return render_template('besucher/update.html', besucher=besucher, title='{}, {}'.format(besucher.name, besucher.vorname))
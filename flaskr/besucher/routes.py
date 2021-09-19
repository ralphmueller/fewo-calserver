'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, flash, redirect, url_for, request
from peewee import fn

from bkormlib import envir, Besucher, Buchung, Apartment

from flaskr.auth import login_required

besucher_bp = Blueprint(
    'besucher_bp',
    __name__,
    url_prefix='/besucher',
    template_folder='templates',
    static_folder='static'
)


def update_from_form(besucher, form):
    '''
        update besucher: check which fields need updating
    '''
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
    if besucher.vermerk != form["vermerk"]:
        besucher.vermerk = form["vermerk"]    
    return besucher


@besucher_bp.route('/')
@login_required
def index():
    '''
        REST: List visitors
    '''
    query = (Besucher
        .select()
        .order_by(Besucher.name)
    )
    if len(list(query)) > 0:
        return render_template(
            'besucher/index.html',
            number_besucher=len(list(query)),
            title='Besucherliste',
            data=query, 
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
    besucher = Besucher()
    if request.method == 'POST':
        besucher.name = request.form['name']
        besucher.vorname = request.form['vorname']
        besucher.email = request.form['email']
        besucher.tel = request.form['tel']
        besucher.plz = request.form['plz']
        besucher.name = request.form['name']
        besucher.stadt = request.form['stadt']
        besucher.strasse = request.form['strasse']
        besucher.land = request.form['land']
        besucher.vermerk = request.form['vermerk']
        besucher.save()
        flash(
            'Neuer Besucher gespeichert: {} {}, {}'
            .format(besucher.id, besucher.name, besucher.vorname)
        )
        return(redirect(url_for('besucher.index')))

    return render_template(
        'besucher/create.html',
        besucher=besucher, title='Neuen Besucher anlegen', run_mode=envir
    )


@besucher_bp.route('/update/<int:id>', methods=('GET', 'POST'))
@login_required
def update(id):

    besucher = Besucher.get(Besucher.id == id)

    buchungen = (Buchung
        .select(Buchung, Apartment)
        .join(Apartment)
        .where(Buchung.besucher == besucher).order_by(Buchung.anreise.desc())
    )

    if request.method == 'POST':
        name = request.form['name']
        vorname = request.form['vorname']
        email = request.form['email']
        action = request.form['button']
        if action == 'update':
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
                    flash(
                        '{}, {} Änderungen gespeichert!'.
                        format(besucher.name, besucher.vorname)
                    )
                else:
                    flash(
                        '{}, {} wurde nicht geändert!'
                        .format(besucher.name, besucher.vorname)
                    )
                return redirect(url_for('home.index'))

        if action == 'neues_angebot':
            return redirect('/buchung/create-angebot/besucher/{}'.format(besucher.id))
        if action == 'neue_buchung':
            return redirect('/buchung/create-buchung/besucher/{}'.format(besucher.id))

        if action == 'delete':
            no_buchungen = Buchung.select(fn.Count(Buchung.id).alias('count')).where(Buchung.besucher == besucher).scalar()
            if no_buchungen > 0:
                flash('Besucher {}, {} wurde nicht gelöscht, da {} Buchungen existieren!'.format(besucher.name, besucher.vorname, no_buchungen))
            else:
                besucher.delete_instance()
                flash('Besucher {}, {} gelöscht'.format(
                    besucher.name, besucher.vorname)
                    )
            return redirect(url_for('home.index'))  


    return render_template(
        'besucher/update.html', 
        besucher=besucher, title='{}, {}'.format(
                besucher.name,
                besucher.vorname
            ),
        buchungen=buchungen
    )
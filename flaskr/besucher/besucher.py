'''
Created on 20 March 2019

@author: ralph

find, list, update, create and delete besucher




'''
from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    current_app
)

from .besucher_forms import BesucherForm

from flaskr.auth.auth import login_required
from flaskr.api import (
    fetch_visitors,
    fetch_besucher_for_update,
    create_besucher_from_form
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
            'besucher/index.html',
            number_besucher=len(data),
            title='Besucherliste',
            data=data,
            run_mode=current_app.env
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
        run_mode=current_app.env)


@besucher_bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    '''
        REST: Create new visitor
    '''
    form = BesucherForm()
    if form.validate_on_submit():
        id, name, vorname = create_besucher_from_form(form)
        flash(
            'Neuer Besucher gespeichert: {} {}, {}'
            .format(id, name, vorname)
        )
        return(redirect(url_for('besucher_bp.index')))

    return render_template(
        'create.html',
        form=form,
        title='Neuen Besucher anlegen',
        run_mode=current_app.env,
        template='form-template'
    )


@besucher_bp.route('/update/<int:besucher_id>', methods=('GET', 'POST'))
@login_required
def update(besucher_id):

    besucher, buchungen = fetch_besucher_for_update(besucher_id)

    form = BesucherForm(obj=besucher)

    if form.validate_on_submit():
        res = form.update_besucher(besucher)
        flash(
            res
        )
        return(redirect(url_for('besucher_bp.index')))

    # left side actions
    actions = [
        (
            'Neue Buchung',
            url_for('buchung_bp.create_buchung', besucher_id=besucher.id))
    ]
    return render_template(
        'update.html',
        form=form,
        actions=actions,
        title='{}, {}'.format(
                besucher.name,
                besucher.vorname
            ),
        buchungen=buchungen,
        besucher=besucher,
        run_mode=current_app.env
    )

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
    request,
    url_for,
    current_app,
    session
)

from .besucher_forms import BesucherForm

from flaskr.auth.auth import login_required
from flaskr.utils.api import (
    fetch_visitors,
    fetch_besucher_for_update,
    create_besucher_from_form,
    update_besucher
)
from bkormlib import Besucher

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
    return render_template(
        'besucher/index.html',
        number_besucher=len(data),
        title='Besucherliste',
        data=data,
        run_mode=current_app.config['ENV']
    )


@besucher_bp.route('/find')
@login_required
def find():
    return render_template(
        'besucher/find.html',
        title="Finde Besucher",
        run_mode=current_app.config['ENV'])


@besucher_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if len(q) < 3:
        return ''

    parts = q.lower().split()
    def pat(s):
        return s.replace('*', '%')

    if len(parts) >= 2:
        where = (Besucher.name ** pat(parts[0])) & (Besucher.vorname ** pat(parts[1]))
    else:
        p = pat(parts[0])
        where = (Besucher.name ** p) | (Besucher.vorname ** p)

    data = Besucher.select().where(where).order_by(Besucher.name)
    return render_template('besucher/list_partial.html', data=data)


@besucher_bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    '''
        REST: Create new visitor
    '''
    form = BesucherForm()
    form.user_id.data = session.get('user_id')
    if form.validate_on_submit():
        besucher = create_besucher_from_form(form)
        flash(
            'Neuer Besucher angelegt: {} {}, {}'
            .format(besucher.id, besucher.name, besucher.vorname)
        )
        return(redirect(
            url_for('besucher_bp.update', besucher_id=besucher.id)))

    return render_template(
        'besucher/create.html',
        form=form,
        title='Neuen Besucher anlegen',
        run_mode=current_app.config['ENV'],
        template='form-template'
    )


@besucher_bp.route('/update/<int:besucher_id>', methods=('GET', 'POST'))
@login_required
def update(besucher_id):

    besucher, buchungen = fetch_besucher_for_update(besucher_id)

    form = BesucherForm(obj=besucher)

    if form.validate_on_submit():
        res = update_besucher(form, besucher)
        flash(
            res
        )
        return(redirect(
            url_for('besucher_bp.update', besucher_id=besucher.id)))

    # left side actions
    actions = [
        (
            'Neue Buchung',
            url_for('buchung_bp.create_buchung', besucher_id=besucher.id)),
        (
            'Neues Angebot',
            url_for('buchung_bp.create_angebot', besucher_id=besucher.id))
    ]
    return render_template(
        'besucher/update.html',
        form=form,
        actions=actions,
        title='{}, {}'.format(
                besucher.name,
                besucher.vorname
            ),
        buchungen=[
            b for b in buchungen if b.status in [
                'gebucht',
                'abgerechnet']],
        angebote=[
            b for b in buchungen if b.status in [
                'angebot']],
        besucher=besucher,
        list_type='long',
        run_mode=current_app.config['ENV']
    )

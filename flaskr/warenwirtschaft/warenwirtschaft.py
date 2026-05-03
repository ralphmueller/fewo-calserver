from collections import defaultdict

from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app,
)
from peewee import fn

from bkormlib import Ware, Verkauf, Buchung
from .warenwirtschaft_forms import WareForm, WareLieferungForm
from flaskr.auth.auth import login_required

warenwirtschaft_bp = Blueprint(
    'warenwirtschaft_bp',
    __name__,
    url_prefix='/warenwirtschaft',
    template_folder='templates',
)


@warenwirtschaft_bp.route('/')
@login_required
def index():
    waren = list(Ware.select().order_by(Ware.bezeichnung))
    return render_template(
        'warenwirtschaft/index.html',
        waren=waren,
        title='Warenwirtschaft',
        run_mode=current_app.config['ENV'],
    )


@warenwirtschaft_bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = WareForm()
    if form.validate_on_submit():
        Ware.create(
            bezeichnung=form.bezeichnung.data,
            preis=form.preis.data,
            mwst_satz=form.mwst_satz.data,
            mindestbestand=form.mindestbestand.data,
            menge_lager=0,
            lieferant=form.lieferant.data or None,
            active=form.active.data,
        ).save()
        flash('Artikel angelegt: {}'.format(form.bezeichnung.data))
        return redirect(url_for('warenwirtschaft_bp.index'))
    return render_template(
        'warenwirtschaft/create.html',
        form=form,
        title='Neuen Artikel anlegen',
        run_mode=current_app.config['ENV'],
    )


@warenwirtschaft_bp.route('/update/<int:ware_id>', methods=('GET', 'POST'))
@login_required
def update(ware_id):
    ware = Ware.get_by_id(ware_id)
    form = WareForm(obj=ware)
    if form.validate_on_submit():
        ware.bezeichnung = form.bezeichnung.data
        ware.preis = form.preis.data
        ware.mwst_satz = form.mwst_satz.data
        ware.mindestbestand = form.mindestbestand.data
        ware.lieferant = form.lieferant.data or None
        ware.active = form.active.data
        ware.save()
        flash('Artikel aktualisiert: {}'.format(ware.bezeichnung))
        return redirect(url_for('warenwirtschaft_bp.index'))
    return render_template(
        'warenwirtschaft/update.html',
        form=form,
        ware=ware,
        title='Artikel bearbeiten',
        run_mode=current_app.config['ENV'],
    )


@warenwirtschaft_bp.route('/lager/<int:ware_id>', methods=('GET', 'POST'))
@login_required
def lager(ware_id):
    ware = Ware.get_by_id(ware_id)
    form = WareLieferungForm()
    if form.validate_on_submit():
        zugang = form.zugang.data
        if zugang <= 0:
            flash('Lieferung muss größer als 0 sein.')
        else:
            ware.menge_lager += zugang
            ware.save()
            flash('Lieferung gebucht: {}x {} — neuer Bestand: {}'.format(
                zugang, ware.bezeichnung, ware.menge_lager))
            return redirect(url_for('warenwirtschaft_bp.index'))
    return render_template(
        'warenwirtschaft/lager.html',
        form=form,
        ware=ware,
        title='Lieferung buchen',
        run_mode=current_app.config['ENV'],
    )


@warenwirtschaft_bp.route('/statistik')
@login_required
def statistik():
    # 1. Top-Artikel: Menge und Umsatz pro Ware
    top_artikel = (
        Verkauf
        .select(
            Verkauf.ware,
            fn.SUM(Verkauf.menge).alias('total_menge'),
            fn.SUM(Verkauf.menge * Verkauf.preis_zum_zeitpunkt).alias('umsatz'),
        )
        .group_by(Verkauf.ware)
        .order_by(fn.SUM(Verkauf.menge * Verkauf.preis_zum_zeitpunkt).desc())
    )

    # 2. Warenerlös pro Jahr und Monat
    erloes_raw = (
        Verkauf
        .select(
            fn.YEAR(Verkauf.zeitpunkt).alias('jahr'),
            fn.MONTH(Verkauf.zeitpunkt).alias('monat'),
            fn.SUM(Verkauf.menge * Verkauf.preis_zum_zeitpunkt).alias('umsatz'),
        )
        .group_by(fn.YEAR(Verkauf.zeitpunkt), fn.MONTH(Verkauf.zeitpunkt))
        .order_by(fn.YEAR(Verkauf.zeitpunkt), fn.MONTH(Verkauf.zeitpunkt))
    )
    erloes_by_year = defaultdict(list)
    for row in erloes_raw:
        erloes_by_year[row.jahr].append((row.monat, float(row.umsatz)))

    # 3. Lagerbestand-Ampel
    lager = list(Ware.select().where(Ware.active).order_by(Ware.bezeichnung))
    for w in lager:
        if w.mindestbestand > 0 and w.menge_lager <= 0:
            w._ampel = 'rot'
        elif w.mindestbestand > 0 and w.menge_lager <= w.mindestbestand:
            w._ampel = 'gelb'
        else:
            w._ampel = 'gruen'

    return render_template(
        'warenwirtschaft/statistik.html',
        top_artikel=list(top_artikel),
        erloes_by_year=dict(erloes_by_year),
        lager=lager,
        title='Warenwirtschaft Statistik',
        run_mode=current_app.config['ENV'],
    )


def _waren_panel(buchung_id, error=None):
    buchung = Buchung.get_by_id(buchung_id)
    verkaeufe = list(Verkauf.select(Verkauf, Ware).join(Ware).where(Verkauf.buchung == buchung))
    waren = list(Ware.select().where(Ware.active == True).order_by(Ware.bezeichnung))
    waren_summe = sum(v.menge * v.preis_zum_zeitpunkt for v in verkaeufe)
    return render_template(
        'buchung/waren_panel_partial.html',
        buchung=buchung,
        verkaeufe=verkaeufe,
        waren=waren,
        waren_summe=waren_summe,
        error=error,
    )


@warenwirtschaft_bp.route('/verkauf/<int:buchung_id>', methods=('POST',))
@login_required
def verkauf_create(buchung_id):
    ware_id = int(request.form['ware_id'])
    menge = int(request.form['menge'])
    ware = Ware.get_by_id(ware_id)
    if menge <= 0:
        return _waren_panel(buchung_id, error='Menge muss größer als 0 sein.')
    if ware.menge_lager < menge:
        return _waren_panel(buchung_id,
                            error='Nicht genug auf Lager (verfügbar: {}).'.format(ware.menge_lager))
    Verkauf.create(
        buchung_id=buchung_id,
        ware=ware,
        menge=menge,
        preis_zum_zeitpunkt=ware.preis,
        mwst_zum_zeitpunkt=ware.mwst_satz,
    ).save()
    ware.menge_lager -= menge
    ware.save()
    return _waren_panel(buchung_id)


@warenwirtschaft_bp.route('/verkauf/delete/<int:verkauf_id>', methods=('POST',))
@login_required
def verkauf_delete(verkauf_id):
    v = Verkauf.get_by_id(verkauf_id)
    buchung_id = v.buchung_id
    ware = v.ware
    ware.menge_lager += v.menge
    ware.save()
    v.delete_instance()
    return _waren_panel(buchung_id)

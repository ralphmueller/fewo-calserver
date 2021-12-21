'''
Created on 10 Mar 2019

@author: ralph
'''
import json
import datetime
from flask import Blueprint, request
from playhouse.shortcuts import model_to_dict

from bkormlib.schema import Apartment, Buchung, Besucher

bp = Blueprint('rest', __name__, url_prefix='/rest')


@bp.route('/buchung/<buchung_id>')
def rest_booking_get(buchung_id):
    booking = (Buchung.
               select().
               join(Besucher).
               where(Buchung.id == buchung_id).
               get())
    return json.dumps(model_to_dict(booking), ensure_ascii=False, default=str)


@bp.route('/besucher/<besucher_id>')
def rest_besucher_get(besucher_id):
    besucher = (
        Besucher
        .select()
        .where(Besucher.id == besucher_id)
        .get())
    return json.dumps(model_to_dict(besucher), ensure_ascii=False, default=str)


@bp.route('/besucher_by_name/<besucher_name>')
def rest_besucher_by_name(besucher_name):
    '''
    return list of visitors for given name expression
        used in lookup_besucher.js
        - patterns like "%müller%" return records containing 'müller'
        - patterns like "müller%" return records containing '^[Mm]üller'
        - ** operator in peewee is 'ILIKE'
    '''
    print('/besucher_by_name/: ', besucher_name.replace('*', '%'))
    res = (
        Besucher
        .select()
        .where(Besucher.name ** besucher_name.lower().replace('*', '%'))
        )
    return json.dumps(
        [model_to_dict(r) for r in res],
        ensure_ascii=False, default=str)


@bp.route('/rechnung/<besucher_name>')
def rest_besucherliste_select(besucher_name):
    '''
    return list of invoices for given visitor
        used in lookup_invoice.js
    '''
    res = (
        Buchung
        .select()
        .join(Besucher)
        .where(
            (Besucher.name ** besucher_name.lower()) &
            (Buchung.status == "abgerechnet"))
        .order_by(Buchung.anreise.desc())
    )
    a = []
    for r in res:
        a.append(model_to_dict(r))
    return json.dumps(a, ensure_ascii=False, default=str)


@bp.route('/buchungen/besucher/<besucher_id>')
def rest_buchungen_for_besucher(besucher_id):
    """
        ?status='{'storno'|'gebucht'|'abgerechnet'}
    """
    status = request.args['status']
    res = (
        Buchung
        .select()
        .join(Besucher)
        .where((Besucher.id == besucher_id) & (Buchung.status == status))
        .order_by(Buchung.anreise.desc())
        )
    return json.dumps(
        [model_to_dict(r) for r in res], ensure_ascii=False, default=str
    )


@bp.route('/apartment/available/<apartment_id>')
def rest_apartment_available(apartment_id):
    """
        TODO: Need to get real values here
    """
    anreise = (
        datetime
        .datetime
        .strptime(request.args['anreise'], "%Y-%m-%d").date())
    abreise = (
        datetime
        .datetime
        .strptime(request.args['abreise'], "%Y-%m-%d").date())
    apt_available = (
        Apartment
        .get_by_id(apartment_id)
        .check_availability(anreise, abreise))
    if not apt_available:
        apts = [
           apt.name for apt in Apartment.select()
           if apt.active and apt.check_availability(anreise, abreise)]
    else:
        apts = []
    return json.dumps({'avail': apt_available, 'apartments': apts})


@bp.route('/by_years')
def by_years():
    """
        SELECT year(anreise), COUNT(*), sum(miete), sum(kurtaxe) from Buchung
            where status in ('abgerechnet', 'gebucht') group by year(anreise);
    """
    db = Buchung._meta.database
    cursor = db.execute_sql('SELECT year(anreise), COUNT(*), sum(miete), sum(kurtaxe) from Buchung where status in ("abgerechnet", "gebucht") group by year(anreise);')
    res = [row for row in cursor.fetchall()]

    return json.dumps(
        res, ensure_ascii=False, default=str
    )

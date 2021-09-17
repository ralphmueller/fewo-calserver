'''
Created on 10 Mar 2019

@author: ralph
'''
import json
from flask import Blueprint, request
from playhouse.shortcuts import model_to_dict

from bkormlib import envir
from bkormlib.schema import Buchung, Besucher

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
    besucher = (Besucher.
               select().
               where(Besucher.id == besucher_id).
               get())
    return json.dumps(model_to_dict(besucher), ensure_ascii=False, default=str)

@bp.route('/besucher_by_name/<besucher_name>')
def rest_besucher_by_name(besucher_name):
    '''
    return list of visitors for given name regex
        used in lookup_besucher.js
    '''
    reg = '^' + besucher_name
    res = (Besucher.
        select().
        where(Besucher.name.regexp(reg))
        )
    return json.dumps([model_to_dict(r) for r in res], ensure_ascii=False, default=str)

@bp.route('/rechnung/<besucher_name>')
def rest_besucherliste_select(besucher_name):
    '''
    return list of invoices for given visitor
        used in lookup_invoice.js
    '''
    reg = '^' + besucher_name
    res = (Buchung.
        select().
        join(Besucher).
        where(Besucher.name.regexp(reg) & (Buchung.status == "abgerechnet")).
        order_by(Buchung.anreise.desc())
        )
    a = []
    for r in res:
        a.append(model_to_dict(r))
    return json.dumps(a, ensure_ascii=False, default=str)

@bp.route('/buchungen/besucher/<besucher_id>')     # ?status = '{'storno'|'gebucht'|'abgerechnet'}
def rest_buchungen_for_besucher(besucher_id):
    status = request.args['status']
    res = (Buchung.
        select().
        join(Besucher).
        where((Besucher.id == besucher_id) & (Buchung.status == status)).
        order_by(Buchung.anreise.desc())
        )
    return json.dumps([model_to_dict(r) for r in res], ensure_ascii=False, default=str)

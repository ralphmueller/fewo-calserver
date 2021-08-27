'''
Created on 7 Mar 2019

@author: ralph
'''

import json
from flask import Blueprint
from playhouse.shortcuts import model_to_dict

from bkormlib.schema import Besucher, Buchung

bp = Blueprint('json', __name__, url_prefix='/json')

@bp.route('/rechnungsliste/<besucher_name>')
def rechnungen_besucher(besucher_name):
    reg = '^' + besucher_name
    res = (Buchung.
        select().
        join(Besucher).
        where(Besucher.name.regexp(reg) & (Buchung.status == "abgerechnet")).
        order_by(Buchung.anreise.desc())
        )
    return json.dumps([model_to_dict(r) for r in res], ensure_ascii=False, default=str)




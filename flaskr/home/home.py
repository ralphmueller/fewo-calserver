'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
import datetime
from flask import Blueprint, render_template, current_app
from bkormlib import Apartment, Buchung, Besucher

home_bp = Blueprint(
    'home_bp',
    __name__,
    url_prefix='/',
    template_folder='templates',
    static_folder='static'
)


@home_bp.route('/')
def index():
    where_list = ['gebucht', 'abgerechnet']
    anreisen = (
        Buchung
        .select()
        .join(Apartment)
        .switch(Buchung)
        .join(Besucher)
        .where(
            Buchung.status.in_(where_list) &
            Buchung.anreise.between(
                datetime.date.today(),
                datetime.date.today() + datetime.timedelta(days=10)))
        .order_by(Buchung.anreise)
    )
    abreisen = (
        Buchung
        .select()
        .join(Apartment)
        .switch(Buchung)
        .join(Besucher)
        .where(
            Buchung.status.in_(where_list) &
            Buchung.abreise.between(
                datetime.date.today(),
                datetime.date.today() + datetime.timedelta(days=5)))
        .order_by(Buchung.abreise)
    )

    return render_template(
        'index.html',
        title='',
        anreisen=list(anreisen),
        abreisen=list(abreisen),
        run_mode=current_app.env)

'''
Created on 9 Mar 2019

@author: ralph

all stats routes for calserver

'''
import json
from flask import Blueprint, render_template, request, current_app
import datetime

from bkormlib.schema import Apartment

from .fewo_reporting import (
    aggregate_byMonth_byApartment,
    calc_income_and_commission_for_years,
    calc_apartment_income_and_commission_for_years,
    calc_income_all_apartments_for_years,
    calc_income_apartment
)

YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021]
APTS = [a.name for a in Apartment.select().order_by(Apartment.name)]

bp = Blueprint('stats', __name__, url_prefix='/stats')

'''
not working
@bp.route('/stats_income_year')
def income_year():
    today = datetime.date.today()
    year = int(request.args.get('year') or today.year)
    data = []
    for apt in APTS:
        data.append([apt, *calc_income_apartment(apt, year)])
    return render_template('income_year_by_apartment.html',
        data=data, run_mode=current_app.env)
'''


@bp.route('/income_and_commission')
def income_and_commission():
    return render_template(
        'apartment_income_and_commission.html',
        sel='',
        chart_title="Einnahmen und Kommission",
        rest_url='/stats/rest/income_and_commission/',
        run_mode=current_app.env)


@bp.route('/income_apartments')
def income_apartments():
    return render_template(
        'apartment_income_and_commission.html',
        sel='',
        chart_title="Einnahmen Apartments",
        rest_url='/stats/rest/income_apartments',
        run_mode=current_app.env)


@bp.route('/income_and_commission/<apartment_name>')
def apartment_income_and_commission(apartment_name):
    return render_template(
        'apartment_income_and_commission.html',
        sel=apartment_name,
        chart_title=apartment_name + " Einnahmen und Kommission",
        rest_url='/stats/rest/income_apartment_and_commission/',
        run_mode=current_app.env)


@bp.route('/rest/income_year')
def stats_income_year():
    today = datetime.date.today()
    year = int(request.args.get('year') or today.year)
    data = []
    for apt in APTS:
        data.append([apt, *calc_income_apartment(apt, year)])
    return json.dumps(data)


@bp.route('/rest/income_apartment_and_commission/<apartment_name>')
def rest_apartment_income_and_commission(apartment_name):
    res = {}
    res['datasets'] = calc_apartment_income_and_commission_for_years(
        apartment_name,
        YEARS)
    res['dataset_labels'] = ['Einnahmen', 'Kommission']
    res['labels'] = YEARS
    return json.dumps(res, default=str)


@bp.route('/rest/income_and_commission/')
def rest_income_and_commission():
    res = {}
    res['datasets'] = calc_income_and_commission_for_years(YEARS)
    res['dataset_labels'] = ['Einnahmen', 'Kommission']
    res['labels'] = YEARS     # this is for linking to single apartment income
    return json.dumps(res, default=str)


@bp.route('/rest/income_apartments')
def rest_income_apartments():
    res = {}
    res['datasets'] = calc_income_all_apartments_for_years(APTS, YEARS)
    res['dataset_labels'] = APTS
    res['labels'] = YEARS
    res['single_apt_url'] = '/stats/income_and_commission/'
    res['comments'] = 'new'
    return json.dumps(res, default=str)


@bp.route('/rechnungen')
def abgerechnete_besuche():
    return render_template(
        'abgerechnete-besuche.html',
        data=aggregate_byMonth_byApartment(),
        run_mode=current_app.env,
    )

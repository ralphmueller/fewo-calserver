'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, request

from bkormlib import envir

bp = Blueprint('besucher', __name__, url_prefix='/besucher')

@bp.route('/find')
def besucher_find():
    return render_template('besucher_find.html',
        run_mode=envir)

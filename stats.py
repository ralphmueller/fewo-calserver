'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, request
import datetime

from bkormlib import envir
from bkormlib.schema import Besucher

bp = Blueprint('besucher', __name__, url_prefix='/besucher')

@bp.route('/find')
def besucher():
    return render_template('besucher_find.html',
        run_mode=envir)

'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, request

from bkormlib import envir

bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('/')
def index():
    return render_template('index.html',
        run_mode=envir)

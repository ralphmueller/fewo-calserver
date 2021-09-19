'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, request

from bkormlib import envir

home_bp = Blueprint(
    'home_bp',
    __name__,
    url_prefix='/',
    template_folder='templates',
    static_folder='static'
)


@home_bp.route('/')
def index():
    return render_template('index.jinja2', title='Welcome', run_mode=envir)

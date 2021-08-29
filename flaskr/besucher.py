'''
Created on 20 March 2019

@author: ralph

find or create besucher

'''
from flask import Blueprint, render_template, flash, redirect, url_for

from bkormlib import envir, Besucher

bp = Blueprint('besucher', __name__, url_prefix='/besucher')

@bp.route('/')
def besucher():
    query = (Besucher
        .select()
        .order_by(Besucher.name)
    )
    if len(list(query)) > 0:
        return render_template('besucher/index.html', besucher=query)
    else:
        flash('no visitors found')
        return(redirect(url_for('home.index')))

@bp.route('/find')
def besucher_find():
    return render_template('besucher_find.html',
        run_mode=envir)

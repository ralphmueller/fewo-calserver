'''
Created on 27.08.2021

@author: ralph
'''

import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from bkormlib.schema import User
from peewee import DoesNotExist

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        user = User()
        user.username = username
        user.password = generate_password_hash(password)

        user.save()

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        try:
            user  = User.get(User.username == username)
            if not check_password_hash(user.password, password):
                error = 'Incorrect password.'
        except DoesNotExist:
            error = 'Incorrect username.'
            session.clear()

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('home.index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    print('session - user-id = {}'.format(user_id))
    if user_id is None:
        g.user = None
    else:
        g.user = User.get(User.id==user_id)
        print('logged in as user {}'.format(g.user.username))

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
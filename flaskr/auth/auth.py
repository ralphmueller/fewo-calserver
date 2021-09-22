'''
Created on 27.08.2021

@author: ralph
'''

import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    current_app
)
from werkzeug.security import check_password_hash, generate_password_hash

from bkormlib import User
from peewee import DoesNotExist


from .auth_forms import LoginForm

auth_bp = Blueprint(
    'auth_bp',
    __name__,
    url_prefix='/auth',
    template_folder='templates',
    static_folder='static'
)


@auth_bp.route('/register', methods=('GET', 'POST'))
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

    return render_template('register.html')


@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    error_message = 'Benutzer Name oder Password nicht korrekt'
    form = LoginForm()
    if form.validate_on_submit():
        error = None
        try:
            user = User.get(User.username == form.user.data)
            if not check_password_hash(user.password, form.password.data):
                error = error_message
        except DoesNotExist:
            error = error_message
            session.clear()

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('home_bp.index'))
        flash(error, 'error')
        return redirect(url_for('auth_bp.login'))

    return render_template(
        'login.html',
        form=form,
        title='Login',
        run_mode=current_app.env,
        template='form-template'
    )


@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.get(User.id == user_id)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home_bp.index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Login Required')
            return redirect(url_for('auth_bp.login'))
        return view(**kwargs)
    return wrapped_view

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
    session,
    url_for,
    current_app
)
from werkzeug.security import check_password_hash, generate_password_hash

from bkormlib import User
from peewee import DoesNotExist

from .auth_forms import LoginForm, RegisterForm, ChangePasswordForm

auth_bp = Blueprint(
    'auth_bp',
    __name__,
    url_prefix='/auth',
    template_folder='templates',
    static_folder='static'
)


@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    error_message = 'Benutzer Name oder Password nicht korrekt'
    form = LoginForm()
    if form.validate_on_submit():
        error = None
        try:
            user = User.get(User.username == form.user.data)
        except DoesNotExist:
            error = error_message
            current_app.logger.warning('username %s invalid', form.user.data)
            session.clear()

        if error is None:
            if not check_password_hash(user.password, form.password.data):
                # wrong password
                error = error_message
                current_app.logger.warning(
                    'user %s wrong password',
                    form.user.data)

        if error is None:
            session.clear()
            session['user_id'] = user.id
            current_app.logger.info(
                'user %s logged in',
                form.user.data)
            return redirect(url_for('home_bp.index'))
        
        flash(error, 'error')
        return redirect(url_for('auth_bp.login'))

    return render_template(
        'login.html',
        form=form,
        title='Anmelden',
        run_mode=current_app.config['ENV'],
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
    ''' need to login before accessing this view '''
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth_bp.login'))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    ''' need to be admin to access this view '''
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth_bp.login'))
        else:
            if not g.admin:
                return redirect(url_for('auth_bp.login'))
        return view(**kwargs)
    return wrapped_view


@auth_bp.route('/profile', methods=('GET', 'POST'))
@login_required
def change_password():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    form = ChangePasswordForm()

    if form.validate_on_submit():
        user.password = generate_password_hash(form.new_password.data)
        user.save()
        flash('Passwort geändert')
        return redirect(url_for('home_bp.index'))

    return render_template(
        'change_password.html',
        form=form,
        user=user,
        title='Password ändern',
        run_mode=current_app.config['ENV'],
        template='form-template')


@auth_bp.route('/register', methods=('GET', 'POST'))
@login_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.user.data
        password = form.password.data
        user = User()
        user.username = username
        user.password = generate_password_hash(password)
        user.save()
        flash('Neuer Benutzer angelegt')
        return redirect(url_for('home_bp.index'))

    return render_template(
        'register.html',
        form=form,
        title='Benutzer anlegen',
        run_mode=current_app.config['ENV'],
        template='form-template'
    )

'''
Created on 13.09.2016

Refactoring ongoing (7.3.2019)

Rewrite Oct. 2021

@author: ralph
'''
from babel.numbers import format_decimal, format_percent
from babel.numbers import format_currency
from babel.dates import format_date
from flask import Flask, render_template, session, g
from flask_cors import CORS
from bkormlib.schema import db_connect
from rmemaillib.email import EmailObject
from flask_wtf.csrf import CSRFProtect

import config

mailer = EmailObject.from_object(config.EmailConfig)
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)

    if test_config is None:
        app.config.from_object('config.Config')
        app.config.from_object('config.EmailConfig')
        print(app.config.get('FLASK_ENV'), app.config.get('DATABASE'))
        db = db_connect(
            app.config.get('FLASK_ENV'), app.config.get('DATABASE'))
        app.config['DB'] = db
    else:
        app.config.update(test_config)

    CORS(app)
    csrf.init_app(app)

    @app.before_request
    def _database_connect():
        db = app.config['DB']
        db.connection().ping(reconnect=True)

    @app.before_request
    def fix_missing_csrf_token():
        if app.config['WTF_CSRF_FIELD_NAME'] not in session:
            if app.config['WTF_CSRF_FIELD_NAME'] in g:
                g.pop(app.config['WTF_CSRF_FIELD_NAME'])

    app_context = app.app_context()
    app_context.push()

    @app.template_filter()
    def rabatt(value):
        return '{} %'.format(value)

    @app.template_filter()
    def euro_percent(value):
        return format_percent(value, locale='de_DE')

    @app.template_filter()
    def euro_decimal(value):
        return format_decimal(value, locale='de_DE')

    @app.template_filter()
    def euro_currency(value):
        return format_currency(value, '€', locale='de_DE')

    @app.template_filter()
    def euro_date(value):
        return format_date(value, locale='de_DE', format="full")

    @app.template_filter()
    def euro_date_short(value):
        return format_date(value, locale='de_DE', format="short")

    """
    from flask_debugtoolbar import DebugToolbarExtension
    _ = DebugToolbarExtension(app)
    """
    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        # note that we set the 500 status explicitly
        return render_template('500.html'), 500

    with app.app_context():
        from .home import home
        from .auth import auth
        from .besucher import besucher
        from .buchung import buchung
        from . import rest
        from . import stats
        from .calendar import calendar
        from . import json_routes

        app.register_error_handler(404, page_not_found)
        app.register_error_handler(500, internal_error)

        app.register_blueprint(home.home_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(besucher.besucher_bp)
        app.register_blueprint(buchung.buchung_bp)
        app.register_blueprint(rest.bp)
        app.register_blueprint(stats.bp)
        app.register_blueprint(calendar.calendar_bp)
        app.register_blueprint(json_routes.bp)

    """        @app.route("/resetinvoice/")
            @login_required
            def reset_invoice_new():
                return render_template('reset_invoice_new.html',
                run_mode=app.env)
    """

    return app

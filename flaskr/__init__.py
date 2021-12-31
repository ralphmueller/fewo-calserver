'''
Created on 13.09.2016

Refactoring ongoing (7.3.2019)

Rewrite Oct. 2021

@author: ralph
'''
from flask import Flask, session, g
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

    """
    from flask_debugtoolbar import DebugToolbarExtension
    _ = DebugToolbarExtension(app)
    """

    with app.app_context():
        import flaskr.utils.assets
        import flaskr.utils.custom_filters
        import flaskr.blueprints
        import flaskr.utils.error_handlers

    return app

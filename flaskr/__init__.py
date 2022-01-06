'''
Created on 13.09.2016

Refactoring ongoing (7.3.2019)

Rewrite Oct. 2021

@author: ralph
'''
from flask import Flask, session, g
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)

    if test_config is None:
        app.config.from_object('config.Config')
        app.config.from_object('config.EmailConfig')
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
        from .utils import assets
        from .utils import custom_filters
        import flaskr.blueprints
        from .utils import error_handlers

    return app

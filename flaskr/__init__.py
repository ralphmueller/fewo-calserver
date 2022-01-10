'''
Created on 13.09.2016

Rewrite Oct. 2021 -> new Booking program

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

    app.config['TEMPLATES_AUTO_RELOAD'] = True

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
        from .utils import assets               # noqa: F401
        from .utils import custom_filters       # noqa: F401
        import flaskr.blueprints                # noqa: F401
        from .utils import error_handlers       # noqa: F401

    return app

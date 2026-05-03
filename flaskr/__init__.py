'''
Created on 13.09.2016

Rewrite Oct. 2021 -> new Booking program

19.01.2024 add logger, can be used
    from flask import current app
    ...
    current_app.logger.{info|warning|error|...}(msg)

@author: ralph
'''
import sys
import re
import logging
from flask import Flask, session, g
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def createLogger(service_name):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:
        from systemd import journal                  # type: ignore
        logger.addHandler(journal.JournaldLogHandler())
    except Exception:
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)
    logger.setLevel(logging.INFO)
    return logger


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)

    logger = createLogger('fewo-calserver')

    if test_config is None:
        app.config.from_object('config.Config')
        app.config.from_object('config.EmailConfig')
        logger.info(
            'env: {}, Database:  {}'.format(
                app.config['ENV'],
                re.sub(r":\w+@", ":_______@", app.config['DATABASE'])))
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

    @app.context_processor
    def inject_operator():
        import os
        kv = float(os.environ.get('KURTAXE_SATZ_VZ', '2.1'))
        kh = float(os.environ.get('KURTAXE_SATZ_HZ', '0.5'))
        return {'operator': {
            'name':           os.environ.get('OPERATOR_NAME', ''),
            'inhaber':        os.environ.get('OPERATOR_INHABER', ''),
            'strasse':        os.environ.get('OPERATOR_STRASSE', ''),
            'plz_ort':        os.environ.get('OPERATOR_PLZ_ORT', ''),
            'gemeinde':       os.environ.get('OPERATOR_GEMEINDE', ''),
            'tel':            os.environ.get('OPERATOR_TEL', ''),
            'tel_intl':       os.environ.get('OPERATOR_TEL_INTL', ''),
            'email':          os.environ.get('OPERATOR_EMAIL', ''),
            'website':        os.environ.get('OPERATOR_WEBSITE', ''),
            'iban':           os.environ.get('OPERATOR_IBAN', ''),
            'bic':            os.environ.get('OPERATOR_BIC', ''),
            'ust_id':         os.environ.get('OPERATOR_UST_ID', ''),
            'paypal':         os.environ.get('OPERATOR_PAYPAL', ''),
            'schluessel':     os.environ.get('OPERATOR_SCHLUESSEL', ''),
            'wlan_ssid':      os.environ.get('OPERATOR_WLAN_SSID', ''),
            'kurtaxe_link':   os.environ.get('OPERATOR_KURTAXE_LINK', ''),
            'storno_frist':   os.environ.get('OPERATOR_STORNO_FRIST', '7'),
            'storno_gebuehr': os.environ.get('OPERATOR_STORNO_GEBUEHR', '50'),
            'kurtaxe_satz_vz': f'{kv:.2f}'.replace('.', ','),
            'kurtaxe_satz_hz': f'{kh:.2f}'.replace('.', ','),
        }}

    with app.app_context():
        from .utils import assets               # noqa: F401
        from .utils import custom_filters       # noqa: F401
        import flaskr.blueprints                # noqa: F401
        from .utils import error_handlers       # noqa: F401
        from .cli import register_commands
        register_commands(app)

    return app

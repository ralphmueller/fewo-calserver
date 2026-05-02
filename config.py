'''
Config class for flask app

Created on 19.09.2021

@author: ralph
'''
from os import environ, path
from dotenv import load_dotenv
import datetime
import socket
from bkormlib.schema import db_connect
from rmemaillib.email import EmailObject

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class EmailConfig:
    EMAIL_ADDRESS = environ.get('EMAIL_ADDRESS')
    EMAIL_USER = environ.get('EMAIL_USER')
    EMAIL_PASSWORD = environ.get('EMAIL_PASSWORD')
    EMAIL_HOST = environ.get('EMAIL_HOST')
    EMAIL_SSL = False
    EMAIL_PORT = 587


class Config:
    """Set Flask config variables."""
    ENV = environ.get('ENV')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=30)
    SECRET_KEY = environ.get('SECRET_KEY')
    DATABASE = environ.get(ENV.upper() + '_DATABASE')
    DB = db_connect(ENV, DATABASE)
    MAILER = EmailObject.from_object(EmailConfig)
    HOST = socket.gethostname()
    IP_ADDRESS = socket.gethostbyname(HOST)

    # for the assets pipeline
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = True

    if ENV == 'development':
        TESTING = True
        EMAILS_TEAM = [e.strip() for e in environ.get('EMAILS_TEAM', '').split(',') if e.strip()]
        INFO_EMAIL = [e.strip() for e in environ.get('INFO_EMAIL', '').split(',') if e.strip()]
    if ENV == 'staging':
        TESTING = True
        SERVER_NAME = environ.get('SERVER_NAME', None)
        EMAILS_TEAM = [e.strip() for e in environ.get('EMAILS_TEAM', '').split(',') if e.strip()]
        INFO_EMAIL = [e.strip() for e in environ.get('INFO_EMAIL', '').split(',') if e.strip()]
    if ENV == 'production':
        TESTING = False
        EMAILS_TEAM = [e.strip() for e in environ.get('EMAILS_TEAM', '').split(',') if e.strip()]
        INFO_EMAIL = [e.strip() for e in environ.get('INFO_EMAIL', '').split(',') if e.strip()]


def get_db(cls=Config):
    return cls.DB


def get_mailer(cls=EmailConfig):
    return cls.MAILER

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
        EMAILS_TEAM = ['ralph.mueller.de@gmail.com']
        INFO_EMAIL = ['ralph.mueller.de@gmail.com']
    if ENV == 'staging':
        TESTING = True
        SERVER_NAME = 'garten4a.dyndns-remote.com'
        EMAILS_TEAM = ['ralph.mueller.de@gmail.com']
        INFO_EMAIL = ['ralph.mueller.de@gmail.com']
        SERVER_NAME = 'garten4a.dyndns-remote.com:8082'
    if ENV == 'production':
        SERVER_NAME = 'garten4a.dyndns-remote.com:82'
        TESTING = False
        EMAILS_TEAM = [
            'ralph.mueller.de@gmail.com',
            'susan.iwai@gmail.com']
        INFO_EMAIL = ['info@ferien-in-gersfeld.de']


def get_db(cls=Config):
    return cls.DB


def get_mailer(cls=EmailConfig):
    return cls.MAILER

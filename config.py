'''
Config class for flask app

Created on 19.09.2021

@author: ralph
'''

from os import environ, path
from dotenv import load_dotenv
import datetime

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config:
    """Set Flask config variables."""
    FLASK_ENV = 'development'
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)
    SECRET_KEY = environ.get('SECRET_KEY')
    DATABASE = environ.get(FLASK_ENV.upper() + '_DATABASE')

    if FLASK_ENV == 'development':
        TESTING = True
        EMAILS_TEAM = ['ralph.mueller.de@gmail.com']
        INFO_EMAIL = ['ralph.mueller.de@gmail.com']
    else:
        TESTING = False
        EMAILS_TEAM = [
            'ralph.mueller.de@gmail.com',
            'susan.iwai@gmail.com',
            'bianka.moeller73@googlemail.com']
        INFO_EMAIL = ['info@ferien-in-gersfeld.de']


class EmailConfig:
    EMAIL_ADDRESS = environ.get('EMAIL_ADDRESS')
    EMAIL_USER = environ.get('EMAIL_USER')
    EMAIL_PASSWORD = environ.get('EMAIL_PASSWORD')
    EMAIL_HOST = environ.get('EMAIL_HOST')
    EMAIL_SSL = False
    EMAIL_PORT = 587

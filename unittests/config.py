'''
Config class for app using bkormlib

Created on 19.09.2021

@author: ralph
'''

from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

print(path.join(basedir, '.env'))


class Config:
    """Set  config variables."""

    ENV = 'test'
    DATABASE = environ.get(ENV.upper() + '_DATABASE')

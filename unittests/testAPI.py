'''
Created on 14.10.2021

@author: ralph
'''

import os
import unittest
import datetime

from bkormlib.schema import db_connect, Buchung, Apartment
from config import Config

from flaskr.api import recalc_buchung

print(Config.ENV, Config.DATABASE, os.getcwd())

db = db_connect(Config.ENV, Config.DATABASE)

BUCHUNG = {
    'anreise': datetime.date(2021, 10, 10),
    'abreise': datetime.date(2021, 10, 15),
    'besucher_id': 1,
    'apartment_id': 1,
    'portal_id': 1,
    'kurtaxe_hz': 0,
    'kurtaxe_kinder': 0,
    'kurtaxe_nz': 0,
    'kurtaxe_vz': 2,
    'preis_nacht': 50,
    'zusatzkosten': 50,
    'rabatt': 0
}


class Test(unittest.TestCase):

    def setUp(self):
        Buchung.drop_table()
        Buchung.create_table()
        Apartment.drop_table()
        Apartment.create_table()

    def testBasicTrue(self):
        self.assertEqual(True, True)

    def testRecalcBuchung(self):
        buchung = Buchung(BUCHUNG)
        recalc_buchung(buchung)

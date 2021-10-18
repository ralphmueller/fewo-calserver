'''
Created on 14.10.2021

@author: ralph
'''

import os
import unittest

from bkormlib.schema import db_connect
from config import Config

print(Config.ENV, Config.DATABASE, os.getcwd())

db = db_connect(Config.ENV, Config.DATABASE)


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def testBasicTrue(self):
        self.assertEqual(True, True)


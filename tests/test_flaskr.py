import os
import tempfile

import pytest

from flaskr import init_app
from config import Config

from bkormlib.schema import db_connect

db = db_connect(Config.ENV, Config.DATABASE)


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app = init_app({'TESTING': True})

    with app.test_client() as client:
        with app.app_context():
            # db = db_connect(Config.ENV, Config.DATABASE)
            print('hello')
        yield client

    

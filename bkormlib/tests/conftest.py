"""
SQLite in-memory database for bkormlib unit tests.

These tests live in bkormlib/tests/ (NOT under tests/) so that the
outer tests/conftest.py bkormlib-mock does not interfere here.
"""

import pytest
from playhouse.db_url import connect
from bkormlib.schema import (
    database_proxy,
    User, Besucher, Buchung, Apartment, Portal,
    Preisliste, Email, UserLogging, Migration,
    Ware, Verkauf,
)

ALL_MODELS = [
    User, UserLogging, Portal, Apartment, Preisliste,
    Besucher, Buchung, Email, Migration,
    Ware, Verkauf,
]


@pytest.fixture(autouse=True)
def sqlite_db():
    """Fresh in-memory SQLite database for every test."""
    db = connect('sqlite:///:memory:')
    database_proxy.initialize(db)
    db.create_tables(ALL_MODELS)
    yield db
    db.drop_tables(ALL_MODELS)
    db.close()

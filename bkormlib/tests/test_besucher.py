"""
Tests for Besucher model — CRUD, constraints, backrefs.
Recovered from pythonpacks git history (commit beb12c5, removed in dbb7e48).
"""

import pytest
from peewee import IntegrityError
from bkormlib import Besucher

BESUCHER = [
    {'user_id': 1, 'anrede': 'Herr', 'name': 'Schmidt', 'vorname': 'Hans',
     'email': 'hans.schmidt@example.com', 'language': 'DE'},
    {'user_id': 1, 'anrede': 'Frau', 'name': 'Weber', 'vorname': 'Maria',
     'email': 'maria.weber@example.com', 'language': 'DE'},
]

INCOMPLETE_BESUCHER = {'anrede': 'Herr', 'name': 'Schmidt', 'vorname': 'Hans'}


class TestBesucherBasic:
    def setup_method(self):
        for b in BESUCHER:
            Besucher.create(**b).save()

    def test_names(self):
        assert Besucher.get_by_id(1).name == 'Schmidt'
        assert Besucher.get_by_id(2).name == 'Weber'

    def test_count(self):
        assert len(list(Besucher.select())) == 2

    def test_incomplete_data_raises(self):
        with pytest.raises(IntegrityError):
            Besucher.create(**INCOMPLETE_BESUCHER).save()

    def test_update(self):
        b = Besucher.get(Besucher.name == 'Schmidt')
        b.name = 'Meier'
        b.vorname = 'Peter'
        b.email = 'peter.meier@example.com'
        b.language = 'EN'
        b.save()
        updated = Besucher.get_by_id(1)
        assert updated.name == 'Meier'
        assert updated.vorname == 'Peter'
        assert updated.email == 'peter.meier@example.com'
        assert updated.language == 'EN'

    def test_delete(self):
        Besucher.get(Besucher.name == 'Schmidt').delete_instance()
        assert len(list(Besucher.select().where(Besucher.name == 'Schmidt'))) == 0

    def test_backrefs_empty_on_new_besucher(self):
        from bkormlib.schema import Email, Buchung
        b = Besucher.get_by_id(1)
        assert len(list(b.buchungen)) == 0
        assert len(list(b.emails)) == 0

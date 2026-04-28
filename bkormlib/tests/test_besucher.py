"""
Tests for Besucher model — CRUD, constraints, backrefs.
Recovered from pythonpacks git history (commit beb12c5, removed in dbb7e48).
"""

import pytest
from peewee import IntegrityError
from bkormlib import Besucher

BESUCHER = [
    {'user_id': 1, 'anrede': 'Herr', 'name': 'Mueller', 'vorname': 'Ralph',
     'email': 'ralph.mueller@gmail.com', 'language': 'DE'},
    {'user_id': 1, 'anrede': 'Frau', 'name': 'Iwai', 'vorname': 'Susan',
     'email': 'susan.iwai@gmail.com', 'language': 'DE'},
]

INCOMPLETE_BESUCHER = {'anrede': 'Herr', 'name': 'Mueller', 'vorname': 'Ralph'}


class TestBesucherBasic:
    def setup_method(self):
        for b in BESUCHER:
            Besucher.create(**b).save()

    def test_names(self):
        assert Besucher.get_by_id(1).name == 'Mueller'
        assert Besucher.get_by_id(2).name == 'Iwai'

    def test_count(self):
        assert len(list(Besucher.select())) == 2

    def test_incomplete_data_raises(self):
        with pytest.raises(IntegrityError):
            Besucher.create(**INCOMPLETE_BESUCHER).save()

    def test_update(self):
        b = Besucher.get(Besucher.name == 'Mueller')
        b.name = 'Meier'
        b.vorname = 'Peter'
        b.email = 'peter.meier@gmail.com'
        b.language = 'EN'
        b.save()
        updated = Besucher.get_by_id(1)
        assert updated.name == 'Meier'
        assert updated.vorname == 'Peter'
        assert updated.email == 'peter.meier@gmail.com'
        assert updated.language == 'EN'

    def test_delete(self):
        Besucher.get(Besucher.name == 'Mueller').delete_instance()
        assert len(list(Besucher.select().where(Besucher.name == 'Mueller'))) == 0

    def test_backrefs_empty_on_new_besucher(self):
        from bkormlib.schema import Email, Buchung
        b = Besucher.get_by_id(1)
        assert len(list(b.buchungen)) == 0
        assert len(list(b.emails)) == 0

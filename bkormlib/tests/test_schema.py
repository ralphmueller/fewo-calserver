"""
Tests for Portal, Apartment.choices(), StaticValuesBuchung, FlaskrSession, Preisliste.
Consolidated from testSchemaClassMethods.py, test_flask_session.py, test_preisliste.py.
Recovered from pythonpacks git history (commit beb12c5, removed in dbb7e48).
"""

import pytest
from bkormlib import Apartment, Portal, StaticValuesBuchung, FlaskrSession, User, Besucher
from bkormlib.schema import Preisliste

PORTALS = [
    {'name': 'booking.com', 'kommission_prozent': 12, 'active': True, 'collect': True},
    {'name': 'ferienzentrum.de', 'kommission_prozent': 0, 'active': True, 'collect': False},
    {'name': 'fewo-direkt.de', 'kommission_prozent': 0, 'active': False, 'collect': False},
]

APARTMENTS = [
    {'name': 'F1', 'beschreibung': 'Die schöne Wohnung F1', 'active': True},
    {'name': 'G1', 'beschreibung': 'Die schöne Wohnung G1', 'active': False},
]


class TestPortal:
    def setup_method(self):
        for p in PORTALS:
            Portal.create(**p).save()

    def test_portal_basic(self):
        assert Portal.get_by_id(1).name == 'booking.com'
        assert Portal.get_by_id(1).kommission_prozent == 12
        assert Portal.get_by_id(3).name == 'fewo-direkt.de'

    def test_choices_returns_only_active(self):
        choices = Portal.choices()
        assert choices == [(1, 'booking.com'), (2, 'ferienzentrum.de')]


class TestApartmentChoices:
    def setup_method(self):
        for a in APARTMENTS:
            Apartment.create(**a).save()

    def test_choices_returns_only_active(self):
        choices = Apartment.choices()
        assert choices == [(1, 'F1')]


class TestStaticValuesBuchung:
    def test_mwstsatz(self):
        assert StaticValuesBuchung.mwstsatz() == 7

    def test_ktsatz_vz(self):
        assert StaticValuesBuchung.ktsatz_vz() == 2.1

    def test_ktsatz_hz(self):
        assert StaticValuesBuchung.ktsatz_hz() == 0.5


class TestFlaskrSession:
    def setup_method(self):
        User.create(username='ralph', password='testpw', admin=True).save()
        for b in [
            {'user_id': 1, 'anrede': 'Herr', 'name': 'Mueller',
             'vorname': 'Ralph', 'email': 'r@example.com'},
            {'user_id': 1, 'anrede': 'Frau', 'name': 'Iwai',
             'vorname': 'Susan', 'email': 's@example.com'},
        ]:
            Besucher.create(**b).save()

    def test_create_session(self):
        data = [{'user_id': 1, 'name': 'test'}]
        session = FlaskrSession.from_object(User.get_by_id(1), data)
        assert type(session) is FlaskrSession
        assert session.user.username == 'ralph'

    def test_save_and_restore_session(self):
        data = [{'user_id': 1, 'name': 'test'}]
        FlaskrSession.from_object(User.get_by_id(1), data)
        restored = FlaskrSession.get_by_id(1)
        assert restored.user.username == 'ralph'
        assert restored.as_object() == data


class TestPreisliste:
    def setup_method(self):
        for a in APARTMENTS:
            Apartment.create(**a).save()

    def test_create_and_retrieve(self):
        Preisliste.create(
            apartment_id=1, year=2023,
            preis_2p=55.0, preis_2p_long=50.0, preis_wp=7.0).save()
        Preisliste.create(
            apartment_id=1, year=2024,
            preis_2p=65.0, preis_2p_long=60.0, preis_wp=8.0).save()

        p2023 = Preisliste.get(Preisliste.year == 2023)
        assert p2023.preis_2p == 55.0
        assert p2023.preis_2p_long == 50.0
        assert p2023.preis_wp == 7.0

        p2024 = Preisliste.get(Preisliste.year == 2024)
        assert p2024.preis_2p == 65.0
        assert p2024.preis_2p_long == 60.0
        assert p2024.preis_wp == 8.0

    def test_default_preis_wp(self):
        p = Preisliste(apartment_id=1, year=2023, preis_2p=55.0, preis_2p_long=50.0)
        assert p.preis_wp == 7.0

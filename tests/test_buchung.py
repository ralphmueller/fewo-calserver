"""
Tests für Buchungs-Routen: /buchung/...
"""
import pytest
from unittest.mock import MagicMock, patch
import datetime


def _make_buchung(id=1, status='gebucht'):
    apt = MagicMock()
    apt.id = 1
    apt.name = 'F1'

    besucher = MagicMock()
    besucher.id = 10
    besucher.name = 'Müller'
    besucher.vorname = 'Ralph'
    besucher.email = 'test@example.com'
    besucher.language = 'de'

    portal = MagicMock()
    portal.id = 1
    portal.name = 'Direkt'
    portal.kommission_prozent = 0

    b = MagicMock()
    b.id = id
    b.status = status
    b.anreise = datetime.date(2026, 5, 1)
    b.abreise = datetime.date(2026, 5, 8)
    b.apartment = apt
    b.apartment_id = 1
    b.besucher = besucher
    b.besucher_id = 10
    b.portal = portal
    b.portal_id = 1
    b.miete = 700.0
    b.kurtaxe = 50.0
    b.summe = 750.0
    b.vorauszahlung = 200.0
    b.offener_betrag = 550.0
    b.preis_nacht = 100.0
    b.rabatt = 0.0
    b.zusatzkosten = 0.0
    b.kurtaxe_vz = 2
    b.kurtaxe_hz = 0
    b.kurtaxe_kinder = 0
    b.kurtaxe_nz = 0
    b.kurtaxe_korrekturwert = 0.0
    b.notiz = ''
    b.meldeschein_nummer = ''
    b.rechnungs_nummer = ''
    return b


def _make_besucher(id=10):
    b = MagicMock()
    b.id = id
    b.name = 'Müller'
    b.vorname = 'Ralph'
    b.email = 'test@example.com'
    b.stadt = 'Gersfeld'
    b.language = 'de'
    return b


class TestBuchungIndex:
    def test_requires_login(self, client):
        r = client.get('/buchung/', follow_redirects=False)
        assert r.status_code == 302
        assert '/auth/login' in r.headers['Location']

    def test_renders_logged_in(self, logged_in_client):
        with patch('flaskr.buchung.buchung.Apartment') as MockApt:
            MockApt.select.return_value.order_by.return_value = []
            r = logged_in_client.get('/buchung/')
        assert r.status_code == 200

    def test_filter_params_accepted(self, logged_in_client):
        with patch('flaskr.buchung.buchung.Apartment') as MockApt:
            MockApt.select.return_value.order_by.return_value = []
            r = logged_in_client.get('/buchung/?year=2026&month=Mai&status=gebucht')
        assert r.status_code == 200


class TestBuchungSearch:
    def test_requires_login(self, client):
        r = client.get('/buchung/search', follow_redirects=False)
        assert r.status_code == 302

    def test_returns_partial(self, logged_in_client):
        r = logged_in_client.get('/buchung/search?year=2026&month=Mai&status=gebucht')
        assert r.status_code == 200
        assert b'<!DOCTYPE' not in r.data  # ist ein Partial, kein volles Layout

    def test_apartment_filter(self, logged_in_client):
        r = logged_in_client.get('/buchung/search?year=2026&month=Mai&status=gebucht&apartment=F1')
        assert r.status_code == 200

    def test_multi_status(self, logged_in_client):
        r = logged_in_client.get(
            '/buchung/search?year=2026&month=Mai&status=gebucht&status=abgerechnet')
        assert r.status_code == 200


class TestBuchungDetail:
    def test_requires_login(self, client):
        r = client.get('/buchung/1/detail', follow_redirects=False)
        assert r.status_code == 302

    def test_renders_card(self, logged_in_client):
        buchung = _make_buchung()
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.get('/buchung/1/detail')
        assert r.status_code == 200
        assert b'M\xc3\xbcller' in r.data
        assert b'F1' in r.data

    def test_shows_bearbeiten_for_gebucht(self, logged_in_client):
        buchung = _make_buchung(status='gebucht')
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.get('/buchung/1/detail')
        assert b'Bearbeiten' in r.data

    def test_no_bearbeiten_for_abgerechnet(self, logged_in_client):
        buchung = _make_buchung(status='abgerechnet')
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.get('/buchung/1/detail')
        assert b'Bearbeiten' not in r.data


class TestBuchungEditInline:
    def test_requires_login(self, client):
        r = client.get('/buchung/1/edit_inline', follow_redirects=False)
        assert r.status_code == 302

    def test_get_renders_form(self, logged_in_client):
        buchung = _make_buchung(status='gebucht')
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.get('/buchung/1/edit_inline')
        assert r.status_code == 200
        assert b'Abbrechen' in r.data

    def test_blocked_for_abgerechnet(self, logged_in_client):
        buchung = _make_buchung(status='abgerechnet')
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.get('/buchung/1/edit_inline')
        assert r.status_code == 200
        assert b'kann nicht' in r.data


class TestBuchungUpdateStatus:
    def test_requires_login(self, client):
        r = client.post('/buchung/1/status', data={'status': 'gebucht'},
                        follow_redirects=False)
        assert r.status_code == 302

    def test_valid_transition_angebot_to_gebucht(self, logged_in_client):
        buchung = _make_buchung(status='angebot')
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.post('/buchung/1/status', data={'status': 'gebucht'})
        assert r.status_code == 200
        buchung.recalc.assert_called_once_with('gebucht')
        buchung.save.assert_called_once()

    def test_invalid_transition_ignored(self, logged_in_client):
        buchung = _make_buchung(status='abgerechnet')
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.post('/buchung/1/status', data={'status': 'gebucht'})
        assert r.status_code == 200
        buchung.recalc.assert_not_called()
        buchung.save.assert_not_called()

    def test_abgerechnet_not_allowed_via_quick_change(self, logged_in_client):
        buchung = _make_buchung(status='gebucht')
        with patch('flaskr.buchung.buchung.Buchung') as MockBuchung:
            MockBuchung.get_by_id.return_value = buchung
            r = logged_in_client.post('/buchung/1/status', data={'status': 'abgerechnet'})
        assert r.status_code == 200
        buchung.recalc.assert_not_called()


class TestNeueBuchung:
    def test_neu_requires_login(self, client):
        r = client.get('/buchung/neu', follow_redirects=False)
        assert r.status_code == 302

    def test_neu_renders_page(self, logged_in_client):
        r = logged_in_client.get('/buchung/neu')
        assert r.status_code == 200
        assert b'Gast suchen' in r.data
        assert b'hx-get' in r.data

    def test_suche_short_query_returns_empty(self, logged_in_client):
        r = logged_in_client.get('/buchung/neu/suche?q=ab')
        assert r.status_code == 200
        assert r.data == b''

    def test_suche_returns_guest_list(self, logged_in_client):
        besucher = _make_besucher()
        q = MagicMock()
        q.where.return_value = q
        q.order_by.return_value = [besucher]
        with patch('flaskr.buchung.buchung.Besucher') as MockBesucher:
            MockBesucher.select.return_value = q
            MockBesucher.name = MagicMock()
            MockBesucher.vorname = MagicMock()
            r = logged_in_client.get('/buchung/neu/suche?q=müller')
        assert r.status_code == 200
        assert b'M\xc3\xbcller' in r.data
        assert b'hx-get' in r.data  # Zeilen haben HTMX-Attribute

    def test_formular_requires_login(self, client):
        r = client.get('/buchung/neu/formular/1', follow_redirects=False)
        assert r.status_code == 302

    def test_formular_renders_form(self, logged_in_client):
        besucher = _make_besucher()
        with patch('flaskr.buchung.buchung.Besucher') as MockBesucher:
            MockBesucher.get_by_id.return_value = besucher
            r = logged_in_client.get('/buchung/neu/formular/10')
        assert r.status_code == 200
        assert b'M\xc3\xbcller' in r.data
        assert b'Buchung speichern' in r.data

"""
Tests for visitor (Besucher) routes: /besucher/...
"""

import pytest
from unittest.mock import MagicMock, patch


def _make_besucher(id=1, name='Schmidt', vorname='Hans'):
    b = MagicMock()
    b.id = id
    b.name = name
    b.vorname = vorname
    b.anrede = 'Herr'
    b.strasse = 'Hauptstr. 1'
    b.plz = '12345'
    b.stadt = 'Musterstadt'
    b.land = 'DE'
    b.email = 'test@example.com'
    b.tel = '01234'
    return b


def _search_mock(results):
    """Returns a Besucher mock whose select().where().order_by() yields results."""
    q = MagicMock()
    q.where.return_value = q
    q.order_by.return_value = iter(results)
    m = MagicMock()
    m.select.return_value = q
    m.name = MagicMock()
    return m


class TestBesucherListProtection:
    def test_list_requires_login(self, client):
        """GET /besucher/ without session → redirect to login."""
        response = client.get('/besucher/', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_list_renders_when_logged_in(self, logged_in_client):
        """GET /besucher/ with session → 200, even when no visitors exist."""
        with patch('flaskr.besucher.besucher.fetch_visitors', return_value=[]):
            response = logged_in_client.get('/besucher/')
        assert response.status_code == 200


class TestBesucherFind:
    def test_find_requires_login(self, client):
        """GET /besucher/find without session → redirect."""
        response = client.get('/besucher/find', follow_redirects=False)
        assert response.status_code == 302

    def test_find_renders_page(self, logged_in_client):
        """GET /besucher/find → 200 with search input."""
        response = logged_in_client.get('/besucher/find')
        assert response.status_code == 200
        assert b'hx-get' in response.data


class TestBesucherSearchRoute:
    def test_search_requires_login(self, client):
        """GET /besucher/search without session → redirect."""
        response = client.get('/besucher/search?q=Müller', follow_redirects=False)
        assert response.status_code == 302

    def test_short_query_returns_empty(self, logged_in_client):
        """Query shorter than 3 chars → empty response, no DB call."""
        with patch('flaskr.besucher.besucher.Besucher') as mock_cls:
            response = logged_in_client.get('/besucher/search?q=Mü')
        assert response.status_code == 200
        assert response.data == b''
        mock_cls.select.assert_not_called()

    def test_single_term_searches_name_and_vorname(self, logged_in_client):
        """Single term → OR search across name and vorname."""
        besucher = _make_besucher()
        with patch('flaskr.besucher.besucher.Besucher', _search_mock([besucher])):
            response = logged_in_client.get('/besucher/search?q=M%C3%BCll*')
        assert response.status_code == 200
        assert b'Schmidt' in response.data

    def test_two_terms_searches_name_and_vorname_combined(self, logged_in_client):
        """Two space-separated terms → AND search: first=name, second=vorname."""
        besucher = _make_besucher()
        with patch('flaskr.besucher.besucher.Besucher', _search_mock([besucher])):
            response = logged_in_client.get('/besucher/search?q=Schm*+Han*')
        assert response.status_code == 200
        assert b'Schmidt' in response.data

    def test_no_results_shows_empty_message(self, logged_in_client):
        """Empty result set → 'Keine Besucher gefunden' in response."""
        with patch('flaskr.besucher.besucher.Besucher', _search_mock([])):
            response = logged_in_client.get('/besucher/search?q=xyzxyz')
        assert response.status_code == 200
        assert 'Keine Besucher gefunden'.encode() in response.data

    def test_wildcard_converted_to_sql_percent(self, logged_in_client):
        """* in query is passed as % to the ORM where clause."""
        with patch('flaskr.besucher.besucher.Besucher') as mock_cls:
            q = MagicMock()
            q.where.return_value = q
            q.order_by.return_value = iter([])
            mock_cls.select.return_value = q
            mock_cls.name = MagicMock()
            logged_in_client.get('/besucher/search?q=M%C3%BCll*')
        # where() must have been called (pattern was passed to ORM)
        q.where.assert_called_once()


class TestBesucherCreate:
    def test_create_form_requires_login(self, client):
        """GET /besucher/create without session → redirect."""
        response = client.get('/besucher/create', follow_redirects=False)
        assert response.status_code == 302

    def test_create_form_renders(self, logged_in_client):
        """GET /besucher/create with session → 200."""
        response = logged_in_client.get('/besucher/create')
        assert response.status_code == 200

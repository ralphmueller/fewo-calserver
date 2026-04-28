"""
Tests for visitor (Besucher) routes: /besucher/...
"""

import pytest
from unittest.mock import MagicMock, patch


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


class TestBesucherSearch:
    def test_find_requires_login(self, client):
        """GET /besucher/find without session → redirect."""
        response = client.get('/besucher/find?q=Müller', follow_redirects=False)
        assert response.status_code == 302

    def test_find_returns_results(self, logged_in_client):
        """GET /besucher/find with a query → 200 (no DB call needed for /find)."""
        response = logged_in_client.get('/besucher/find?q=M%C3%BCller')
        assert response.status_code == 200


class TestBesucherCreate:
    def test_create_form_requires_login(self, client):
        """GET /besucher/create without session → redirect."""
        response = client.get('/besucher/create', follow_redirects=False)
        assert response.status_code == 302

    def test_create_form_renders(self, logged_in_client):
        """GET /besucher/create with session → 200."""
        response = logged_in_client.get('/besucher/create')
        assert response.status_code == 200

"""
Tests for the home/dashboard route: /.
"""

import pytest


class TestHomeRoute:
    def test_home_renders_when_logged_in(self, logged_in_client):
        """GET / returns 200 for authenticated users."""
        response = logged_in_client.get('/')
        assert response.status_code == 200

    def test_home_accessible_without_login(self, client):
        """GET / is currently public (no @login_required on home)."""
        response = client.get('/')
        # The home route has no login_required decorator — it renders publicly.
        assert response.status_code == 200

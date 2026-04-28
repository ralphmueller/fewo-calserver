"""
Tests for authentication routes: /auth/login, /auth/logout, /auth/profile.
"""

import pytest
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash
from peewee import DoesNotExist


class TestLoginPage:
    def test_login_page_renders(self, client):
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Anmelden' in response.data or b'login' in response.data.lower()

    def test_login_wrong_username_redirects_back(self, client, app):
        """Unknown username → flash error, redirect to /auth/login."""
        with patch('flaskr.auth.auth.User') as mock_user_cls:
            mock_user_cls.get.side_effect = DoesNotExist()
            response = client.post('/auth/login', data={
                'user': 'nobody',
                'password': 'whatever',
            }, follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_login_wrong_password_redirects_back(self, client, mock_user):
        """Correct username but wrong password → redirect to /auth/login."""
        with patch('flaskr.auth.auth.User') as mock_user_cls:
            mock_user_cls.get.return_value = mock_user
            response = client.post('/auth/login', data={
                'user': 'testuser',
                'password': 'wrongpassword',
            }, follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_login_correct_credentials_redirects_home(self, client, mock_user):
        """Correct credentials → redirect to home."""
        with patch('flaskr.auth.auth.User') as mock_user_cls:
            mock_user_cls.get.return_value = mock_user
            response = client.post('/auth/login', data={
                'user': 'testuser',
                'password': 'correctpassword',
            }, follow_redirects=False)
        assert response.status_code == 302
        assert '/' in response.headers['Location']

    def test_login_grants_access_to_protected_routes(self, client, mock_user):
        """After login, protected routes are accessible (session is active)."""
        with patch('flaskr.auth.auth.User') as mock_user_cls:
            mock_user_cls.get.return_value = mock_user
            client.post('/auth/login', data={
                'user': 'testuser',
                'password': 'correctpassword',
            })
        # /auth/profile requires login; accessible only with valid session
        with patch('flaskr.auth.auth.User') as mock_user_cls:
            mock_user_cls.get.return_value = mock_user
            response = client.get('/auth/profile')
        assert response.status_code == 200


class TestLogout:
    def test_logout_redirects(self, client, mock_user):
        """Logout redirects to home."""
        with patch('flaskr.auth.auth.User') as mock_user_cls:
            mock_user_cls.get.return_value = mock_user
            client.post('/auth/login', data={
                'user': 'testuser',
                'password': 'correctpassword',
            })
        response = client.get('/auth/logout', follow_redirects=False)
        assert response.status_code == 302

    def test_logout_revokes_access(self, client, mock_user):
        """After logout, protected routes redirect to login."""
        with patch('flaskr.auth.auth.User') as mock_user_cls:
            mock_user_cls.get.return_value = mock_user
            client.post('/auth/login', data={
                'user': 'testuser',
                'password': 'correctpassword',
            })
        client.get('/auth/logout')
        response = client.get('/auth/profile', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']


class TestProtectedRoutes:
    def test_profile_requires_login(self, client):
        """GET /auth/profile without login → redirect to /auth/login."""
        response = client.get('/auth/profile', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_profile_accessible_when_logged_in(self, logged_in_client):
        """GET /auth/profile with valid session → 200."""
        response = logged_in_client.get('/auth/profile')
        assert response.status_code == 200

    def test_register_requires_login(self, client):
        """GET /auth/register without login → redirect to /auth/login."""
        response = client.get('/auth/register', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

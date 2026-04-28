"""
Pytest configuration and shared fixtures.

bkormlib and rmemaillib are external packages not available in test
environment. They must be patched in sys.modules before flaskr is imported,
because buchung_forms.py calls Apartment.choices() and
StaticValuesBuchung.mwstsatz() at class-definition time.
"""

import os
import sys
import json
from unittest.mock import MagicMock, patch
import pytest

# ── 0. Werkzeug compatibility shim ──────────────────────────────────────────
# Flask 2.3.1 references werkzeug.__version__ in its test client, but
# Werkzeug 3.x removed that attribute. Inject it before Flask is imported.
import werkzeug as _werkzeug
if not hasattr(_werkzeug, '__version__'):
    import importlib.metadata as _im
    _werkzeug.__version__ = _im.version('werkzeug')

# ── 1. Environment variables (must be set before config.py is imported) ──────

os.environ.setdefault('ENV', 'development')
os.environ.setdefault('DEVELOPMENT_DATABASE', 'mysql://test:test@localhost/fewo_test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('EMAIL_ADDRESS', 'test@example.com')
os.environ.setdefault('EMAIL_USER', 'testuser')
os.environ.setdefault('EMAIL_PASSWORD', 'testpassword')
os.environ.setdefault('EMAIL_HOST', 'localhost')

# ── 2. Mock external packages in sys.modules ─────────────────────────────────

# systemd.journal is only available on Linux with systemd
sys.modules.setdefault('systemd', MagicMock())
sys.modules.setdefault('systemd.journal', MagicMock())

# rmemaillib: internal email library
_mock_rmemaillib = MagicMock()
sys.modules.setdefault('rmemaillib', _mock_rmemaillib)
sys.modules.setdefault('rmemaillib.email', _mock_rmemaillib.email)

# bkormlib: internal ORM library — must define all used names explicitly
_mock_db = MagicMock()
_mock_db.connection.return_value.ping.return_value = None

_mock_apartment_query = MagicMock()
_mock_apartment_query.order_by.return_value = []  # iterable, no further chaining needed
_mock_apartment_query.__iter__ = MagicMock(return_value=iter([]))

_mock_apartment_cls = MagicMock()
_mock_apartment_cls.choices.return_value = [(1, 'Apartment A'), (2, 'Apartment B')]
_mock_apartment_cls.select.return_value = _mock_apartment_query
_mock_apartment_cls.get.return_value = MagicMock(id=1, name='Apartment A', active=True)
_mock_apartment_cls.name = MagicMock()  # used in Apartment.select().order_by(Apartment.name)

_mock_portal_cls = MagicMock()
_mock_portal_cls.choices.return_value = [(1, 'Direkt'), (2, 'Airbnb')]

_mock_static_values = MagicMock()
_mock_static_values.mwstsatz.return_value = 7.0
_mock_static_values.ktsatz_vz.return_value = 2.10
_mock_static_values.ktsatz_hz.return_value = 0.50

_mock_buchung_query = MagicMock()
_mock_buchung_query.join.return_value = _mock_buchung_query
_mock_buchung_query.switch.return_value = _mock_buchung_query
_mock_buchung_query.where.return_value = _mock_buchung_query
_mock_buchung_query.order_by.return_value = _mock_buchung_query
_mock_buchung_query.__iter__ = MagicMock(return_value=iter([]))
_mock_buchung_query.__len__ = MagicMock(return_value=0)

_mock_db_cursor = MagicMock()
_mock_db_cursor.fetchall.return_value = [(2023, 45, '18000.00', '900.00')]

_mock_buchung_meta_db = MagicMock()
_mock_buchung_meta_db.execute_sql.return_value = _mock_db_cursor

_mock_buchung_cls = MagicMock()
_mock_buchung_cls.select.return_value = _mock_buchung_query
_mock_buchung_cls.status = MagicMock()
_mock_buchung_cls.anreise = MagicMock()
_mock_buchung_cls.abreise = MagicMock()
_mock_buchung_cls._meta.database = _mock_buchung_meta_db

_mock_besucher_cls = MagicMock()
_mock_besucher_cls.select.return_value = _mock_buchung_query  # reuse chainable mock

_mock_user_cls = MagicMock()

_mock_bkormlib = MagicMock()
_mock_bkormlib.schema.db_connect.return_value = _mock_db
_mock_bkormlib.schema.Apartment = _mock_apartment_cls
_mock_bkormlib.schema.Portal = _mock_portal_cls
_mock_bkormlib.schema.Buchung = _mock_buchung_cls
_mock_bkormlib.schema.Besucher = _mock_besucher_cls
_mock_bkormlib.schema.User = _mock_user_cls
_mock_bkormlib.schema.StaticValuesBuchung = _mock_static_values
_mock_bkormlib.Apartment = _mock_apartment_cls
_mock_bkormlib.Portal = _mock_portal_cls
_mock_bkormlib.Buchung = _mock_buchung_cls
_mock_bkormlib.Besucher = _mock_besucher_cls
_mock_bkormlib.User = _mock_user_cls
_mock_bkormlib.StaticValuesBuchung = _mock_static_values
_mock_bkormlib.FlaskrSession = MagicMock()
_mock_bkormlib.DoesNotExist = Exception  # used in except clauses

sys.modules.setdefault('bkormlib', _mock_bkormlib)
sys.modules.setdefault('bkormlib.schema', _mock_bkormlib.schema)

# ── 3. Import flaskr (now uses mocked external packages) ─────────────────────

from flaskr import create_app  # noqa: E402


# ── 4. Fixtures ───────────────────────────────────────────────────────────────

TEST_CONFIG = {
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'WTF_CSRF_FIELD_NAME': 'csrf_token',
    'SECRET_KEY': 'test-secret-key',
    'ENV': 'development',
    'DB': _mock_db,
    'MAILER': MagicMock(),
    'EMAILS_TEAM': ['test@example.com'],
    'INFO_EMAIL': ['test@example.com'],
    'HOST': 'localhost',
    'IP_ADDRESS': '127.0.0.1',
    'ASSETS_DEBUG': True,
    'ASSETS_AUTO_BUILD': False,
}


@pytest.fixture(scope='session')
def app():
    application = create_app(TEST_CONFIG)
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_user():
    """A mock User object with a hashed password."""
    from werkzeug.security import generate_password_hash
    user = MagicMock()
    user.id = 1
    user.username = 'testuser'
    user.password = generate_password_hash('correctpassword')
    return user


@pytest.fixture
def logged_in_client(app, mock_user):
    """Test client with a real authenticated session via the login route.

    Uses the login form instead of session_transaction() to avoid
    Flask 2.3.1 / Werkzeug 3.x incompatibility in _update_cookies_from_response.
    """
    from unittest.mock import patch as _patch
    client = app.test_client()
    _mock_user_cls.get.return_value = mock_user
    with _patch('flaskr.auth.auth.User') as patched:
        patched.get.return_value = mock_user
        client.post('/auth/login', data={
            'user': mock_user.username,
            'password': 'correctpassword',
        })
    return client

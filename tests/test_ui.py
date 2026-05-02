"""
Playwright UI-Tests für fewo-calserver.

Startet einen echten Flask-HTTP-Server in einem Thread und steuert
Chromium headless über pytest-playwright. Alle DB-Zugriffe laufen
gegen die bereits in conftest.py konfigurierten Mocks.
"""
import sys
import threading
import pytest
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

BASE_URL = 'http://127.0.0.1:5099'
VALID_PASSWORD = 'test-ui-password'


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def ui_user():
    """Mock-User mit echtem Passwort-Hash für Login-Tests."""
    user = type('UIUser', (), {
        'id': 42,
        'username': 'ui_tester',
        'password': generate_password_hash(VALID_PASSWORD),
    })()
    mock_cls = sys.modules['bkormlib'].User
    original = mock_cls.get.return_value
    mock_cls.get.return_value = user
    yield user
    mock_cls.get.return_value = original


@pytest.fixture(scope='module')
def live_server(app):
    """Flask-App in Hintergrund-Thread (Port 5099)."""
    server = make_server('127.0.0.1', 5099, app)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    yield BASE_URL
    server.shutdown()


# ── Hilfs-Funktion ────────────────────────────────────────────────────────────

def do_login(page, base_url, password=VALID_PASSWORD):
    page.goto(f'{base_url}/auth/login')
    page.locator('input[name="user"]').fill('ui_tester')
    page.locator('input[name="password"]').fill(password)
    page.locator('input[type="submit"]').click()


# ── Tests: Login-Seite ────────────────────────────────────────────────────────

class TestLoginPageUI:

    def test_login_page_renders_form(self, page, live_server):
        page.goto(f'{live_server}/auth/login')
        assert page.locator('input[name="user"]').is_visible()
        assert page.locator('input[name="password"]').is_visible()
        assert page.locator('input[type="submit"]').is_visible()

    def test_login_page_title(self, page, live_server):
        page.goto(f'{live_server}/auth/login')
        assert 'FewoApp' in page.title()

    def test_login_with_wrong_password_stays_on_login(self, page, live_server, ui_user):
        # ui_user aktiviert den korrekten Mock; falsches PW schlägt fehl
        do_login(page, live_server, password='falsch')
        assert '/auth/login' in page.url

    def test_login_with_wrong_password_shows_error_flash(self, page, live_server, ui_user):
        do_login(page, live_server, password='falsch')
        flash = page.locator('li.error.flash')
        assert flash.count() > 0
        assert 'nicht korrekt' in flash.first.text_content()

    def test_successful_login_redirects_to_home(self, page, live_server, ui_user):
        do_login(page, live_server)
        assert page.url == f'{live_server}/'

    def test_nav_shows_username_after_login(self, page, live_server, ui_user):
        do_login(page, live_server)
        assert page.locator(f'text=ui_tester').is_visible()

    def test_nav_hides_anmelden_link_after_login(self, page, live_server, ui_user):
        do_login(page, live_server)
        assert page.locator('a:has-text("Anmelden")').count() == 0


# ── Tests: Unauthentifizierter Zugriff ───────────────────────────────────────

class TestProtectedRoutesUI:

    def test_besucher_liste_redirects_to_login(self, page, live_server):
        page.goto(f'{live_server}/besucher/')
        assert '/auth/login' in page.url

    def test_calendar_redirects_to_login(self, page, live_server):
        page.goto(f'{live_server}/calendar/month')
        assert '/auth/login' in page.url

    def test_login_link_visible_when_logged_out(self, page, live_server):
        page.goto(f'{live_server}/')
        assert page.locator('a:has-text("Anmelden")').is_visible()


# ── Tests: Navigation nach Login ─────────────────────────────────────────────

class TestNavigationUI:

    def test_nav_shows_besucher_dropdown(self, page, live_server, ui_user):
        do_login(page, live_server)
        assert page.locator('a.nav-link.dropdown-toggle:has-text("Besucher")').is_visible()

    def test_nav_shows_buchungen_dropdown(self, page, live_server, ui_user):
        do_login(page, live_server)
        assert page.locator('a.nav-link.dropdown-toggle:has-text("Buchungen")').is_visible()

    def test_nav_shows_kalender_link(self, page, live_server, ui_user):
        do_login(page, live_server)
        assert page.locator('a:has-text("Kalender")').is_visible()

    def test_besucher_dropdown_contains_links(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.locator('a.nav-link.dropdown-toggle:has-text("Besucher")').click()
        assert page.locator('a.dropdown-item[href="/besucher/"]').is_visible()
        assert page.locator('a.dropdown-item[href="/besucher/create"]').is_visible()
        assert page.locator('a.dropdown-item[href="/besucher/find"]').is_visible()

    def test_brand_link_leads_to_home(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/auth/profile')
        page.locator('a.navbar-brand').click()
        assert page.url == f'{live_server}/'


# ── Tests: Logout ─────────────────────────────────────────────────────────────

class TestLogoutUI:

    def test_logout_redirects_to_home(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/auth/logout')
        assert page.url == f'{live_server}/'

    def test_logout_shows_anmelden_again(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/auth/logout')
        assert page.locator('a:has-text("Anmelden")').is_visible()

    def test_after_logout_besucher_list_requires_login(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/auth/logout')
        page.goto(f'{live_server}/besucher/')
        assert '/auth/login' in page.url


# ── Tests: Besucher Suche ────────────────────────────────────────────────────

class TestBesucherFindUI:

    def test_find_page_shows_search_input(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/besucher/find')
        assert page.locator('input[name="q"]').is_visible()

    def test_find_page_shows_help_text(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/besucher/find')
        assert page.locator('text=Mindestens 3 Zeichen').is_visible()

    def test_find_page_user_can_type_in_search(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/besucher/find')
        page.locator('input[name="q"]').fill('Schmidt')
        assert page.locator('input[name="q"]').input_value() == 'Schmidt'


# ── Tests: Besucher anlegen (Formularfelder) ──────────────────────────────────

class TestBesucherCreateUI:

    def test_create_form_shows_name_field(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/besucher/create')
        assert page.locator('input[name="name"]').is_visible()

    def test_create_form_shows_email_field(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/besucher/create')
        assert page.locator('input[name="email"]').is_visible()

    def test_create_form_shows_submit_button(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/besucher/create')
        assert page.locator('input[type="submit"][value="Speichern"]').is_visible()

    def test_user_can_fill_create_form(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/besucher/create')
        page.locator('input[name="vorname"]').fill('Maria')
        page.locator('input[name="name"]').fill('Mustermann')
        page.locator('input[name="email"]').fill('maria@example.com')
        assert page.locator('input[name="vorname"]').input_value() == 'Maria'
        assert page.locator('input[name="name"]').input_value() == 'Mustermann'


# ── Tests: Passwort ändern ────────────────────────────────────────────────────

class TestChangePasswordUI:

    def test_change_password_form_renders(self, page, live_server, ui_user):
        do_login(page, live_server)
        page.goto(f'{live_server}/auth/profile')
        assert page.locator('input[name="new_password"]').is_visible()
        assert page.locator('input[name="confirm"]').is_visible()
        assert page.locator('input[type="submit"][value="Ändern"]').is_visible()

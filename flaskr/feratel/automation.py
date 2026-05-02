"""
Feratel Deskline Gästemeldung Automation

Öffnet einen echten Chromium-Browser (headless), loggt sich ins Feratel
WebClient4 ein und füllt einen Meldeschein für eine Buchung aus.

Aufruf:
    from flaskr.feratel.automation import submit_meldeschein
    result = submit_meldeschein(buchung_id)

Rückgabe:
    {'success': True, 'meldeschein_nr': '...'}  oder
    {'success': False, 'error': '...'}
"""

import os
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)


def _is_mock() -> bool:
    return os.environ.get('FERATEL_MOCK', '').lower() in ('true', '1', 'yes')


def _submit_meldeschein_mock(buchung_id: int) -> dict:
    """Simuliert die Feratel-Meldung ohne echten Browser."""
    from bkormlib import Buchung
    try:
        b = Buchung.get_by_id(buchung_id)
        besucher = b.besucher
        fake_nr = f"MOCK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        log.info(
            '[MOCK] Würde Meldeschein anlegen: %s %s, %s–%s, %s, %d Pers. → Nr. %s',
            besucher.name, besucher.vorname,
            b.anreise, b.abreise,
            b.apartment.name,
            int(b.kurtaxe_vz or 1),
            fake_nr,
        )
        return {'success': True, 'meldeschein_nr': fake_nr}
    except Exception as e:
        return {'success': False, 'error': str(e)}

import json

BASE_URL = 'https://webclient4.deskline.net/RHO/de'
LOGIN_URL = f'{BASE_URL}/login'
ACCOMMODATION_ID = os.environ.get('FERATEL_ACCOMMODATION_ID', '')

_apartment_map_raw = os.environ.get('FERATEL_APARTMENT_MAP', '{}')
try:
    APARTMENT_MAP = json.loads(_apartment_map_raw)
except json.JSONDecodeError:
    APARTMENT_MAP = {}


def _fmt_date(d) -> str:
    if isinstance(d, str):
        from datetime import datetime
        d = datetime.strptime(d, '%Y-%m-%d').date()
    return d.strftime('%d.%m.%Y')


class FeratelSession:

    def __init__(self, headless: bool = True):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        self._page = self._browser.new_page()

    def close(self):
        self._browser.close()
        self._pw.stop()

    # ── Login ──────────────────────────────────────────────────────────────

    def login(self):
        page = self._page
        page.goto(LOGIN_URL, wait_until='domcontentloaded', timeout=60_000)
        page.wait_for_timeout(3_000)
        page.locator('#Username').click()
        page.keyboard.type(os.environ['FERATEL_ID'], delay=80)
        page.locator('#Password').click()
        page.keyboard.type(os.environ['FERATEL_PW'], delay=80)
        page.keyboard.press('Enter')
        page.wait_for_timeout(7_000)
        if 'identity.deskline.net' in page.url:
            raise RuntimeError('Feratel Login fehlgeschlagen — Credentials prüfen')
        log.info('Feratel Login erfolgreich')

    # ── Navigation ─────────────────────────────────────────────────────────

    def goto_guestregistration(self):
        url = f'{BASE_URL}/visitorregistrationforms/guestregistration/{ACCOMMODATION_ID}'
        self._page.goto(url, wait_until='domcontentloaded', timeout=60_000)
        self._page.wait_for_timeout(5_000)

    def select_apartment(self, apartment_name: str):
        feratel_name = APARTMENT_MAP.get(apartment_name)
        if not feratel_name:
            log.warning('Apartment "%s" nicht im APARTMENT_MAP — benutze Standard', apartment_name)
            return
        page = self._page
        # Der erste sichtbare dropdown-toggle ist der Apartment-Selector
        toggle = page.locator('button.dropdown-toggle').nth(0)
        current = toggle.inner_text().strip()
        if feratel_name in current:
            log.info('Apartment bereits ausgewählt: %s', feratel_name)
            return
        toggle.click()
        page.wait_for_timeout(800)
        # Optionen sind einfache <a>-Tags im geöffneten Dropdown
        page.locator(f'a:has-text("{feratel_name}")').first.click()
        page.wait_for_timeout(2_000)
        log.info('Apartment gewählt: %s', feratel_name)

    # ── Meldeschein Modal öffnen ───────────────────────────────────────────

    def open_new_meldeschein(self):
        page = self._page
        btns = page.locator('button:has-text("Neuer Meldeschein")')
        for i in range(btns.count()):
            if btns.nth(i).is_visible():
                btns.nth(i).click()
                break
        page.wait_for_selector('a[ng-click*="Standard"][ng-click*="Individual"]:visible', timeout=5_000)
        links = page.locator('a[ng-click*="Standard"][ng-click*="Individual"]')
        for i in range(links.count()):
            if links.nth(i).is_visible():
                links.nth(i).click()
                break
        page.wait_for_selector('.modal-content', timeout=8_000)
        page.wait_for_timeout(2_000)
        log.info('Meldeschein Modal geöffnet')

    # ── Datum setzen ──────────────────────────────────────────────────────

    def set_dates(self, anreise, abreise):
        page = self._page
        arr = _fmt_date(anreise)
        dep = _fmt_date(abreise)
        for field_id, value in [
            ('#mainGuestArrival', arr),
            ('#mainGuestPlannedDeparture', dep),
            ('#mainGuestDeparture', dep),
        ]:
            f = page.locator(field_id)
            f.fill('')
            f.type(value, delay=60)
            page.keyboard.press('Tab')
            page.wait_for_timeout(300)

    # ── Gast suchen und auswählen ─────────────────────────────────────────

    def _open_search_modal(self, is_main: bool, slot_index: int = 0):
        page = self._page
        if is_main:
            page.locator('button[ng-click="openSearchMyGuestsModal(true)"]').click()
        else:
            page.locator('button[ng-click="openSearchMyGuestsModal(false, $index)"]').nth(slot_index).click()
        page.wait_for_timeout(2_000)

    def search_and_select(self, surname: str, firstname: str = '') -> bool:
        """Sucht im offenen Such-Modal; gibt True zurück wenn Gast ausgewählt."""
        page = self._page
        page.locator('input[ng-model="filterData.Search.LastName"]').fill(surname)
        if firstname:
            page.locator('input[ng-model="filterData.Search.FirstName"]').fill(firstname)
        page.locator('button[ng-click="searchGuests(1)"]').click()
        page.wait_for_timeout(2_000)

        rows = page.locator('input[ng-model="guest.Checked"]')
        visible = [i for i in range(rows.count()) if rows.nth(i).is_visible()]
        if not visible:
            log.info('"%s %s" nicht in Feratel gefunden', firstname, surname)
            page.locator('button[ng-click="closeSearchMyGuestsModal()"]').last.click()
            page.wait_for_timeout(1_000)
            return False

        rows.nth(visible[0]).check()
        page.locator('button[ng-click="selectAddressesIntoForm()"]').click()
        page.wait_for_timeout(1_500)
        log.info('"%s %s" aus Feratel-Adressen übernommen', firstname, surname)
        return True

    # ── Hauptgast manuell füllen ──────────────────────────────────────────

    def fill_main_guest_manually(self, besucher):
        page = self._page
        for field_id, value in [
            ('#mainGuestSurname',    besucher.name),
            ('#mainGuestFirstName',  besucher.vorname),
            ('#mainGuestZipCode',    besucher.plz),
            ('#mainGuestCity',       besucher.stadt),
            ('#mainGuestStreet',     besucher.strasse),
        ]:
            if value:
                page.locator(field_id).fill(str(value))

    # ── Weitere Gäste hinzufügen ──────────────────────────────────────────

    def add_extra_guests(self, surname: str, anzahl_gaeste: int):
        """
        Füllt die Slots für Gast 2…N.
        - Slot für Gast 2 ist bereits im Modal vorhanden
        - Ab Gast 3 muss "+ Gast hinzufügen" geklickt werden
        - Pro Slot: Suche nach Nachname → auswählen falls gefunden, sonst leer lassen
        """
        page = self._page
        extra = anzahl_gaeste - 1  # Anzahl zusätzlicher Gäste (Gast 2, 3, ...)
        if extra <= 0:
            return

        for i in range(extra):
            # Ab Gast 3: neuen Slot hinzufügen
            if i >= 1:
                add_btn = page.locator('button:has-text("Gast hinzufügen")')
                if add_btn.is_visible():
                    add_btn.click()
                    page.wait_for_timeout(1_500)

            # Suchbutton für diesen Slot (0-basierter Index)
            search_btns = page.locator('button[ng-click="openSearchMyGuestsModal(false, $index)"]')
            visible_search = [j for j in range(search_btns.count()) if search_btns.nth(j).is_visible()]
            if not visible_search:
                log.warning('Kein Suchbutton für Gast %d gefunden', i + 2)
                continue

            search_btns.nth(visible_search[i] if i < len(visible_search) else visible_search[-1]).click()
            page.wait_for_timeout(2_000)
            found = self.search_and_select(surname)
            if not found:
                log.info('Gast %d (%s) nicht gefunden — Slot bleibt leer', i + 2, surname)

    # ── Speichern und Meldeschein-Nummer auslesen ─────────────────────────

    def save_and_close(self) -> str | None:
        page = self._page
        page.locator('button[ng-click="saveForm(SaveActions.None)"]').first.click()
        page.wait_for_timeout(5_000)

        # Meldeschein-Nummer aus Header/Modal lesen
        for selector in [
            '[ng-bind*="FormNumber"]',
            '[ng-bind*="formNumber"]',
            '[ng-bind*="SheetNumber"]',
            '.sheet-number',
            'span:has-text("Nr.")',
        ]:
            el = page.locator(selector)
            if el.count() > 0 and el.first.is_visible():
                text = el.first.inner_text().strip()
                if text:
                    return text
        return None


# ── Öffentliche API ────────────────────────────────────────────────────────────

def submit_meldeschein(buchung_id: int, headless: bool = True) -> dict:
    """
    Legt einen Feratel-Meldeschein für die angegebene Buchung an
    und gibt die Meldeschein-Nummer zurück.

    Wenn FERATEL_MOCK=true gesetzt ist, wird kein echter Browser gestartet
    und stattdessen eine simulierte Antwort zurückgegeben.
    """
    if _is_mock():
        return _submit_meldeschein_mock(buchung_id)

    from bkormlib import Buchung

    try:
        buchung = Buchung.get_by_id(buchung_id)
        besucher = buchung.besucher
        apartment_name = buchung.apartment.name
        anzahl_vz = int(buchung.kurtaxe_vz or 1)
    except Exception as e:
        return {'success': False, 'error': f'Buchung nicht gefunden: {e}'}

    session = FeratelSession(headless=headless)
    try:
        session.login()
        session.goto_guestregistration()
        session.select_apartment(apartment_name)
        session.open_new_meldeschein()
        session.set_dates(buchung.anreise, buchung.abreise)

        # Hauptgast
        session._open_search_modal(is_main=True)
        found = session.search_and_select(besucher.name, besucher.vorname)
        if not found:
            session.fill_main_guest_manually(besucher)

        # Weitere Gäste (kurtaxe_vz > 1)
        if anzahl_vz > 1:
            session.add_extra_guests(besucher.name, anzahl_vz)

        meldeschein_nr = session.save_and_close()
        log.info('Meldeschein gespeichert, Nr: %s', meldeschein_nr)
        return {'success': True, 'meldeschein_nr': meldeschein_nr}

    except Exception as e:
        log.exception('Feratel Automation fehlgeschlagen')
        return {'success': False, 'error': str(e)}
    finally:
        session.close()

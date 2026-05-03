"""
Tests für Buchung-Methoden rund um Nächte, Ankünfte und Monatsberichte:
  arrivals_for_month, nights_for_month, nights_per_month_*, nights_report,
  happened, cancelled, get_nights
"""

import datetime
import pytest
from bkormlib import Buchung, Portal, Besucher, Apartment
from bkormlib.schema import StaticValuesBuchung


PORTAL = {'name': 'Direkt', 'kommission_prozent': 0, 'active': True, 'collect': False}

BASE = {
    'user_id': 1,
    'besucher_id': 1,
    'apartment_id': 1,
    'portal_id': 1,
    'preis_nacht': 80,
    'zusatzkosten': 0,
    'rabatt': 0,
    'vorauszahlung': 0,
    'kurtaxe_vz': 2,
    'kurtaxe_hz': 1,
    'kurtaxe_kinder': 1,
    'kurtaxe_nz': 0,
    'kurtaxe_korrekturwert': 0,
    'notiz': '',
}


def _make_buchung(anreise, abreise, status='abgerechnet', **kwargs):
    data = dict(BASE)
    data.update(kwargs)
    data['anreise'] = anreise
    data['abreise'] = abreise
    data['status'] = status
    return Buchung(**data)


def setup_db():
    Portal.create(**PORTAL).save()
    Besucher.create(
        user_id=1, anrede='Fam', name='Schmidt', vorname='Hans',
        strasse='', plz='', stadt='', land='DE', email='test@example.com',
        tel='', language='de',
    ).save()
    apt = Apartment.create(
        name='F1', active=True, rooms=2, beds=4,
        address='', description='',
    )
    apt.save()


# ── get_nights ────────────────────────────────────────────────────────────────

class TestGetNights:
    def setup_method(self):
        setup_db()

    def test_same_month(self):
        b = _make_buchung(datetime.date(2024, 5, 10), datetime.date(2024, 5, 17))
        assert b.get_nights() == 7

    def test_cross_month(self):
        b = _make_buchung(datetime.date(2024, 1, 28), datetime.date(2024, 2, 3))
        assert b.get_nights() == 6

    def test_one_night(self):
        b = _make_buchung(datetime.date(2024, 6, 1), datetime.date(2024, 6, 2))
        assert b.get_nights() == 1


# ── happened / cancelled ──────────────────────────────────────────────────────

class TestHappenedCancelled:
    def setup_method(self):
        setup_db()

    def test_abgerechnet_happened(self):
        b = _make_buchung(datetime.date(2024, 5, 1), datetime.date(2024, 5, 7),
                          status='abgerechnet')
        assert b.happened() is True
        assert b.cancelled() is False

    def test_gebucht_not_happened(self):
        b = _make_buchung(datetime.date(2024, 5, 1), datetime.date(2024, 5, 7),
                          status='gebucht')
        assert b.happened() is False
        assert b.cancelled() is True

    def test_storno_cancelled(self):
        b = _make_buchung(datetime.date(2024, 5, 1), datetime.date(2024, 5, 7),
                          status='storno')
        assert b.happened() is False
        assert b.cancelled() is True

    def test_angebot_cancelled(self):
        b = _make_buchung(datetime.date(2024, 5, 1), datetime.date(2024, 5, 7),
                          status='angebot')
        assert b.happened() is False
        assert b.cancelled() is True


# ── arrivals_for_month ────────────────────────────────────────────────────────

class TestArrivalsForMonth:
    """Ankünfte zählen nur für den Monat, in dem die Anreise liegt."""

    def setup_method(self):
        setup_db()

    def test_arrival_in_month(self):
        # Anreise im Mai → Mai hat Ankünfte
        b = _make_buchung(datetime.date(2024, 5, 10), datetime.date(2024, 5, 17),
                          kurtaxe_vz=2, kurtaxe_hz=1, kurtaxe_kinder=1, kurtaxe_nz=0)
        assert b.arrivals_for_month(5, 2024) == 4  # 2 + 1 + 1 + 0

    def test_arrival_not_in_month(self):
        # Anreise im Mai → Juni hat keine Ankünfte
        b = _make_buchung(datetime.date(2024, 5, 10), datetime.date(2024, 6, 3),
                          kurtaxe_vz=2, kurtaxe_hz=0, kurtaxe_kinder=0, kurtaxe_nz=0)
        assert b.arrivals_for_month(6, 2024) == 0

    def test_arrival_wrong_year(self):
        b = _make_buchung(datetime.date(2024, 5, 10), datetime.date(2024, 5, 17),
                          kurtaxe_vz=2, kurtaxe_hz=0, kurtaxe_kinder=0, kurtaxe_nz=0)
        assert b.arrivals_for_month(5, 2023) == 0

    def test_only_vz_guests(self):
        b = _make_buchung(datetime.date(2024, 3, 1), datetime.date(2024, 3, 5),
                          kurtaxe_vz=3, kurtaxe_hz=0, kurtaxe_kinder=0, kurtaxe_nz=0)
        assert b.arrivals_for_month(3, 2024) == 3


# ── nights_for_month ──────────────────────────────────────────────────────────

class TestNightsForMonth:
    """
    Kernlogik: wie viele Nächte fallen in einen bestimmten Monat?
    Beispiel aus dem Docstring: Anreise 27. Jan, Abreise 3. Feb
      → Jan: 4 Nächte (27, 28, 29, 30 = bis Ende Jan), Feb: 3 Nächte (1, 2, Abreise-Tag zählt nicht)
    """

    def setup_method(self):
        setup_db()

    def test_stay_entirely_within_month(self):
        # 10.–17. Mai = 7 Nächte, alles in Mai
        b = _make_buchung(datetime.date(2024, 5, 10), datetime.date(2024, 5, 17))
        assert b.nights_for_month(5, 2024, 1) == 7

    def test_stay_entirely_within_month_multiplied_by_visitors(self):
        b = _make_buchung(datetime.date(2024, 5, 10), datetime.date(2024, 5, 17))
        assert b.nights_for_month(5, 2024, 2) == 14

    def test_stay_crosses_month_boundary_arrival_month(self):
        # Anreise 27. Jan, Abreise 3. Feb → Jan-Nächte = 31 - 27 = 4
        b = _make_buchung(datetime.date(2024, 1, 27), datetime.date(2024, 2, 3))
        assert b.nights_for_month(1, 2024, 1) == 4

    def test_stay_crosses_month_boundary_departure_month(self):
        # Anreise 27. Jan, Abreise 3. Feb → Feb-Nächte = Abreise.day = 3
        b = _make_buchung(datetime.date(2024, 1, 27), datetime.date(2024, 2, 3))
        assert b.nights_for_month(2, 2024, 1) == 3

    def test_stay_before_month_returns_zero(self):
        b = _make_buchung(datetime.date(2024, 3, 1), datetime.date(2024, 3, 10))
        assert b.nights_for_month(5, 2024, 1) == 0

    def test_stay_after_month_returns_zero(self):
        b = _make_buchung(datetime.date(2024, 8, 1), datetime.date(2024, 8, 10))
        assert b.nights_for_month(5, 2024, 1) == 0

    def test_departure_on_first_of_month_no_nights_in_that_month(self):
        # Abreise am 1. Februar → keine Nächte mehr in Februar
        b = _make_buchung(datetime.date(2024, 1, 27), datetime.date(2024, 2, 1))
        assert b.nights_for_month(2, 2024, 1) == 0

    def test_arrival_on_last_of_month_one_night_in_that_month(self):
        # Anreise am 31. Jan, Abreise 3. Feb → Jan-Nächte = 31 - 31 = 0?
        # Nein: monthrange(2024,1)[1] - anreise.day = 31 - 31 = 0
        # Das bedeutet: Anreise am letzten Tag → 0 Nächte in Jan
        b = _make_buchung(datetime.date(2024, 1, 31), datetime.date(2024, 2, 3))
        assert b.nights_for_month(1, 2024, 1) == 0
        assert b.nights_for_month(2, 2024, 1) == 3

    def test_zero_visitors(self):
        b = _make_buchung(datetime.date(2024, 5, 10), datetime.date(2024, 5, 17))
        assert b.nights_for_month(5, 2024, 0) == 0


# ── nights_per_month_* (Wrapper) ──────────────────────────────────────────────

class TestNightsPerMonthWrappers:
    """Die vier Wrapper delegieren an nights_for_month mit der richtigen Gästezahl."""

    def setup_method(self):
        setup_db()

    def _buchung(self):
        return _make_buchung(
            datetime.date(2024, 5, 10), datetime.date(2024, 5, 17),
            kurtaxe_vz=2, kurtaxe_hz=1, kurtaxe_kinder=3, kurtaxe_nz=0,
        )

    def test_ueber_15_kt_uses_kurtaxe_vz(self):
        b = self._buchung()
        assert b.nights_per_month_ueber_15_kt(5, 2024) == 7 * 2

    def test_ueber_15_uses_kurtaxe_nz(self):
        b = self._buchung()
        assert b.nights_per_month_ueber_15(5, 2024) == 7 * 0  # kurtaxe_nz=0

    def test_ueber_10_kt_uses_kurtaxe_hz(self):
        b = self._buchung()
        assert b.nights_per_month_ueber_10_kt(5, 2024) == 7 * 1

    def test_unter_10_uses_kurtaxe_kinder(self):
        b = self._buchung()
        assert b.nights_per_month_unter_10(5, 2024) == 7 * 3


# ── nights_report ─────────────────────────────────────────────────────────────

class TestNightsReport:
    """
    nights_report gibt [ü15_kt, ü15, ü10, u10, gesamt, land] zurück.
    Index 4 = Summe aller Nächte aller Personengruppen.
    """

    def setup_method(self):
        setup_db()

    def test_report_structure_and_length(self):
        b = _make_buchung(
            datetime.date(2024, 5, 10), datetime.date(2024, 5, 17),
            kurtaxe_vz=2, kurtaxe_hz=1, kurtaxe_kinder=1, kurtaxe_nz=0,
        )
        report = b.nights_report(5, 2024)
        assert len(report) == 6

    def test_report_values_single_month_stay(self):
        # 7 Nächte, vz=2, hz=1, kinder=1, nz=0
        b = _make_buchung(
            datetime.date(2024, 5, 10), datetime.date(2024, 5, 17),
            kurtaxe_vz=2, kurtaxe_hz=1, kurtaxe_kinder=1, kurtaxe_nz=0,
        )
        report = b.nights_report(5, 2024)
        assert report[0] == 7 * 2   # ü15 kt
        assert report[1] == 7 * 0   # ü15 (nz)
        assert report[2] == 7 * 1   # ü10 kt (hz)
        assert report[3] == 7 * 1   # u10 (kinder)
        assert report[4] == 7 * 2 + 7 * 0 + 7 * 1 + 7 * 1  # gesamt = 28
        assert report[5] == 'DE'    # land

    def test_report_total_equals_sum_of_parts(self):
        b = _make_buchung(
            datetime.date(2024, 6, 1), datetime.date(2024, 6, 8),
            kurtaxe_vz=3, kurtaxe_hz=2, kurtaxe_kinder=0, kurtaxe_nz=1,
        )
        report = b.nights_report(6, 2024)
        assert report[4] == report[0] + report[1] + report[2] + report[3]

    def test_report_cross_month_only_counts_arrival_month(self):
        # Anreise 27. Jan, Abreise 3. Feb: Jan hat 4 Nächte, Feb hat 3
        b = _make_buchung(
            datetime.date(2024, 1, 27), datetime.date(2024, 2, 3),
            kurtaxe_vz=2, kurtaxe_hz=0, kurtaxe_kinder=0, kurtaxe_nz=0,
        )
        jan = b.nights_report(1, 2024)
        feb = b.nights_report(2, 2024)
        assert jan[0] == 4 * 2  # 4 Jan-Nächte × 2 VZ
        assert feb[0] == 3 * 2  # 3 Feb-Nächte × 2 VZ

    def test_report_outside_month_all_zeros(self):
        b = _make_buchung(
            datetime.date(2024, 5, 10), datetime.date(2024, 5, 17),
            kurtaxe_vz=2, kurtaxe_hz=1, kurtaxe_kinder=1, kurtaxe_nz=0,
        )
        report = b.nights_report(6, 2024)
        assert report[0] == 0
        assert report[4] == 0

"""
Tests for Buchung model — recalc, kurtaxe, miete, offener Betrag.
Recovered from pythonpacks git history (commit beb12c5, removed in dbb7e48).
"""

import datetime
import pytest
from bkormlib import Buchung, Portal, StaticValuesBuchung

PORTAL = {
    'name': 'booking.com',
    'kommission_prozent': 10,
    'active': True,
    'collect': True,
}

BASE_BUCHUNG = {
    'user_id': 1,
    'anreise': datetime.date(2021, 10, 10),
    'abreise': datetime.date(2021, 10, 20),
    'besucher_id': 1,
    'apartment_id': 1,
    'portal_id': 1,
    'kurtaxe_hz': 0,
    'kurtaxe_kinder': 0,
    'kurtaxe_nz': 0,
    'kurtaxe_vz': 2,
    'preis_nacht': 50,
    'zusatzkosten': 50,
    'rabatt': 5,
    'notiz': 'Hat Hund!',
}

KTVZ = StaticValuesBuchung.ktsatz_vz()   # 2.1
KTHZ = StaticValuesBuchung.ktsatz_hz()   # 0.5


class TestBuchungGetters:
    def setup_method(self):
        Portal.create(**PORTAL).save()

    def test_initial_calculated_values_are_zero(self):
        b = Buchung(**BASE_BUCHUNG)
        assert b.anreise == datetime.date(2021, 10, 10)
        assert b.abreise == datetime.date(2021, 10, 20)
        assert b.get_preis_nacht() == 50.0
        assert b.get_zusatzkosten() == 50.0
        assert b.get_miete() == 0
        assert b.get_summe() == 0
        assert b.get_kurtaxe() == 0
        assert b.get_offener_betrag() == 0
        assert b.get_mwst() == 0
        assert b.get_notiz() == 'Hat Hund!'


class TestBuchungRecalc:
    def setup_method(self):
        Portal.create(**PORTAL).save()

    def test_recalc_miete(self):
        # 10 nights × 50 € × (1 - 5%) + 50 Zusatz = 475 + 50 = 525
        b = Buchung(**BASE_BUCHUNG)
        b.recalc(status='gebucht')
        assert b.miete == 525

    def test_recalc_kurtaxe(self):
        b = Buchung(**BASE_BUCHUNG)
        b.recalc(status='gebucht')
        assert b.kurtaxe == 10 * 2 * KTVZ  # 10 Nächte × 2 VZ-Personen

    def test_recalc_summe(self):
        b = Buchung(**BASE_BUCHUNG)
        b.recalc(status='gebucht')
        assert b.summe == 525 + 10 * 2 * KTVZ

    def test_recalc_mwst(self):
        b = Buchung(**BASE_BUCHUNG)
        b.recalc(status='gebucht')
        assert b.get_mwst() == 34.35

    def test_recalc_offener_betrag_equals_summe_without_prepayment(self):
        b = Buchung(**BASE_BUCHUNG)
        b.recalc(status='gebucht')
        assert b.get_vorauszahlung() == 0
        assert b.get_offener_betrag() == b.get_summe()

    def test_recalc_with_prepayment(self):
        b = Buchung(**BASE_BUCHUNG)
        b.recalc(status='gebucht')
        b.vorauszahlung = b.get_summe() - b.get_kurtaxe()
        b.recalc(status=b.status)
        assert b.get_vorauszahlung() == 525
        assert b.get_offener_betrag() == b.get_kurtaxe()

    def test_recalc_after_save(self):
        Buchung(**BASE_BUCHUNG).save()
        b = Buchung.get_by_id(1)
        b.recalc(status='gebucht')
        assert b.miete == 525
        assert b.kurtaxe == 10 * 2 * KTVZ


class TestBuchungKurtaxe:
    def setup_method(self):
        Portal.create(**PORTAL).save()

    def test_kurtaxe_changes_with_abreise(self):
        Buchung(**BASE_BUCHUNG).save()
        b = Buchung.get_by_id(1)
        b.recalc(status='gebucht')
        assert b.get_kurtaxe() == 10 * 2 * KTVZ

        b.abreise = datetime.date(2021, 10, 15)
        b.save()
        b.recalc(status='gebucht')
        assert b.get_kurtaxe() == 5 * 2 * KTVZ

    def test_kurtaxe_hz_added(self):
        Buchung(**BASE_BUCHUNG).save()
        b = Buchung.get_by_id(1)
        b.abreise = datetime.date(2021, 10, 15)
        b.kurtaxe_hz = 1
        b.save()
        b.recalc(status='gebucht')
        assert b.get_kurtaxe() == 5 * 2 * KTVZ + 5 * 1 * KTHZ

    def test_kurtaxe_hz_only(self):
        Buchung(**BASE_BUCHUNG).save()
        b = Buchung.get_by_id(1)
        b.kurtaxe_hz = 2
        b.kurtaxe_vz = 0
        b.save()
        b.recalc(status='gebucht')
        assert b.get_kurtaxe() == 10 * 2 * KTHZ

    def test_kurtaxe_korrekturwert(self):
        Buchung(**BASE_BUCHUNG).save()
        b = Buchung.get_by_id(1)
        b.kurtaxe_hz = 2
        b.kurtaxe_vz = 0
        b.kurtaxe_korrekturwert = 10 * KTHZ
        b.save()
        b.recalc(status='gebucht')
        assert b.get_kurtaxe() == 10 * KTHZ

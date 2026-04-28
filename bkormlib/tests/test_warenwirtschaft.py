"""
Tests für Ware und Verkauf — Lagerreduzierung, Storno, Waren-Summe.
"""

import datetime
import pytest
from bkormlib import Buchung, Portal, Ware, Verkauf


PORTAL = {
    'name': 'booking.com',
    'kommission_prozent': 10,
    'active': True,
    'collect': True,
}

BASE_BUCHUNG = {
    'user_id': 1,
    'anreise': datetime.date(2024, 6, 1),
    'abreise': datetime.date(2024, 6, 8),
    'besucher_id': 1,
    'apartment_id': 1,
    'portal_id': 1,
    'kurtaxe_hz': 0,
    'kurtaxe_kinder': 0,
    'kurtaxe_nz': 0,
    'kurtaxe_vz': 2,
    'preis_nacht': 55,
    'zusatzkosten': 0,
    'rabatt': 0,
    'notiz': '',
    'status': 'gebucht',
}

WAREN = [
    {'bezeichnung': 'Bier 0,5l', 'preis': 2.50, 'mwst_satz': 19,
     'menge_lager': 24, 'active': True},
    {'bezeichnung': 'Wein 0,75l', 'preis': 12.00, 'mwst_satz': 19,
     'menge_lager': 6, 'active': True},
    {'bezeichnung': 'Apfelsaft', 'preis': 1.80, 'mwst_satz': 7,
     'menge_lager': 12, 'active': True},
]


class TestWare:
    def setup_method(self):
        for w in WAREN:
            Ware.create(**w).save()

    def test_ware_erstellt(self):
        assert Ware.get_by_id(1).bezeichnung == 'Bier 0,5l'
        assert float(Ware.get_by_id(1).preis) == 2.50
        assert Ware.get_by_id(1).menge_lager == 24

    def test_choices_nur_aktive(self):
        Ware.create(bezeichnung='Inaktiv', preis=1.0, mwst_satz=19,
                    menge_lager=0, active=False).save()
        choices = Ware.choices()
        bezeichnungen = [c[1] for c in choices]
        assert 'Inaktiv' not in bezeichnungen
        assert len(choices) == 3

    def test_mwst_satz_7_prozent(self):
        assert Ware.get_by_id(3).mwst_satz == 7


class TestVerkauf:
    def setup_method(self):
        Portal.create(**PORTAL).save()
        for w in WAREN:
            Ware.create(**w).save()
        Buchung(**BASE_BUCHUNG).save()

    def _verkaufe(self, ware_id, menge):
        ware = Ware.get_by_id(ware_id)
        Verkauf.create(
            buchung_id=1,
            ware=ware,
            menge=menge,
            preis_zum_zeitpunkt=ware.preis,
            mwst_zum_zeitpunkt=ware.mwst_satz,
        ).save()
        ware.menge_lager -= menge
        ware.save()

    def test_lager_reduziert_nach_verkauf(self):
        self._verkaufe(1, 2)
        assert Ware.get_by_id(1).menge_lager == 22

    def test_storno_erhoeht_lager(self):
        self._verkaufe(1, 2)
        v = Verkauf.get_by_id(1)
        ware = v.ware
        ware.menge_lager += v.menge
        ware.save()
        v.delete_instance()
        assert Ware.get_by_id(1).menge_lager == 24
        assert len(list(Verkauf.select())) == 0

    def test_preis_snapshot(self):
        self._verkaufe(2, 1)
        v = Verkauf.get_by_id(1)
        assert float(v.preis_zum_zeitpunkt) == 12.00
        # Preisänderung nachher beeinflusst nicht den gespeicherten Verkauf
        Ware.get_by_id(2).save()  # preis bleibt gleich (kein Update)
        assert float(Verkauf.get_by_id(1).preis_zum_zeitpunkt) == 12.00

    def test_mehrere_verkaeufe_backref(self):
        self._verkaufe(1, 2)
        self._verkaufe(2, 1)
        b = Buchung.get_by_id(1)
        assert len(list(b.verkaeufe)) == 2

    def test_get_waren_summe(self):
        self._verkaufe(1, 2)   # 2 × 2,50 = 5,00
        self._verkaufe(2, 1)   # 1 × 12,00 = 12,00
        b = Buchung.get_by_id(1)
        assert b.get_waren_summe() == pytest.approx(17.00)

    def test_get_waren_mwst_aufschluesselung(self):
        self._verkaufe(1, 2)   # 19% → 5,00
        self._verkaufe(3, 3)   # 7%  → 3 × 1,80 = 5,40
        b = Buchung.get_by_id(1)
        mwst = b.get_waren_mwst()
        assert mwst[19] == pytest.approx(5.00)
        assert mwst[7] == pytest.approx(5.40)

    def test_get_waren_summe_leer(self):
        b = Buchung.get_by_id(1)
        assert b.get_waren_summe() == 0.0

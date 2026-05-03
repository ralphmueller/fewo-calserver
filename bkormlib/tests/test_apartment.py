"""
Tests for Apartment model — availability checking, invoice numbers, pricing.
Recovered from pythonpacks git history (commit beb12c5, removed in dbb7e48).
"""

import datetime
import pytest
from bkormlib import Apartment, Buchung
from bkormlib.schema import Preisliste

APARTMENTS = [
    {'name': 'F1', 'beschreibung': 'Die schöne Wohnung F1',
     'active': True, 'rechnungs_nummer': 1},
    {'name': 'G1', 'beschreibung': 'Die schöne Wohnung G1', 'active': False},
    {'name': 'G2', 'beschreibung': 'Die schöne Wohnung G2', 'active': True},
]

PREISINFO = [
    {'apartment_id': 1, 'year': 2023, 'preis_2p': 55.0,
     'preis_2p_long': 50.0, 'preis_wp': 7.0},
    {'apartment_id': 1, 'year': 2024, 'preis_2p': 65.0,
     'preis_2p_long': 60.0, 'preis_wp': 8.0},
    {'apartment_id': 2, 'year': 2023, 'preis_2p': 45.0,
     'preis_2p_long': 42.0, 'preis_wp': 7.0},
    {'apartment_id': 2, 'year': 2024, 'preis_2p': 47.0,
     'preis_2p_long': 42.0, 'preis_wp': 7.0},
]

ANREISE = datetime.date(2021, 10, 10)
ABREISE = datetime.date(2021, 10, 24)

BASE_BUCHUNG = {
    'anreise': ANREISE,
    'abreise': ABREISE,
    'besucher_id': 1,
    'user_id': 1,
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
    'status': 'gebucht',
}


def setup_apartments():
    for a in APARTMENTS:
        Apartment.create(**a).save()
    for p in PREISINFO:
        Preisliste.create(**p).save()


class TestApartmentBasic:
    def setup_method(self):
        setup_apartments()

    def test_apartment_name_and_active(self):
        assert Apartment.get_by_id(1).name == 'F1'
        assert Apartment.get_by_id(1).active is True
        assert Apartment.get_by_id(2).name == 'G1'
        assert Apartment.get_by_id(2).active is False

    def test_invoice_number_increments(self):
        apt = Apartment.get_by_id(1)
        assert apt.rechnungs_nummer == 1
        assert apt.get_next_invoice_no() == 2
        assert Apartment.get_by_id(1).rechnungs_nummer == 2

    def test_preisliste_count(self):
        assert len(list(Apartment.get_by_id(1).preislisten)) == 2

    def test_prices_2023(self):
        p = Apartment.get_by_id(1).get_preisliste_year(2023)
        assert p.preis_2p == 55.0
        assert p.preis_2p_long == 50.0

    def test_prices_2024(self):
        p = Apartment.get_by_id(1).get_preisliste_year(2024)
        assert p.preis_2p == 65.0
        assert p.preis_2p_long == 60.0


class TestApartmentPriceForStay:
    def setup_method(self):
        setup_apartments()

    def test_short_stay_2p(self):
        apt = Apartment.get_by_id(1)
        assert apt.get_price_for_stay(
            datetime.date(2023, 10, 22), datetime.date(2023, 10, 25)) == 55.0 * 3

    def test_short_stay_3p(self):
        apt = Apartment.get_by_id(1)
        assert apt.get_price_for_stay(
            datetime.date(2023, 10, 22), datetime.date(2023, 10, 25), 3) == 55.0 * 3 + 7.0 * 3

    def test_long_stay_2p(self):
        apt = Apartment.get_by_id(1)
        assert apt.get_price_for_stay(
            datetime.date(2023, 10, 22), datetime.date(2023, 10, 28)) == 50.0 * 6

    def test_long_stay_3p(self):
        apt = Apartment.get_by_id(1)
        assert apt.get_price_for_stay(
            datetime.date(2023, 10, 22), datetime.date(2023, 10, 28), 3) == 50.0 * 6 + 7.0 * 6

    def test_price_2024(self):
        apt = Apartment.get_by_id(1)
        assert apt.get_price_for_stay(
            datetime.date(2024, 10, 22), datetime.date(2024, 10, 25)) == 65.0 * 3
        assert apt.get_price_for_stay(
            datetime.date(2024, 10, 22), datetime.date(2024, 10, 28)) == 60.0 * 6


class TestApartmentAvailability:
    def setup_method(self):
        setup_apartments()

    def _book(self, anreise, abreise, apartment_id=1, status='gebucht'):
        b = dict(BASE_BUCHUNG)
        b['anreise'] = anreise
        b['abreise'] = abreise
        b['apartment_id'] = apartment_id
        b['status'] = status
        Buchung(**b).save()

    def test_equal_dates_not_available(self):
        self._book(ANREISE, ABREISE)
        assert not Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_past_and_future_dates_available(self):
        self._book(ANREISE, ABREISE)
        assert Apartment.get_by_id(1).check_availability(
            datetime.date(2020, 10, 4), datetime.date(2020, 10, 9))
        assert Apartment.get_by_id(1).check_availability(
            datetime.date(2022, 10, 4), datetime.date(2022, 10, 9))

    def test_existing_booking_starts_earlier_ends_later(self):
        self._book(datetime.date(2021, 10, 9), datetime.date(2021, 10, 25))
        assert not Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_existing_booking_inside_requested(self):
        self._book(datetime.date(2021, 10, 11), datetime.date(2021, 10, 23))
        assert not Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_existing_booking_overlaps_departure(self):
        self._book(datetime.date(2021, 10, 11), datetime.date(2021, 10, 25))
        assert not Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_existing_booking_overlaps_arrival(self):
        self._book(datetime.date(2021, 10, 9), datetime.date(2021, 10, 23))
        assert not Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_booking_for_other_apartment_does_not_block(self):
        self._book(datetime.date(2021, 10, 9), datetime.date(2021, 10, 23),
                   apartment_id=3)
        assert Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_storno_booking_does_not_block(self):
        self._book(ANREISE, ABREISE, status='storno')
        assert Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_back_to_back_new_arrives_on_existing_departure(self):
        # Existing departs 2021-10-10 (= ANREISE), new arrives same day → free
        self._book(datetime.date(2021, 10, 3), ANREISE)
        assert Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

    def test_back_to_back_new_departs_on_existing_arrival(self):
        # New departs 2021-10-24 (= ABREISE), existing arrives same day → free
        self._book(ABREISE, datetime.date(2021, 11, 7))
        assert Apartment.get_by_id(1).check_availability(ANREISE, ABREISE)

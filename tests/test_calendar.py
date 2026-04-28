"""
Tests for calendar logic.

FewoCalendar and days_in_month can be tested without a real database;
the route test verifies that @login_required is enforced.
"""

import datetime
import pytest
from unittest.mock import MagicMock, patch


class TestDaysInMonth:
    """days_in_month is a pure function — no DB needed."""

    def _days_in_month(self, year, month):
        from flaskr.calendar.calendar import days_in_month
        return days_in_month(year, month)

    def test_january_has_31_days(self):
        days = self._days_in_month(2024, 1)
        # January grid can include trailing days from adjacent months
        jan_days = [d for d in days if d[2] == 1]
        assert len(jan_days) == 31

    def test_returns_tuples_with_three_elements(self):
        days = self._days_in_month(2024, 6)
        for entry in days:
            assert len(entry) == 3, "each entry must be (day, weekday, month)"

    def test_weekday_label_for_known_date(self):
        # 2024-01-01 is a Monday
        days = self._days_in_month(2024, 1)
        first_jan = next(d for d in days if d[0] == 1 and d[2] == 1)
        assert first_jan[1] == 'Mo'

    def test_february_leap_year(self):
        days = self._days_in_month(2024, 2)  # 2024 is a leap year
        feb_days = [d for d in days if d[2] == 2]
        assert len(feb_days) == 29

    def test_february_non_leap_year(self):
        days = self._days_in_month(2023, 2)
        feb_days = [d for d in days if d[2] == 2]
        assert len(feb_days) == 28

    def test_all_weekday_labels_are_valid(self):
        valid_labels = {'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'}
        days = self._days_in_month(2024, 3)
        for _, weekday, _ in days:
            assert weekday in valid_labels


class TestCalendarRoute:
    def test_calendar_requires_login(self, client):
        """GET /calendar/month without session → redirect to login."""
        response = client.get('/calendar/month', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_calendar_renders_when_logged_in(self, logged_in_client):
        """GET /calendar/month with session → 200."""
        with patch('flaskr.calendar.calendar.Apartment') as mock_apt:
            mock_apt.select.return_value = []
            response = logged_in_client.get('/calendar/month?year=2024&month=6')
        assert response.status_code == 200

    def test_calendar_accepts_year_month_params(self, logged_in_client):
        """Year and month query parameters are accepted."""
        with patch('flaskr.calendar.calendar.Apartment') as mock_apt:
            mock_apt.select.return_value = []
            response = logged_in_client.get('/calendar/month?year=2023&month=12')
        assert response.status_code == 200


class TestFewoCalendarLogic:
    """Unit tests for FewoCalendar.calendar_for_apartments."""

    def test_empty_apartments_returns_empty_list(self):
        from flaskr.calendar.calendar import FewoCalendar
        with patch('flaskr.calendar.calendar.Apartment') as mock_apt:
            mock_apt.select.return_value = []
            cal = FewoCalendar()
            result = cal.calendar_for_apartments(2024, 6)
        assert result == []

    def test_apartment_without_bookings_has_no_belegung(self):
        """An apartment with no bookings should have no filled days."""
        from flaskr.calendar.calendar import FewoCalendar
        mock_apt = MagicMock()
        mock_apt.active = True
        mock_apt.name = 'Apartment A'
        mock_apt.calendar_support.return_value = []

        with patch('flaskr.calendar.calendar.Apartment') as mock_apt_cls:
            mock_apt_cls.select.return_value = [mock_apt]
            cal = FewoCalendar()
            result = cal.calendar_for_apartments(2024, 6)

        assert len(result) == 1
        # All belegung entries should be empty strings
        belegungen = [day['belegung'] for day in result[0]]
        assert all(b == '' for b in belegungen)

    def test_booking_marks_arrival_and_departure_days(self):
        """A booking spanning 3 days marks 'an', middle, and 'ab' correctly."""
        from flaskr.calendar.calendar import FewoCalendar

        booking = MagicMock()
        booking.anreise = datetime.date(2024, 6, 10)
        booking.abreise = datetime.date(2024, 6, 12)
        booking.besucher.name = 'Müller'
        booking.besucher.vorname = 'Max'
        booking.id = 99

        mock_apt = MagicMock()
        mock_apt.active = True
        mock_apt.name = 'Apartment A'
        mock_apt.calendar_support.return_value = [booking]

        with patch('flaskr.calendar.calendar.Apartment') as mock_apt_cls:
            mock_apt_cls.select.return_value = [mock_apt]
            cal = FewoCalendar()
            result = cal.calendar_for_apartments(2024, 6)

        days = {d['day']: d for d in result[0] if d['month'] == 6}
        assert 'an' in days[10]['belegung']
        assert 'ab' in days[12]['belegung']
        # Day 11 is a middle day — name of apartment in lowercase
        assert days[11]['belegung'] == 'apartment a'
        assert days[11]['buchung_id'] == 99

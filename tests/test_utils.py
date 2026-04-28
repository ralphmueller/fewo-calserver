"""
Tests for pure utility functions that need no database or Flask context.
"""

import datetime
import pytest


class TestGetMondayOfWeek:
    """snippets.get_monday_of_week returns the Monday of the ISO week."""

    def _monday(self, date):
        from flaskr.utils.snippets import get_monday_of_week
        return get_monday_of_week(date).date()

    def test_monday_input_returns_same_day(self):
        monday = datetime.date(2024, 6, 10)  # known Monday
        assert self._monday(monday) == monday

    def test_wednesday_returns_previous_monday(self):
        wednesday = datetime.date(2024, 6, 12)
        expected = datetime.date(2024, 6, 10)
        assert self._monday(wednesday) == expected

    def test_sunday_returns_monday_of_same_week(self):
        sunday = datetime.date(2024, 6, 16)
        expected = datetime.date(2024, 6, 10)
        assert self._monday(sunday) == expected

    def test_first_day_of_year(self):
        # 2024-01-01 is a Monday
        day = datetime.date(2024, 1, 1)
        assert self._monday(day) == day

    def test_year_boundary_week(self):
        # 2023-12-31 is a Sunday → Monday is 2023-12-25
        day = datetime.date(2023, 12, 31)
        expected = datetime.date(2023, 12, 25)
        assert self._monday(day) == expected


class TestDaysInMonthPure:
    """Additional edge-case tests for the calendar helper."""

    def test_grid_length_is_always_multiple_of_7(self):
        from flaskr.calendar.calendar import days_in_month
        for month in range(1, 13):
            days = days_in_month(2024, month)
            assert len(days) % 7 == 0, \
                f"Month {month}: grid length {len(days)} is not a multiple of 7"

    def test_day_numbers_in_range(self):
        from flaskr.calendar.calendar import days_in_month
        days = days_in_month(2024, 3)
        for day_num, _, _ in days:
            assert 1 <= day_num <= 31


class TestForecastYearList:
    """Document the hardcoded year list bug: years stop at 2024."""

    def test_forecast_years_do_not_include_current_year(self):
        """This test will fail once the hardcoded list is fixed to be dynamic."""
        import flaskr.utils.fewo_reporting as reporting
        import inspect

        source = inspect.getsource(reporting.calc_forecast_today)
        # Hardcoded list is a known issue — this test documents it
        assert '2024' in source, (
            "Hardcoded year 2024 no longer present — "
            "verify that calc_forecast_today now uses a dynamic year list"
        )

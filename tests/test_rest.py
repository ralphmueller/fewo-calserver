"""
Tests for REST API endpoints: /rest/...

REST routes currently have no authentication, so all tests use the plain
client. Tests verify HTTP status and JSON response structure.
"""

import json
import pytest
from unittest.mock import MagicMock, patch


class TestRestBuchung:
    def test_get_buchung_returns_json(self, client):
        """/rest/buchung/<id> returns 200 with JSON."""
        mock_booking = MagicMock()
        with patch('flaskr.rest.Buchung') as mock_buchung_cls, \
             patch('flaskr.rest.model_to_dict') as mock_m2d:
            mock_buchung_cls.select.return_value.join.return_value \
                .where.return_value.get.return_value = mock_booking
            mock_m2d.return_value = {
                'id': 1,
                'status': 'gebucht',
                'miete': '500.00',
                'kurtaxe': '21.00',
            }
            response = client.get('/rest/buchung/1')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 1
        assert data['status'] == 'gebucht'

    def test_get_buchung_invalid_id_raises(self, client):
        """/rest/buchung/<id> with unknown id raises an unhandled exception.

        Known issue: the route has no DoesNotExist/404 handler. In Flask TESTING
        mode exceptions propagate to the test rather than becoming 500 responses.
        """
        with patch('flaskr.rest.Buchung') as mock_buchung_cls:
            mock_buchung_cls.select.return_value.join.return_value \
                .where.return_value.get.side_effect = Exception('not found')
            with pytest.raises(Exception, match='not found'):
                client.get('/rest/buchung/9999')


class TestRestBesucher:
    def test_get_besucher_returns_json(self, client):
        """/rest/besucher/<id> returns 200 with visitor JSON."""
        mock_visitor = MagicMock()
        with patch('flaskr.rest.Besucher') as mock_besucher_cls, \
             patch('flaskr.rest.model_to_dict') as mock_m2d:
            mock_besucher_cls.select.return_value \
                .where.return_value.get.return_value = mock_visitor
            mock_m2d.return_value = {
                'id': 42,
                'name': 'Mustermann',
                'vorname': 'Max',
                'email': 'max@example.com',
            }
            response = client.get('/rest/besucher/42')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Mustermann'
        assert data['vorname'] == 'Max'

    def test_get_besucher_by_name_returns_list(self, client):
        """/rest/besucher_by_name/<pattern> returns a JSON list."""
        with patch('flaskr.rest.Besucher') as mock_besucher_cls, \
             patch('flaskr.rest.model_to_dict') as mock_m2d:
            mock_m2d.side_effect = lambda r: {'id': r.id, 'name': r.name}
            mock_result = [MagicMock(id=1, name='Müller'),
                           MagicMock(id=2, name='Müller-Schmidt')]
            mock_besucher_cls.select.return_value \
                .where.return_value = mock_result
            response = client.get('/rest/besucher_by_name/m%C3%BCller')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_besucher_by_name_wildcard_converts_star(self, client):
        """* in search string is converted to % for ILIKE."""
        with patch('flaskr.rest.Besucher') as mock_besucher_cls, \
             patch('flaskr.rest.model_to_dict', return_value={}):
            mock_besucher_cls.select.return_value.where.return_value = []
            # The route should not crash when * is in the pattern
            response = client.get('/rest/besucher_by_name/*m%C3%BCller*')
        assert response.status_code == 200


class TestRestApartment:
    def test_apartment_available_returns_json(self, client):
        """/rest/apartment/available/<id> returns {avail, apartments}."""
        with patch('flaskr.rest.Apartment') as mock_apt_cls:
            mock_apt_instance = MagicMock()
            mock_apt_instance.check_availability.return_value = True
            mock_apt_cls.get_by_id.return_value = mock_apt_instance
            mock_apt_cls.select.return_value = []

            response = client.get(
                '/rest/apartment/available/1'
                '?anreise=2025-06-01&abreise=2025-06-07'
            )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'avail' in data
        assert data['avail'] is True

    def test_apartment_not_available_includes_alternatives(self, client):
        """When requested apartment is not available, alternatives are listed."""
        mock_alt = MagicMock()
        mock_alt.active = True
        mock_alt.name = 'Apartment B'
        mock_alt.check_availability.return_value = True

        with patch('flaskr.rest.Apartment') as mock_apt_cls:
            mock_main = MagicMock()
            mock_main.check_availability.return_value = False
            mock_apt_cls.get_by_id.return_value = mock_main
            mock_apt_cls.select.return_value = [mock_alt]

            response = client.get(
                '/rest/apartment/available/1'
                '?anreise=2025-06-01&abreise=2025-06-07'
            )

        data = json.loads(response.data)
        assert data['avail'] is False
        assert 'Apartment B' in data['apartments']

    def test_apartment_available_bad_date_raises(self, client):
        """Malformed date parameter raises ValueError.

        Known issue: no input validation in the route. In Flask TESTING mode
        the ValueError propagates to the test rather than becoming a 400/500.
        """
        with patch('flaskr.rest.Apartment'):
            with pytest.raises(ValueError):
                client.get(
                    '/rest/apartment/available/1'
                    '?anreise=not-a-date&abreise=2025-06-07'
                )


class TestRestByYears:
    def test_by_years_returns_json_list(self, client):
        """/rest/by_years returns a JSON list of year-aggregates."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (2023, 45, '18000.00', '900.00'),
            (2024, 52, '22000.00', '1040.00'),
        ]
        with patch('flaskr.rest.Buchung') as mock_buchung_cls:
            mock_buchung_cls._meta.database.execute_sql.return_value = mock_cursor
            response = client.get('/rest/by_years')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0][0] == 2023

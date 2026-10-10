from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    db = tmp_path / 'barber.db'
    app = create_app(f'sqlite:///{db}', seed_demo=True, booking_enabled=True)
    with TestClient(app) as c:
        yield c


def future_workday():
    d = datetime.now(ZoneInfo('America/Sao_Paulo')).date() + timedelta(days=3)
    while d.weekday() == 6:
        d += timedelta(days=1)
    return d.isoformat()


def booking_payload(day, *, barber='roger', time='09:00', service='corte'):
    return {'service_id': service, 'barber_id': barber, 'date': day, 'time': time,
            'client_name': 'Cliente Teste', 'client_phone': '19999999999', 'marketing_opt_in': False}


def test_catalog_lists_services_and_barbers(client):
    r = client.get('/api/catalog')
    assert r.status_code == 200
    assert len(r.json()['services']) == 4
    assert len(r.json()['barbers']) == 3


def test_slot_selection_and_collision(client):
    day = future_workday()
    res = client.post('/api/bookings', json=booking_payload(day))
    assert res.status_code == 201, res.text
    assert res.json()['barber_id'] == 'roger'
    assert client.post('/api/bookings', json=booking_payload(day)).status_code == 409
    # A 45 minute service overlaps 09:30, not just identical start time.
    assert client.post('/api/bookings', json=booking_payload(day, time='09:30')).status_code == 409
    assert client.post('/api/bookings', json=booking_payload(day, time='10:00')).status_code == 201


def test_any_barber_assignment(client):
    day = future_workday()
    for _ in range(3):
        r = client.post('/api/bookings', json=booking_payload(day, barber=None))
        assert r.status_code == 201
    assert client.post('/api/bookings', json=booking_payload(day, barber=None)).status_code == 409


def test_lunch_and_sunday_closed(client):
    day = future_workday()
    assert client.post('/api/bookings', json=booking_payload(day, time='11:30')).status_code == 409
    assert client.post('/api/bookings', json=booking_payload(day, time='12:00')).status_code == 409
    d = datetime.fromisoformat(day).date()
    while d.weekday() != 6:
        d += timedelta(days=1)
    assert client.get('/api/availability', params={'service_id': 'corte', 'date': d.isoformat()}).json()['slots'] == []


def test_unsupported_barber_and_invalid_phone(client):
    day = future_workday()
    assert client.post('/api/bookings', json=booking_payload(day, barber='rafael', service='degrade')).status_code == 409
    payload = booking_payload(day)
    payload['client_phone'] = '555'
    assert client.post('/api/bookings', json=payload).status_code == 422


def test_booking_disabled_by_default(tmp_path):
    app = create_app(f'sqlite:///{tmp_path / "locked.db"}', seed_demo=True, booking_enabled=False)
    with TestClient(app) as c:
        assert c.post('/api/bookings', json=booking_payload(future_workday())).status_code == 503


def test_concurrent_requests_only_one_reservation(client):
    day = future_workday()
    payload = booking_payload(day, barber='roger')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post('/api/bookings', json=payload).status_code, range(2)))
    assert sorted(results) == [201, 409]

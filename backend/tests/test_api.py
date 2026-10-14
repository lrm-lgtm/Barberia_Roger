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


def test_internal_dashboard_customers_and_status(tmp_path):
    key = 'k' * 40
    app = create_app(f'sqlite:///{tmp_path / "admin.db"}', seed_demo=True, booking_enabled=True, admin_api_key=key)
    day = future_workday()
    with TestClient(app) as c:
        assert c.post('/api/bookings', json=booking_payload(day)).status_code == 201
        headers = {'Authorization': f'Bearer {key}'}
        dashboard = c.get('/api/admin/dashboard', headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()['metrics']['customers'] == 1
        assert dashboard.json()['ranking'][0]['phone'] == '19999999999'
        customers = c.get('/api/admin/customers?q=Cliente', headers=headers)
        assert customers.status_code == 200
        assert customers.json()['customers'][0]['visits'] == 1
        booking = c.get('/api/admin/bookings', params={'day': day}, headers=headers).json()['bookings'][0]
        assert booking['service_name'] == 'Corte clássico'
        assert c.patch(f"/api/admin/bookings/{booking['id']}", json={'status': 'completed'}, headers=headers).status_code == 200
        assert c.get('/api/admin/dashboard', headers=headers).json()['metrics']['revenue_cents'] == 4500
        assert c.get('/api/admin/customers/19999999999/history', headers=headers).json()['history'][0]['status'] == 'completed'


def test_concurrent_requests_only_one_reservation(client):
    day = future_workday()
    payload = booking_payload(day, barber='roger')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post('/api/bookings', json=payload).status_code, range(2)))
    assert sorted(results) == [201, 409]


def test_availability_days_returns_sunday_closed_and_workdays_open(client):
    day = datetime.now(ZoneInfo('America/Sao_Paulo')).date() + timedelta(days=2)
    r = client.get('/api/availability/days', params={'service_id': 'corte', 'start': day.isoformat(), 'count': 7})
    assert r.status_code == 200, r.text
    days = r.json()['days']
    assert len(days) == 7
    assert any(d['available'] for d in days)
    assert any(not d['available'] for d in days)
    for entry in days:
        if datetime.fromisoformat(entry['date']).weekday() == 6:
            assert entry['available'] is False


def test_availability_days_rejects_invalid_range_and_barber(client):
    day = future_workday()
    assert client.get('/api/availability/days', params={'service_id': 'corte', 'start': day, 'count': 31}).status_code == 422
    assert client.get('/api/availability/days', params={'service_id': 'degrade', 'start': day, 'count': 7, 'barber_id': 'rafael'}).status_code == 422
    assert client.get('/api/availability/days', params={'service_id': 'missing', 'start': day, 'count': 7}).status_code == 404


def test_availability_days_observes_booking_conflict_for_selected_barber(client):
    day = future_workday()
    before = client.get('/api/availability/days', params={'service_id': 'corte', 'start': day, 'count': 1, 'barber_id': 'roger'})
    assert before.json()['days'][0]['available'] is True
    assert client.post('/api/bookings', json=booking_payload(day)).status_code == 201
    after = client.get('/api/availability/days', params={'service_id': 'corte', 'start': day, 'count': 1, 'barber_id': 'roger'})
    assert after.json()['days'][0]['available'] is True  # Other hours remain.

ADMIN_KEY = 'roger-admin-test-only-key-32-chars-safe'
ADMIN_HEADERS = {'Authorization': f'Bearer {ADMIN_KEY}'}


@pytest.fixture
def admin_client(tmp_path):
    db = tmp_path / 'admin.db'
    app = create_app(f'sqlite:///{db}', seed_demo=True, booking_enabled=True, admin_api_key=ADMIN_KEY)
    with TestClient(app) as c:
        yield c


def test_admin_endpoints_require_a_secret_and_fail_closed(admin_client, tmp_path):
    assert admin_client.get('/api/admin/config').status_code == 401
    assert admin_client.get('/api/admin/config', headers={'Authorization': 'Bearer wrong'}).status_code == 401
    assert admin_client.get('/api/admin/config', headers=ADMIN_HEADERS).status_code == 200
    disabled = create_app(f'sqlite:///{tmp_path / "no-admin.db"}', seed_demo=True, admin_api_key='')
    with TestClient(disabled) as c:
        assert c.get('/api/admin/config').status_code == 503
    with pytest.raises(ValueError):
        create_app(f'sqlite:///{tmp_path / "weak.db"}', admin_api_key='weak')


def test_admin_can_create_and_configure_services_and_professionals(admin_client):
    service = {'name': 'Pezinho', 'description': 'Contorno', 'price_cents': 1500,
               'duration_minutes': 30, 'image_url': None, 'active': True}
    assert admin_client.put('/api/admin/services/pezinho', json=service).status_code == 401
    added = admin_client.put('/api/admin/services/pezinho', json=service, headers=ADMIN_HEADERS)
    assert added.status_code == 200, added.text
    professional = {'name': 'Gabriel', 'service_ids': ['pezinho'], 'active': True}
    added = admin_client.put('/api/admin/barbers/gabriel', json=professional, headers=ADMIN_HEADERS)
    assert added.status_code == 200, added.text
    current = admin_client.get('/api/catalog').json()
    assert any(s['id'] == 'pezinho' for s in current['services'])
    assert any(b['id'] == 'gabriel' and b['service_ids'] == ['pezinho'] for b in current['barbers'])
    assert admin_client.put('/api/admin/barbers/oops', json={**professional, 'service_ids': ['unknown']}, headers=ADMIN_HEADERS).status_code == 422
    assert admin_client.put('/api/admin/services/Not-Allowed', json=service, headers=ADMIN_HEADERS).status_code == 422


def test_new_barber_is_unavailable_until_shift_is_configured(admin_client):
    today = future_workday()
    data = {'name': 'Novo Barbeiro', 'service_ids': ['corte'], 'active': True}
    assert admin_client.put('/api/admin/barbers/new-barber', json=data, headers=ADMIN_HEADERS).status_code == 200
    qs = {'service_id': 'corte', 'date': today, 'barber_id': 'new-barber'}
    assert admin_client.get('/api/availability', params=qs).json()['slots'] == []
    weekday = datetime.fromisoformat(today).weekday()
    slots = {'shifts': [{'weekday': weekday, 'start': '09:00', 'end': '11:00'}]}
    response = admin_client.put('/api/admin/barbers/new-barber/shifts', json=slots, headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    times = [s['time'] for s in admin_client.get('/api/availability', params=qs).json()['slots']]
    assert times == ['09:00', '09:30', '10:00']
    assert admin_client.post('/api/bookings', json=booking_payload(today, barber='new-barber', time='11:00')).status_code == 409


def test_custom_schedule_rejects_overlap_and_preserves_confirmed_bookings(admin_client):
    today = future_workday()
    payload = booking_payload(today)
    assert admin_client.post('/api/bookings', json=payload).status_code == 201
    weekday = datetime.fromisoformat(today).weekday()
    invalid = {'shifts': [{'weekday': weekday, 'start': '09:00', 'end': '12:00'},
                          {'weekday': weekday, 'start': '11:00', 'end': '14:00'}]}
    route = '/api/admin/barbers/roger/shifts'
    assert admin_client.put(route, json=invalid, headers=ADMIN_HEADERS).status_code == 422
    without_reserved_time = {'shifts': [{'weekday': weekday, 'start': '10:00', 'end': '18:00'}]}
    assert admin_client.put(route, json=without_reserved_time, headers=ADMIN_HEADERS).status_code == 409
    # The original shift still exists after rejected write.
    slots = admin_client.get('/api/availability', params={'service_id': 'corte', 'date': today, 'barber_id': 'roger'}).json()['slots']
    assert any(s['time'] == '10:00' for s in slots)


def test_blocks_reject_existing_booking_and_can_be_removed(admin_client):
    today = future_workday()
    route = '/api/admin/barbers/roger/blocks'
    assert admin_client.post('/api/bookings', json=booking_payload(today)).status_code == 201
    block = {'date': today, 'start': '09:00', 'end': '10:00', 'reason': 'Folga'}
    assert admin_client.post(route, json=block, headers=ADMIN_HEADERS).status_code == 409
    block['start'], block['end'] = '14:00', '16:00'
    created = admin_client.post(route, json=block, headers=ADMIN_HEADERS)
    assert created.status_code == 201, created.text
    slots = admin_client.get('/api/availability', params={'service_id': 'corte', 'date': today, 'barber_id': 'roger'}).json()['slots']
    assert not any(s['time'] == '14:00' for s in slots)
    block_id = created.json()['id']
    assert admin_client.delete(f'{route}/{block_id}', headers=ADMIN_HEADERS).status_code == 204
    slots = admin_client.get('/api/availability', params={'service_id': 'corte', 'date': today, 'barber_id': 'roger'}).json()['slots']
    assert any(s['time'] == '14:00' for s in slots)


def test_admin_can_read_bookings_but_public_endpoint_does_not_reveal_personal_data(admin_client):
    today = future_workday()
    created = admin_client.post('/api/bookings', json=booking_payload(today))
    assert created.status_code == 201
    assert 'client_phone' not in created.text
    assert 'client_name' not in created.text
    assert admin_client.get('/api/admin/bookings', params={'day': today}).status_code == 401
    staff = admin_client.get('/api/admin/bookings', params={'day': today}, headers=ADMIN_HEADERS)
    assert staff.status_code == 200
    assert staff.json()['bookings'][0]['client_phone'] == '19999999999'
    assert staff.json()['bookings'][0]['client_name'] == 'Cliente Teste'


def test_admin_sunday_shift_overrides_demo_default(admin_client):
    local_today = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
    sunday = local_today + timedelta(days=(6 - local_today.weekday()) % 7 + 7)
    qs = {'service_id': 'corte', 'date': sunday.isoformat(), 'barber_id': 'roger'}
    assert admin_client.get('/api/availability', params=qs).json()['slots'] == []
    config = admin_client.get('/api/admin/config', headers=ADMIN_HEADERS).json()
    roger_shifts = [s for s in config['shifts'] if s['barber_id'] == 'roger']
    roger_shifts.append({'weekday': 6, 'start': '09:00', 'end': '11:00'})
    replacement = {'shifts': [{k: s[k] for k in ('weekday', 'start', 'end')} for s in roger_shifts]}
    assert admin_client.put('/api/admin/barbers/roger/shifts', json=replacement, headers=ADMIN_HEADERS).status_code == 200
    assert admin_client.get('/api/availability', params=qs).json()['slots']


def test_booking_and_block_cannot_both_succeed_for_same_slot(admin_client):
    day = future_workday()
    block = {'date': day, 'start': '09:00', 'end': '10:00', 'reason': 'Bloqueio concorrente'}
    def reserve(_):
        return admin_client.post('/api/bookings', json=booking_payload(day)).status_code
    def block_slot(_):
        return admin_client.post('/api/admin/barbers/roger/blocks', json=block, headers=ADMIN_HEADERS).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(reserve, None), pool.submit(block_slot, None)]
        statuses = sorted(f.result() for f in jobs)
    assert statuses in ([201, 409], [201, 409])

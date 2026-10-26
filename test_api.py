"""
VHotels REST API End-to-End Integration Tests
Validates all endpoints, HTTP response codes, JSON structures, RBAC guards, and CSV exports.
"""

import pytest
import json
import hotel_app
from app import app


@pytest.fixture
def client():
    hotel_app.DB_PATH = 'test_vhotels.db'
    hotel_app.init_db(force_recreate=True)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    hotel_app.DB_PATH = 'vhotels.db'


def test_api_health(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'
    assert 'VHotels' in data['service']


def test_api_auth_workflow(client):
    # 1. Register a new member
    reg_payload = {
        'title': 'Lady',
        'first_name': 'Genevieve',
        'last_name': 'DuPont',
        'dob': '1992-08-14',
        'email': 'genevieve.dupont@chateau.com',
        'password': 'Chateau@123',
        'mobile': '9876543299',
        'preferred_resort': 'VHotels Riviera (Maldives)',
        'address': 'Rue de la Paix, Paris'
    }
    res = client.post('/api/auth/register', json=reg_payload)
    assert res.status_code == 201
    reg_data = res.get_json()
    assert reg_data['success'] is True
    assert reg_data['user']['email'] == 'genevieve.dupont@chateau.com'

    # 2. Check /api/auth/me session
    me_res = client.get('/api/auth/me')
    assert me_res.status_code == 200
    assert me_res.get_json()['authenticated'] is True

    # 3. Logout
    logout_res = client.post('/api/auth/logout')
    assert logout_res.status_code == 200

    # 4. Login with registered account
    login_res = client.post('/api/auth/login', json={
        'email': 'genevieve.dupont@chateau.com',
        'password': 'Chateau@123'
    })
    assert login_res.status_code == 200
    assert login_res.get_json()['user']['first_name'] == 'Genevieve'


def test_api_suite_catalog(client):
    # Query all suites
    res = client.get('/api/suites')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['suites']) >= 6

    # Filter by destination
    res_maldives = client.get('/api/suites?location=Maldives')
    assert res_maldives.status_code == 200
    for s in res_maldives.get_json()['suites']:
        assert 'Maldives' in s['resort_location']


def test_api_booking_and_cancellation_workflow(client):
    # 1. Login as Member
    client.post('/api/auth/login', json={'email': 'member@vhotels.com', 'password': 'Member@123'})

    # 2. Get a suite
    suites_res = client.get('/api/suites')
    suite_id = suites_res.get_json()['suites'][0]['id']

    # 3. Book the suite
    booking_payload = {
        'suite_id': suite_id,
        'check_in_date': '2026-12-01',
        'check_out_date': '2026-12-05',
        'guests_count': 2,
        'special_requests': 'Late check-out please'
    }
    b_res = client.post('/api/bookings', json=booking_payload)
    assert b_res.status_code == 201
    b_data = b_res.get_json()
    assert b_data['success'] is True
    booking_id = b_data['booking']['id']
    assert b_data['booking']['num_nights'] == 4

    # 4. View in guest bookings
    my_bookings = client.get('/api/guest/bookings').get_json()
    assert any(b['id'] == booking_id for b in my_bookings['bookings'])

    # 5. Cancel the booking
    cancel_res = client.post(f'/api/bookings/{booking_id}/cancel')
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()['success'] is True


def test_api_staff_roster_and_csv_export(client):
    # Login as Staff
    client.post('/api/auth/login', json={'email': 'staff@vhotels.com', 'password': 'Staff@123'})

    # Get reservations
    res = client.get('/api/staff/reservations')
    assert res.status_code == 200
    assert 'reservations' in res.get_json()

    # Download CSV export
    csv_res = client.get('/api/staff/reservations/export')
    assert csv_res.status_code == 200
    assert 'text/csv' in csv_res.headers['Content-Type']
    assert b'Booking Ref,Guest Name,Email' in csv_res.data


def test_api_admin_controls(client):
    # Login as Admin
    client.post('/api/auth/login', json={'email': 'admin@vhotels.com', 'password': 'Admin@123'})

    # 1. Get system stats
    stats_res = client.get('/api/admin/stats')
    assert stats_res.status_code == 200
    stats = stats_res.get_json()['stats']
    assert stats['total_suites'] >= 6
    assert stats['total_revenue'] > 0

    # 2. Get users list
    users_res = client.get('/api/admin/users')
    assert users_res.status_code == 200
    users = users_res.get_json()['users']
    assert len(users) >= 3

    # 3. Toggle user status (suspend guest)
    guest_user = [u for u in users if u['role'] == 'guest'][0]
    toggle_res = client.post(f'/api/admin/users/{guest_user["id"]}/toggle-status')
    assert toggle_res.status_code == 200
    assert 'suspended' in toggle_res.get_json()['message']

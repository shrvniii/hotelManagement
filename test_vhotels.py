"""
VHotels Automated Test Suite - Conforming to Lab Manual Experiment 10
Testing Equivalence Partitioning (EP), Boundary Value Analysis (BVA),
Security, Validation, RBAC, and ACID Transactions.
"""

import unittest
import pytest
import datetime
import hotel_app


class TestVHotels(unittest.TestCase):

    def setUp(self):
        # Fresh test database for pristine test isolation
        hotel_app.DB_PATH = 'test_vhotels.db'
        hotel_app.init_db(force_recreate=True)

    def tearDown(self):
        hotel_app.DB_PATH = 'vhotels.db'
        import os
        if os.path.exists('test_vhotels.db'):
            try:
                os.remove('test_vhotels.db')
            except Exception:
                pass

    # ==========================================================================
    # 1. Validation & Equivalence Partitioning (Experiment 3 & 4)
    # ==========================================================================

    def test_tc_register_01_valid_guest(self):
        """TC_REG_01: Verify successful registration with valid inputs."""
        ok, msg, user = hotel_app.register_user(
            title='Lord',
            first_name='Arthur',
            last_name='Pendelton',
            dob='1990-01-01',
            email='arthur.pendelton@luxury.com',
            password='Secure@123',
            mobile='9123456780',
            preferred_resort='VHotels Riviera (Maldives)',
            address='10 Downing St, London',
            role='guest'
        )
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'arthur.pendelton@luxury.com')
        self.assertEqual(user['role'], 'guest')

    def test_tc_register_02_short_first_names_allowed(self):
        """TC_REG_02: Short alphabetic first names like 'Nia' or 'Reha' must succeed."""
        ok, msg, user = hotel_app.register_user(
            title='Ms.',
            first_name='Nia',  # 3 chars, purely alphabetic
            last_name='Sharma',
            dob='1998-05-12',
            email='nia.sharma@vhotels.com',
            password='Password@123',
            mobile='9876543210',
            preferred_resort='',
            address='Valid Address',
            role='guest'
        )
        self.assertTrue(ok)
        self.assertEqual(user['first_name'], 'Nia')

        # Also test 'Reha' (4 chars)
        ok2, msg2, user2 = hotel_app.register_user(
            title='Ms.',
            first_name='Reha',  # 4 chars, purely alphabetic
            last_name='Kapoor',
            dob='1999-07-21',
            email='reha.kapoor@vhotels.com',
            password='Password@123',
            mobile='9876543211',
            preferred_resort='',
            address='Valid Address',
            role='guest'
        )
        self.assertTrue(ok2)
        self.assertEqual(user2['first_name'], 'Reha')

    def test_tc_register_03_invalid_first_name_digits(self):
        """TC_REG_03: First name with digits or symbols must fail."""
        ok, msg, user = hotel_app.register_user(
            title='Mr.',
            first_name='Alexander99',  # Contains digits
            last_name='Smith',
            dob='1995-05-12',
            email='alex.smith@vhotels.com',
            password='Password@123',
            mobile='9876543210',
            preferred_resort='',
            address='Valid Address',
            role='guest'
        )
        self.assertFalse(ok)
        self.assertIn("only alphabets", msg)

    def test_tc_register_password_criteria(self):
        """Verify password rules: 1 caps, 1 no, 1 symbol, min 8 chars."""
        # 1. Less than 8 characters
        ok1, msg1, _ = hotel_app.register_user(
            'Ms.', 'Ananya', 'Sen', '', 'pass1@test.com', 'Pass@1', '9876543210', '', 'Addr'
        )
        self.assertFalse(ok1)
        self.assertIn("at least 8 characters", msg1)

        # 2. Missing uppercase (no caps)
        ok2, msg2, _ = hotel_app.register_user(
            'Ms.', 'Ananya', 'Sen', '', 'pass2@test.com', 'password@123', '9876543210', '', 'Addr'
        )
        self.assertFalse(ok2)
        self.assertIn("uppercase letter", msg2)

        # 3. Missing number (no digit)
        ok3, msg3, _ = hotel_app.register_user(
            'Ms.', 'Ananya', 'Sen', '', 'pass3@test.com', 'Password@Symbol', '9876543210', '', 'Addr'
        )
        self.assertFalse(ok3)
        self.assertIn("number", msg3)

        # 4. Missing symbol
        ok4, msg4, _ = hotel_app.register_user(
            'Ms.', 'Ananya', 'Sen', '', 'pass4@test.com', 'Password123', '9876543210', '', 'Addr'
        )
        self.assertFalse(ok4)
        self.assertIn("special symbol", msg4)

        # 5. Valid password satisfying all criteria (1 caps, 1 no, 1 symbol, min 8 chars)
        ok5, msg5, u5 = hotel_app.register_user(
            'Ms.', 'Ananya', 'Sen', '', 'pass5@test.com', 'Password@123', '9876543210', '', 'Addr'
        )
        self.assertTrue(ok5)

    def test_tc_register_04_invalid_mobile_not_10_digits(self):
        """TC_REG_04: Mobile numbers not exactly 10 digits must fail."""
        # Test 9 digits
        ok1, msg1, _ = hotel_app.register_user(
            title='Ms.', first_name='Eleanor', last_name='Vane', dob='',
            email='eleanor9@test.com', password='ValidPass@1', mobile='987654321',  # 9 digits
            preferred_resort='', address='Address', role='guest'
        )
        self.assertFalse(ok1)
        self.assertIn("exactly 10", msg1)

        # Test 11 digits
        ok2, msg2, _ = hotel_app.register_user(
            title='Ms.', first_name='Eleanor', last_name='Vane', dob='',
            email='eleanor11@test.com', password='ValidPass@1', mobile='98765432100',  # 11 digits
            preferred_resort='', address='Address', role='guest'
        )
        self.assertFalse(ok2)
        self.assertIn("exactly 10", msg2)

    def test_tc_register_05_duplicate_email_prevention(self):
        """TC_REG_05: Cannot register with an already existing email."""
        ok, msg, _ = hotel_app.register_user(
            title='Dr.', first_name='Jonathan', last_name='Duplicate', dob='',
            email='member@vhotels.com',  # Pre-seeded email
            password='NewPassword@123', mobile='9876543219',
            preferred_resort='', address='Address', role='guest'
        )
        self.assertFalse(ok)
        self.assertIn("already exists", msg)

    # ==========================================================================
    # 2. Authentication & RBAC (Role-Based Access Control)
    # ==========================================================================

    def test_tc_login_01_valid_guest(self):
        """TC_LOGIN_01: Valid guest credentials succeed."""
        ok, msg, user = hotel_app.authenticate_user('member@vhotels.com', 'Member@123')
        self.assertTrue(ok)
        self.assertEqual(user['role'], 'guest')

    def test_tc_login_02_valid_staff(self):
        """TC_LOGIN_02: Valid staff credentials succeed with staff role."""
        ok, msg, user = hotel_app.authenticate_user('staff@vhotels.com', 'Staff@123')
        self.assertTrue(ok)
        self.assertEqual(user['role'], 'staff')

    def test_tc_login_03_valid_admin(self):
        """TC_LOGIN_03: Valid admin credentials succeed with admin role."""
        ok, msg, user = hotel_app.authenticate_user('admin@vhotels.com', 'Admin@123')
        self.assertTrue(ok)
        self.assertEqual(user['role'], 'admin')

    def test_tc_login_04_invalid_password(self):
        """TC_LOGIN_04: Wrong password returns failure."""
        ok, msg, user = hotel_app.authenticate_user('member@vhotels.com', 'WrongPass')
        self.assertFalse(ok)
        self.assertIn("Invalid email address or password", msg)

    def test_tc_login_05_empty_fields(self):
        """TC_LOGIN_05: Missing email or password returns failure."""
        ok, msg, user = hotel_app.authenticate_user('', '')
        self.assertFalse(ok)
        self.assertIn("required", msg)

    # ==========================================================================
    # 3. Boundary Value Analysis (BVA): Dates & Capacity
    # ==========================================================================

    def test_tc_bva_dates_past_checkin(self):
        """BVA: Check-in date in the past must be rejected."""
        past_checkin = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        future_checkout = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
        ok, err, nights = hotel_app.validate_booking_dates(past_checkin, future_checkout)
        self.assertFalse(ok)
        self.assertIn("past", err)

    def test_tc_bva_dates_same_day_checkout(self):
        """BVA: Check-out on same date as check-in (0 nights) must be rejected."""
        today = datetime.date.today().isoformat()
        ok, err, nights = hotel_app.validate_booking_dates(today, today)
        self.assertFalse(ok)
        self.assertIn("strictly after", err)

    def test_tc_bva_dates_valid_one_night(self):
        """BVA: Minimum valid stay is exactly 1 night."""
        today = datetime.date.today().isoformat()
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        ok, err, nights = hotel_app.validate_booking_dates(today, tomorrow)
        self.assertTrue(ok)
        self.assertEqual(nights, 1)

    def test_tc_bva_guest_capacity_limits(self):
        """BVA: Guest capacity boundary tests."""
        # Suite PALACE-01 has capacity_guests = 2
        conn = hotel_app.get_db()
        suite = conn.execute("SELECT id, capacity_guests FROM suites WHERE code = 'PALACE-01'").fetchone()
        suite_id = suite['id']
        guest_id = conn.execute("SELECT id FROM users WHERE email = 'member@vhotels.com'").fetchone()['id']
        conn.close()

        ci = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()
        co = (datetime.date.today() + datetime.timedelta(days=22)).isoformat()

        # 1. Zero guests (invalid)
        ok0, err0, _ = hotel_app.create_booking(guest_id, suite_id, ci, co, 0)
        self.assertFalse(ok0)

        # 2. Maximum capacity (2 guests -> valid)
        ok2, err2, b2 = hotel_app.create_booking(guest_id, suite_id, ci, co, 2)
        self.assertTrue(ok2)
        self.assertEqual(b2['guests_count'], 2)
        self.assertEqual(b2['num_nights'], 2)
        # Check 18% GST calculation
        subtotal = b2['price_per_night'] * 2
        expected_tax = round(subtotal * 0.18, 2)
        self.assertEqual(b2['tax_amount'], expected_tax)
        self.assertEqual(b2['total_amount'], round(subtotal + expected_tax, 2))

        # 3. Over capacity (3 guests > 2 capacity -> rejected)
        ok3, err3, _ = hotel_app.create_booking(guest_id, suite_id, ci, co, 3)
        self.assertFalse(ok3)
        self.assertIn("Maximum capacity", err3)

    def test_tc_bva_inventory_exhaustion_and_cancellation(self):
        """BVA: Exhaust available rooms to 0, verify sold out, cancel to recover."""
        conn = hotel_app.get_db()
        cursor = conn.cursor()
        # Set Heights penthouse to exactly 1 available room
        cursor.execute("UPDATE suites SET available_rooms = 1 WHERE code = 'HEIGHTS-01'")
        suite = cursor.execute("SELECT id FROM suites WHERE code = 'HEIGHTS-01'").fetchone()
        suite_id = suite['id']
        guest_id = cursor.execute("SELECT id FROM users WHERE email = 'member@vhotels.com'").fetchone()['id']
        conn.commit()
        conn.close()

        ci = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        co = (datetime.date.today() + datetime.timedelta(days=33)).isoformat()

        # Book the last available room
        ok1, msg1, b1 = hotel_app.create_booking(guest_id, suite_id, ci, co, 2)
        self.assertTrue(ok1)

        # Check inventory is now 0
        s_after = hotel_app.get_suite_by_id(suite_id)
        self.assertEqual(s_after['available_rooms'], 0)

        # Attempt to book when sold out -> must fail
        ok2, msg2, b2 = hotel_app.create_booking(guest_id, suite_id, ci, co, 2)
        self.assertFalse(ok2)
        self.assertIn("sold out", msg2)

        # Cancel the confirmed booking -> inventory restored to 1
        ok_cancel, msg_cancel = hotel_app.cancel_booking(b1['id'], guest_id)
        self.assertTrue(ok_cancel)

        s_restored = hotel_app.get_suite_by_id(suite_id)
        self.assertEqual(s_restored['available_rooms'], 1)

    # ==========================================================================
    # 4. Security & Access Control
    # ==========================================================================

    def test_tc_unauthorized_cancellation(self):
        """Verify Guest A cannot cancel Guest B's reservation."""
        conn = hotel_app.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = 'member@vhotels.com'")
        guest1_id = cursor.fetchone()['id']
        suite_id = cursor.execute("SELECT id FROM suites LIMIT 1").fetchone()['id']
        conn.close()

        ci = (datetime.date.today() + datetime.timedelta(days=40)).isoformat()
        co = (datetime.date.today() + datetime.timedelta(days=42)).isoformat()

        ok, _, booking = hotel_app.create_booking(guest1_id, suite_id, ci, co, 1)
        self.assertTrue(ok)

        # Create Guest 2
        ok2, _, guest2 = hotel_app.register_user('Ms.', 'Victoria', 'Secret', '', 'vic@test.com', 'Pass@123', '9876543200', '', 'Paris', 'guest')
        self.assertTrue(ok2)

        # Guest 2 attempts to cancel Guest 1's booking
        cancel_ok, cancel_msg = hotel_app.cancel_booking(booking['id'], guest2['id'], is_staff_or_admin=False)
        self.assertFalse(cancel_ok)
        self.assertIn("Unauthorized", cancel_msg)


# Standalone pytest functions for pytest test runner
def test_pytest_valid_booking():
    hotel_app.DB_PATH = 'test_vhotels.db'
    hotel_app.init_db(force_recreate=True)
    conn = hotel_app.get_db()
    g_id = conn.execute("SELECT id FROM users WHERE email = 'member@vhotels.com'").fetchone()['id']
    s_id = conn.execute("SELECT id FROM suites WHERE code = 'RIVIERA-01'").fetchone()['id']
    conn.close()

    ci = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
    co = (datetime.date.today() + datetime.timedelta(days=13)).isoformat()

    ok, msg, booked = hotel_app.create_booking(g_id, s_id, ci, co, 2)
    assert ok is True
    assert booked['num_nights'] == 3
    assert booked['status'] == 'confirmed'
    hotel_app.DB_PATH = 'vhotels.db'

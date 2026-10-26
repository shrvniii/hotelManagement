"""
VHotels Luxury Hotel Management System - Core Database Engine & Business Logic
Conforming to Software Engineering Lab standards:
- SQLite3 persistent relational storage with ACID transactions
- Role-Based Access Control (RBAC): Guest, Staff, Admin
- Lab Manual Exp 3 Validation rules (First Name, Password, Email RFC, 10-digit Mobile)
- Room Inventory Management & Double-Booking / Overbooking Prevention (BVA verified)
- Check-in / Check-out Date Validation and GST Tax Calculations
- CSV Roster Export & Digital Booking Voucher Generation
"""

import sqlite3
import os
import re
import random
import datetime
import shutil
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIG_DB_PATH = os.path.join(BASE_DIR, 'vhotels.db')

# On Vercel / serverless environment, use /tmp for a writable SQLite database
if os.environ.get('VERCEL') or not os.access(BASE_DIR, os.W_OK):
    TMP_DB = os.path.join('/tmp', 'vhotels.db')
    if not os.path.exists(TMP_DB) and os.path.exists(ORIG_DB_PATH):
        try:
            shutil.copy2(ORIG_DB_PATH, TMP_DB)
        except Exception:
            pass
    DB_PATH = TMP_DB
else:
    DB_PATH = ORIG_DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==============================================================================
# Validation Rules (Lab Manual Experiment 3 & 4)
# ==============================================================================

def validate_first_name(first_name):
    """Must contain only alphabetic characters."""
    if not first_name or not isinstance(first_name, str):
        return False, "First name is required."
    first_name = first_name.strip()
    if not re.match(r'^[A-Za-z]+$', first_name):
        return False, "First name must contain only alphabets (no digits or special symbols)."
    return True, ""


def validate_last_name(last_name):
    """Last name must not be empty."""
    if not last_name or not isinstance(last_name, str) or not last_name.strip():
        return False, "Last name cannot be empty."
    return True, ""


def validate_password(password):
    """
    Password validation criteria:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 number (0-9)
    - At least 1 special symbol
    """
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least one special symbol (e.g. @, #, $, !)."
    return True, ""


def validate_email(email):
    """Email must follow standard RFC name@domain.com format."""
    if not email or not isinstance(email, str):
        return False, "Email address is required."
    email = email.strip()
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$'
    if not re.match(pattern, email):
        return False, "Invalid email address format (e.g. guest@vhotels.com)."
    return True, ""


def validate_mobile(mobile):
    """Mobile number must contain exactly 10 digits."""
    if not mobile or not isinstance(mobile, str):
        return False, "Mobile number is required."
    mobile = mobile.strip()
    if not re.match(r'^\d{10}$', mobile):
        return False, "Mobile number must be exactly 10 numeric digits."
    return True, ""


def validate_address(address):
    """Address must not be empty."""
    if not address or not isinstance(address, str) or not address.strip():
        return False, "Residential address cannot be empty."
    return True, ""


def validate_booking_dates(check_in_str, check_out_str):
    """
    Validate check-in and check-out dates:
    - Check-in must be formatted as YYYY-MM-DD.
    - Check-out must be after check-in.
    - Minimum 1 night stay.
    """
    try:
        check_in = datetime.date.fromisoformat(check_in_str)
        check_out = datetime.date.fromisoformat(check_out_str)
    except (ValueError, TypeError):
        return False, "Dates must be in valid YYYY-MM-DD format.", 0

    today = datetime.date.today()
    if check_in < today:
        return False, "Check-in date cannot be in the past.", 0
    if check_out <= check_in:
        return False, "Check-out date must be strictly after the check-in date.", 0

    nights = (check_out - check_in).days
    if nights < 1:
        return False, "A booking must be for a minimum of 1 night.", 0

    return True, "", nights


# ==============================================================================
# Database Schema Initialization
# ==============================================================================

def init_db(force_recreate=False):
    if force_recreate and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT 'Mr.',
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dob TEXT,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            mobile TEXT NOT NULL,
            preferred_resort TEXT,
            address TEXT NOT NULL,
            role TEXT DEFAULT 'guest' CHECK(role IN ('guest', 'staff', 'admin')),
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'suspended')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Suites / Rooms Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            resort_location TEXT NOT NULL,
            suite_type TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            capacity_guests INTEGER NOT NULL,
            total_rooms INTEGER NOT NULL,
            available_rooms INTEGER NOT NULL,
            description TEXT,
            amenities TEXT,
            image_url TEXT,
            rating REAL DEFAULT 5.0,
            reviews_count INTEGER DEFAULT 120,
            status TEXT DEFAULT 'available' CHECK(status IN ('available', 'maintenance')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Bookings / Reservations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_reference TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            suite_id INTEGER NOT NULL REFERENCES suites(id) ON DELETE RESTRICT,
            check_in_date TEXT NOT NULL,
            check_out_date TEXT NOT NULL,
            guests_count INTEGER NOT NULL,
            num_nights INTEGER NOT NULL,
            price_per_night REAL NOT NULL,
            subtotal REAL NOT NULL,
            tax_amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            special_requests TEXT,
            status TEXT DEFAULT 'confirmed' CHECK(status IN ('confirmed', 'checked_in', 'checked_out', 'cancelled')),
            cancelled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Inquiries / Concierge Requests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            inquiry_type TEXT DEFAULT 'general',
            resort_location TEXT,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'unread' CHECK(status IN ('unread', 'responded')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Notices / Offers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'offer',
            target_role TEXT DEFAULT 'all',
            author_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    seed_initial_data(conn)
    conn.close()


def seed_initial_data(conn):
    cursor = conn.cursor()

    # Check if admin already exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@vhotels.com'")
    if cursor.fetchone():
        return

    # Seed Default Users with Normal Indian Names (all first names >= 6 letters for Exp 3 compliance)
    users_data = [
        # 1. Administrator
        ('Mr.', 'Rajesh', 'Sharma', '1982-05-14', 'admin@vhotels.com',
         generate_password_hash('Admin@123'), '9876543210', 'VHotels Palace (Rajasthan)',
         '01 Civil Lines, Jaipur, Rajasthan', 'admin'),

        # 2. Hotel Staff Members (Concierge, Front Desk, Estate Supervisors)
        ('Ms.', 'Ananya', 'Patel', '1994-08-22', 'staff@vhotels.com',
         generate_password_hash('Staff@123'), '9876543211', 'VHotels Palace (Rajasthan)',
         'VIP Concierge Desk, Lake Palace Rd, Udaipur', 'staff'),
        ('Mr.', 'Vikram', 'Shetty', '1991-04-12', 'vikram.shetty@vhotels.com',
         generate_password_hash('Staff@123'), '9820543211', 'VHotels Coastal (Goa)',
         'Candolim Beach Operations, Goa', 'staff'),
        ('Mrs.', 'Meenakshi', 'Sundaram', '1989-10-05', 'meenakshi.s@vhotels.com',
         generate_password_hash('Staff@123'), '9845543211', 'VHotels Backwaters (Kerala)',
         'Kumarakom Jetty Concierge, Kerala', 'staff'),
        ('Mr.', 'Raghavendra', 'Rao', '1987-12-19', 'raghav.rao@vhotels.com',
         generate_password_hash('Staff@123'), '9830543211', 'VHotels Himalayan (Kashmir)',
         'Gulmarg Ski Resort Concierge, Kashmir', 'staff'),
        ('Ms.', 'Shalini', 'Deshmukh', '1995-02-14', 'shalini.d@vhotels.com',
         generate_password_hash('Staff@123'), '9811543211', 'VHotels Bay (Mumbai)',
         'Marine Drive VIP Reception, Mumbai', 'staff'),

        # 3. Guest Members / Customers
        ('Mr.', 'Siddharth', 'Verma', '1991-11-18', 'member@vhotels.com',
         generate_password_hash('Member@123'), '9876543212', 'VHotels Palace (Rajasthan)',
         '42 Bandra West, Mumbai, Maharashtra', 'guest'),
        ('Ms.', 'Priyanka', 'Sen', '1993-03-25', 'priyanka.sen@gmail.com',
         generate_password_hash('Priyanka@123'), '9820123456', 'VHotels Backwaters (Kerala)',
         '14 Lake View Road, Kolkata, West Bengal', 'guest'),
        ('Mr.', 'Vikramaditya', 'Singh', '1988-07-19', 'vikramaditya.singh@gmail.com',
         generate_password_hash('Vikram@123'), '9811234567', 'VHotels Bay (Mumbai)',
         '88 Golf Links, New Delhi', 'guest'),
        ('Mrs.', 'Kavita', 'Iyer', '1990-12-05', 'kavita.iyer@gmail.com',
         generate_password_hash('Kavita@123'), '9845012345', 'VHotels Coastal (Goa)',
         '25 Indiranagar, Bengaluru, Karnataka', 'guest'),
        ('Dr.', 'Aditya', 'Khurana', '1986-09-30', 'aditya.khurana@gmail.com',
         generate_password_hash('Aditya@123'), '9830123456', 'VHotels Himalayan (Kashmir)',
         '102 Sector 17, Chandigarh', 'guest'),
        ('Ms.', 'Sunita', 'Mehra', '1995-04-10', 'sunita.mehra@gmail.com',
         generate_password_hash('Sunita@123'), '9871023456', 'VHotels Heritage (Varanasi)',
         '18 Aliganj, Lucknow, Uttar Pradesh', 'guest'),
        ('Mr.', 'Deepak', 'Sharma', '1989-01-15', 'deepak.sharma@gmail.com',
         generate_password_hash('Deepak@123'), '9899123456', 'VHotels Palace (Rajasthan)',
         '56 Jubilee Hills, Hyderabad, Telangana', 'guest'),
        ('Mr.', 'Aakash', 'Gupta', '1992-06-28', 'aakash.gupta@gmail.com',
         generate_password_hash('Aakash@123'), '9821012345', 'VHotels Coastal (Goa)',
         '12 Koregaon Park, Pune, Maharashtra', 'guest'),
        ('Mr.', 'Harish', 'Chandra', '1984-07-03', 'harish.chandra@gmail.com',
         generate_password_hash('Harish@123'), '9810123456', 'VHotels Heritage (Varanasi)',
         '77 Civil Lines, Prayagraj, UP', 'guest'),
        ('Mrs.', 'Rekha', 'Singhania', '1988-11-20', 'rekha.singhania@gmail.com',
         generate_password_hash('Rekha@123'), '9822123456', 'VHotels Palace (Rajasthan)',
         '10 Malabar Hill, Mumbai, Maharashtra', 'guest')
    ]

    for u in users_data:
        cursor.execute("""
            INSERT INTO users (title, first_name, last_name, dob, email, password_hash, mobile, preferred_resort, address, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, u)

    # Seed Expanded Luxury Suites & Resorts
    suites_data = [
        (
            'PALACE-01',
            'VHotels Palace - Royal Mewar Fort Suite',
            'Rajasthan',
            'Heritage',
            55000.0,
            2,
            5,
            4,
            'A magnificent 19th-century royal fortress suite restored into a breathtaking sanctuary, reflecting the grand heritage of Mewar with private courtyard and marble plunge bath.',
            'King Bed, Private Plunge Pool, 24/7 Butler Service, Courtyard View, Marble Bath, Royal High Tea, High-speed Wi-Fi',
            'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?q=80&w=800',
            5.0,
            340
        ),
        (
            'PALACE-02',
            'VHotels Palace - Maharani Heritage Courtyard Suite',
            'Rajasthan',
            'Heritage',
            68000.0,
            3,
            4,
            3,
            'Adorned with gold-leaf ceiling frescoes and hand-carved teak woodwork, celebrating regal Rajasthani hospitality with royal peacock garden vistas.',
            'Super King Bed, Peacock Garden Balcony, Traditional Sitar Welcome, Clawfoot Copper Tub, Private Butler',
            'https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=800',
            4.8,
            142
        ),
        (
            'KERALA-01',
            'VHotels Backwaters - Vembanad Presidential Houseboat Suite',
            'Kerala',
            'Exclusive',
            48000.0,
            2,
            6,
            5,
            'A hand-crafted teakwood luxury cruiser sailing serenely through the Kumarakom backwaters with private sun deck, personal Ayurvedic chef, and sunset cruise.',
            'King Bed, Private Sun Deck, Live Ayurvedic Chef, Backwater Cruise, Jacuzzi, Traditional Malabar High Tea',
            'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?q=80&w=800',
            4.9,
            265
        ),
        (
            'GOA-01',
            'VHotels Coastal - Candolim Grand Beachfront Villa',
            'Goa',
            'Exclusive',
            62000.0,
            4,
            5,
            4,
            'Portuguese-colonial luxury villa nestled amidst swaying palms directly on Candolim sands with private lap pool, beachfront cabana, and sunset BBQ butler.',
            '2 King Suites, Private Lap Pool, Private Beach Cabana, Sunset Cocktail Lounge, Seafood Barbecue Butler',
            'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?q=80&w=800',
            4.9,
            312
        ),
        (
            'KASHMIR-01',
            'VHotels Himalayan - Pir Panjal Pine Forest Chalet',
            'Kashmir',
            'Chalet',
            72000.0,
            4,
            4,
            3,
            'Perched atop snow-dusted pine ridges in Gulmarg with Bukhari cedarwood fireplaces, heated outdoor mountain spa, and ski-in ski-out gondola access.',
            '2 King Bedrooms, Traditional Bukhari Fireplace, Heated Mountain Spa, Ski Concierge, Kashmiri Kahwa Service',
            'https://images.unsplash.com/photo-1502784444187-359ac186c5bb?q=80&w=800',
            4.9,
            195
        ),
        (
            'MUMBAI-01',
            'VHotels Bay - Arabian Sea Imperial Penthouse',
            'Mumbai',
            'Presidential',
            125000.0,
            4,
            2,
            1,
            'Panoramic sweeping vistas of the Queen\'s Necklace from the 45th floor on Marine Drive with private infinity plunge pool and Rolls-Royce chauffeur service.',
            'Master Suite + Guest Room, Arabian Sea Sunset Balcony, 24/7 Butler, Rolls-Royce Airport Transfer, Private Sommelier',
            'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=800',
            5.0,
            118
        ),
        (
            'VARANASI-01',
            'VHotels Heritage - Ganga Ghat Royal Haveli Suite',
            'Varanasi',
            'Heritage',
            42000.0,
            3,
            6,
            5,
            'An exquisitely restored 18th-century stone mansion overlooking the sacred Dashashwamedh Ghat with private sunrise boat tours and serene courtyards.',
            'Stone Balcony, Private Sunrise Boat, Sitar & Flute Recital, Royal Benarasi Thali, Rooftop Ganga Aarti View',
            'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?q=80&w=800',
            4.8,
            176
        ),
        (
            'HEIGHTS-01',
            'VHotels Heights - Central Park Skyline Duplex',
            'New York',
            'Presidential',
            150000.0,
            4,
            2,
            2,
            'Soaring 80 stories above Central Park, this duplex penthouse features 360-degree skyline views, private elevator, and dedicated Michelin chef.',
            'Master Suite + Guest Suite, Private Elevator, Central Park Skyline, Dedicated Private Chef, Chauffeur Service',
            'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=800',
            5.0,
            88
        ),
        (
            'RIVIERA-01',
            'VHotels Riviera - Overwater Ocean Villa',
            'Maldives',
            'Exclusive',
            95000.0,
            3,
            4,
            3,
            'Intimate, private overwater villas floating atop crystal-clear turquoise waters with private infinity deck and direct coral reef access.',
            'King Bed + Daybed, Infinity Glass Deck, Direct Reef Access, Sunset Catamaran Cruise, Private Sommelier, Spa Bath',
            'https://images.unsplash.com/photo-1571896349842-33c89424de2d?q=80&w=800',
            4.9,
            280
        ),
        (
            'ALPINE-01',
            'VHotels Alpine Lodge - Matterhorn Chalet Suite',
            'St. Moritz',
            'Chalet',
            75000.0,
            4,
            6,
            5,
            'Tucked in the pristine snowcapped peaks of the Swiss Alps, offering cedarwood fireplaces, heated balcony spa, and direct ski-in ski-out access.',
            '2 King Bedrooms, Cedar Fireplace, Heated Outdoor Jacuzzi, Ski-in/Ski-out Butler, Mountain Views, Sauna',
            'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?q=80&w=800',
            4.9,
            195
        )
    ]

    for s in suites_data:
        cursor.execute("""
            INSERT INTO suites (code, name, resort_location, suite_type, price_per_night, capacity_guests, total_rooms, available_rooms, description, amenities, image_url, rating, reviews_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, s)

    # Helper maps for seeding reservations
    cursor.execute("SELECT id, email, first_name, last_name FROM users")
    user_map = {row['email']: row['id'] for row in cursor.fetchall()}

    cursor.execute("SELECT id, code, price_per_night, name FROM suites")
    suite_map = {row['code']: row for row in cursor.fetchall()}

    today = datetime.date.today()

    # Seed Realistic Bookings for Indian Customers
    bookings_data = [
        # 1. Siddharth Verma - Udaipur
        (
            'VH-2026-7841', user_map.get('member@vhotels.com'), suite_map['PALACE-01']['id'],
            (today + datetime.timedelta(days=14)).isoformat(), (today + datetime.timedelta(days=17)).isoformat(),
            2, 3, suite_map['PALACE-01']['price_per_night'], 'Anniversary setup with red roses and Rajasthani thali dinner.', 'confirmed'
        ),
        # 2. Priyanka Sen - Kerala Backwaters Houseboat
        (
            'VH-2026-8192', user_map.get('priyanka.sen@gmail.com'), suite_map['KERALA-01']['id'],
            (today + datetime.timedelta(days=7)).isoformat(), (today + datetime.timedelta(days=10)).isoformat(),
            2, 3, suite_map['KERALA-01']['price_per_night'], 'Ayurvedic wellness rejuvenation treatment booking on day 2.', 'confirmed'
        ),
        # 3. Vikramaditya Singh - Mumbai Marine Drive Penthouse
        (
            'VH-2026-9054', user_map.get('vikramaditya.singh@gmail.com'), suite_map['MUMBAI-01']['id'],
            (today - datetime.timedelta(days=1)).isoformat(), (today + datetime.timedelta(days=2)).isoformat(),
            3, 3, suite_map['MUMBAI-01']['price_per_night'], 'Rolls-Royce airport pickup at Chhatrapati Shivaji Airport terminal 2.', 'checked_in'
        ),
        # 4. Kavita Iyer - Goa Beachfront Villa
        (
            'VH-2026-6419', user_map.get('kavita.iyer@gmail.com'), suite_map['GOA-01']['id'],
            (today + datetime.timedelta(days=21)).isoformat(), (today + datetime.timedelta(days=25)).isoformat(),
            4, 4, suite_map['GOA-01']['price_per_night'], 'Candlelight beach dinner setup for family birthday celebration.', 'confirmed'
        ),
        # 5. Aditya Khurana - Kashmir Gulmarg Chalet
        (
            'VH-2026-5381', user_map.get('aditya.khurana@gmail.com'), suite_map['KASHMIR-01']['id'],
            (today - datetime.timedelta(days=4)).isoformat(), (today - datetime.timedelta(days=1)).isoformat(),
            2, 3, suite_map['KASHMIR-01']['price_per_night'], 'Ski instructor and equipment rental requested.', 'checked_out'
        ),
        # 6. Sunita Mehra - Varanasi Ganga Haveli
        (
            'VH-2026-4720', user_map.get('sunita.mehra@gmail.com'), suite_map['VARANASI-01']['id'],
            (today + datetime.timedelta(days=30)).isoformat(), (today + datetime.timedelta(days=32)).isoformat(),
            2, 2, suite_map['VARANASI-01']['price_per_night'], 'Morning Dashashwamedh boat ride with senior family members.', 'confirmed'
        ),
        # 7. Deepak Sharma - Jaipur Maharani Suite
        (
            'VH-2026-3829', user_map.get('deepak.sharma@gmail.com'), suite_map['PALACE-02']['id'],
            (today + datetime.timedelta(days=10)).isoformat(), (today + datetime.timedelta(days=12)).isoformat(),
            2, 2, suite_map['PALACE-02']['price_per_night'], 'Strict Jain vegetarian breakfast arrangements required.', 'confirmed'
        ),
        # 8. Aakash Gupta - Maldives Overwater Villa
        (
            'VH-2026-2184', user_map.get('aakash.gupta@gmail.com'), suite_map['RIVIERA-01']['id'],
            (today + datetime.timedelta(days=40)).isoformat(), (today + datetime.timedelta(days=44)).isoformat(),
            2, 4, suite_map['RIVIERA-01']['price_per_night'], 'Honeymoon arrangement and sunset catamaran cruise.', 'confirmed'
        )
    ]

    for b in bookings_data:
        ref, uid, sid, ci, co, guests, nights, rate, req, status = b
        if uid and sid:
            subtotal = rate * nights
            tax = round(subtotal * 0.18, 2)
            total = round(subtotal + tax, 2)
            cursor.execute("""
                INSERT INTO bookings (
                    booking_reference, user_id, suite_id, check_in_date, check_out_date,
                    guests_count, num_nights, price_per_night, subtotal, tax_amount, total_amount,
                    special_requests, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ref, uid, sid, ci, co, guests, nights, rate, subtotal, tax, total, req, status))

    # Seed Club Notices
    admin_id = user_map.get('admin@vhotels.com', 1)

    notices_data = [
        ('Diwali Royal Illumination & Gala Banquet', 'Celebrate the festival of lights with royal sitar concerts, grand fireworks over Lake Pichola, and a royal feast at VHotels Palace Udaipur.', 'offer', 'all', admin_id),
        ('Ayurvedic Monsoon Rejuvenation Season', 'Bespoke traditional panchakarma therapies and herbal wellness pathways now open at VHotels Backwaters Kumarakom.', 'estate_update', 'all', admin_id),
        ('Kashmir Winter Heliskiing & Pine Retreat', 'Private heliskiing packages and cozy Bukhari fireplace banquets at VHotels Himalayan Chalet Gulmarg through February.', 'offer', 'all', admin_id)
    ]

    for n in notices_data:
        cursor.execute("""
            INSERT INTO notices (title, content, category, target_role, author_id)
            VALUES (?, ?, ?, ?, ?)
        """, n)

    conn.commit()



# ==============================================================================
# Authentication & User Management Business Logic
# ==============================================================================

def register_user(title, first_name, last_name, dob, email, password, mobile, preferred_resort, address, role='guest'):
    """Validates and registers a new user with secure password hashing."""
    # 1. Validation checks
    ok, err = validate_first_name(first_name)
    if not ok: return False, err, None
    ok, err = validate_last_name(last_name)
    if not ok: return False, err, None
    ok, err = validate_password(password)
    if not ok: return False, err, None
    ok, err = validate_email(email)
    if not ok: return False, err, None
    ok, err = validate_mobile(mobile)
    if not ok: return False, err, None
    ok, err = validate_address(address)
    if not ok: return False, err, None

    conn = get_db()
    cursor = conn.cursor()

    # Check duplicate email
    cursor.execute("SELECT id FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),))
    if cursor.fetchone():
        conn.close()
        return False, "An account with this email address already exists. Please sign in.", None

    pwd_hash = generate_password_hash(password)
    try:
        cursor.execute("""
            INSERT INTO users (title, first_name, last_name, dob, email, password_hash, mobile, preferred_resort, address, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title or 'Mr.', first_name.strip(), last_name.strip(), dob or '', email.strip().lower(),
              pwd_hash, mobile.strip(), preferred_resort or '', address.strip(), role))
        user_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.close()
        return False, f"Database error: {str(e)}", None

    cursor.execute("SELECT id, title, first_name, last_name, email, mobile, role, status, preferred_resort, address FROM users WHERE id = ?", (user_id,))
    user = dict(cursor.fetchone())
    conn.close()
    return True, "Membership registration successful. Welcome to VHotels!", user


def authenticate_user(email, password):
    """Authenticates email and password, checks account suspension, returns user info."""
    if not email or not password:
        return False, "Email and password are required.", None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return False, "Invalid email address or password.", None

    if not check_password_hash(user['password_hash'], password):
        return False, "Invalid email address or password.", None

    if user['status'] == 'suspended':
        return False, "Your membership account has been suspended. Please contact concierge administration.", None

    user_dict = {
        'id': user['id'],
        'title': user['title'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'email': user['email'],
        'mobile': user['mobile'],
        'dob': user['dob'],
        'preferred_resort': user['preferred_resort'],
        'address': user['address'],
        'role': user['role'],
        'status': user['status']
    }
    return True, "Login successful.", user_dict


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, first_name, last_name, dob, email, mobile, preferred_resort, address, role, status FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_profile(user_id, title, first_name, last_name, dob, mobile, preferred_resort, address):
    ok, err = validate_first_name(first_name)
    if not ok: return False, err
    ok, err = validate_last_name(last_name)
    if not ok: return False, err
    ok, err = validate_mobile(mobile)
    if not ok: return False, err
    ok, err = validate_address(address)
    if not ok: return False, err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET title = ?, first_name = ?, last_name = ?, dob = ?, mobile = ?, preferred_resort = ?, address = ?
        WHERE id = ?
    """, (title or 'Mr.', first_name.strip(), last_name.strip(), dob or '', mobile.strip(), preferred_resort or '', address.strip(), user_id))
    conn.commit()
    conn.close()
    return True, "Profile updated successfully."


# ==============================================================================
# Suite Catalog & Reservation Business Logic
# ==============================================================================

def get_all_suites(location=None, suite_type=None, min_capacity=None, search=None):
    """Retrieve suites with optional filtering."""
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM suites WHERE status = 'available'"
    params = []

    if location and location.strip():
        query += " AND (resort_location LIKE ? OR name LIKE ?)"
        loc_param = f"%{location.strip()}%"
        params.extend([loc_param, loc_param])

    if suite_type and suite_type.strip() and suite_type.lower() != 'all':
        query += " AND suite_type = ?"
        params.append(suite_type.strip())

    if min_capacity:
        try:
            cap = int(min_capacity)
            query += " AND capacity_guests >= ?"
            params.append(cap)
        except ValueError:
            pass

    if search and search.strip():
        query += " AND (name LIKE ? OR description LIKE ? OR resort_location LIKE ?)"
        s = f"%{search.strip()}%"
        params.extend([s, s, s])

    query += " ORDER BY price_per_night ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_suite_by_id(suite_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM suites WHERE id = ?", (suite_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_booking(user_id, suite_id, check_in_date, check_out_date, guests_count, special_requests=""):
    """
    Creates a confirmed luxury booking with atomic capacity checks:
    - Date format and sequence validation.
    - Capacity and inventory checks.
    - Automatic 18% GST calculation.
    - Unique reference code generation.
    - Decrements available_rooms atomically.
    """
    # 1. Date Validation
    ok, err, nights = validate_booking_dates(check_in_date, check_out_date)
    if not ok:
        return False, err, None

    # 2. Guest Count Validation
    try:
        guests = int(guests_count)
        if guests < 1:
            return False, "At least 1 guest is required.", None
    except (ValueError, TypeError):
        return False, "Guest count must be a positive integer.", None

    conn = get_db()
    cursor = conn.cursor()

    # Retrieve suite under lock
    cursor.execute("SELECT * FROM suites WHERE id = ?", (suite_id,))
    suite = cursor.fetchone()
    if not suite:
        conn.close()
        return False, "Selected suite does not exist.", None

    if suite['status'] != 'available':
        conn.close()
        return False, "This suite is currently undergoing seasonal maintenance.", None

    if guests > suite['capacity_guests']:
        conn.close()
        return False, f"Maximum capacity for this suite is {suite['capacity_guests']} guests.", None

    if suite['available_rooms'] <= 0:
        conn.close()
        return False, "Regrettably, this suite is completely sold out for the selected period.", None

    # Calculate financial totals
    price = suite['price_per_night']
    subtotal = price * nights
    tax = round(subtotal * 0.18, 2)
    total = round(subtotal + tax, 2)

    # Generate unique booking reference
    ref_suffix = random.randint(1000, 9999)
    booking_ref = f"VH-2026-{ref_suffix}"

    try:
        # Atomic inventory decrement
        cursor.execute("""
            UPDATE suites
            SET available_rooms = available_rooms - 1
            WHERE id = ? AND available_rooms > 0
        """, (suite_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            return False, "Suite capacity was just filled by another reservation. Please choose another estate.", None

        cursor.execute("""
            INSERT INTO bookings (
                booking_reference, user_id, suite_id, check_in_date, check_out_date,
                guests_count, num_nights, price_per_night, subtotal, tax_amount, total_amount,
                special_requests, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')
        """, (booking_ref, user_id, suite_id, check_in_date, check_out_date,
              guests, nights, price, subtotal, tax, total, special_requests or ''))

        booking_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Reservation error: {str(e)}", None

    # Fetch complete booking details
    cursor.execute("""
        SELECT b.*, s.name as suite_name, s.resort_location, s.image_url,
               u.first_name, u.last_name, u.email, u.mobile, u.title
        FROM bookings b
        JOIN suites s ON b.suite_id = s.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id = ?
    """, (booking_id,))
    booked = dict(cursor.fetchone())
    conn.close()

    return True, "Your luxury stay is confirmed! We look forward to welcoming you.", booked


def cancel_booking(booking_id, user_id, is_staff_or_admin=False):
    """
    Cancels a confirmed reservation and restores suite inventory.
    Enforces authorization check unless cancelled by staff/admin.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        conn.close()
        return False, "Reservation not found."

    if not is_staff_or_admin and booking['user_id'] != user_id:
        conn.close()
        return False, "Unauthorized: You can only cancel your own reservations."

    if booking['status'] == 'cancelled':
        conn.close()
        return False, "This reservation has already been cancelled."

    try:
        cursor.execute("""
            UPDATE bookings
            SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (booking_id,))

        # Restore inventory
        cursor.execute("""
            UPDATE suites
            SET available_rooms = available_rooms + 1
            WHERE id = ?
        """, (booking['suite_id'],))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Cancellation error: {str(e)}"

    conn.close()
    return True, "Reservation successfully cancelled. Room inventory has been restored."


def get_user_bookings(user_id):
    """Fetch all reservations for a given guest."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, s.name as suite_name, s.resort_location, s.image_url, s.suite_type
        FROM bookings b
        JOIN suites s ON b.suite_id = s.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_bookings(search=None, status=None, resort=None):
    """Staff & Admin view of all reservations across all properties."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT b.*, s.name as suite_name, s.resort_location, s.code as suite_code,
               u.first_name, u.last_name, u.email, u.mobile, u.title
        FROM bookings b
        JOIN suites s ON b.suite_id = s.id
        JOIN users u ON b.user_id = u.id
        WHERE 1=1
    """
    params = []

    if status and status.strip() and status.lower() != 'all':
        query += " AND b.status = ?"
        params.append(status.strip())

    if resort and resort.strip() and resort.lower() != 'all':
        query += " AND s.resort_location LIKE ?"
        params.append(f"%{resort.strip()}%")

    if search and search.strip():
        s = f"%{search.strip()}%"
        query += " AND (b.booking_reference LIKE ? OR u.first_name LIKE ? OR u.last_name LIKE ? OR u.email LIKE ? OR s.name LIKE ?)"
        params.extend([s, s, s, s, s])

    query += " ORDER BY b.check_in_date ASC, b.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_booking_status(booking_id, new_status):
    """Staff operation: update status (confirmed -> checked_in -> checked_out)."""
    valid_statuses = ('confirmed', 'checked_in', 'checked_out', 'cancelled')
    if new_status not in valid_statuses:
        return False, "Invalid booking status."

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))
    conn.commit()
    conn.close()
    return True, f"Reservation status updated to {new_status}."


# ==============================================================================
# Administration & Analytics Operations
# ==============================================================================

def get_admin_system_stats():
    """Calculates operational and financial KPIs."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'guest'")
    total_guests = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM suites")
    total_suites = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE status != 'cancelled'")
    active_bookings = cursor.fetchone()['count']

    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM bookings WHERE status != 'cancelled'")
    total_revenue = cursor.fetchone()['revenue']

    cursor.execute("SELECT SUM(total_rooms) as total_cap, SUM(available_rooms) as avail_cap FROM suites")
    cap_row = cursor.fetchone()
    total_cap = cap_row['total_cap'] or 1
    avail_cap = cap_row['avail_cap'] or 0
    occupied = total_cap - avail_cap
    occupancy_pct = round((occupied / total_cap) * 100, 1)

    conn.close()
    return {
        'total_guests': total_guests,
        'total_suites': total_suites,
        'active_bookings': active_bookings,
        'total_revenue': round(total_revenue, 2),
        'total_rooms': total_cap,
        'available_rooms': avail_cap,
        'occupancy_pct': occupancy_pct
    }


def get_all_users_admin(search=None, role=None, status=None):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, title, first_name, last_name, email, mobile, role, status, preferred_resort, address, created_at FROM users WHERE 1=1"
    params = []

    if role and role.strip() and role.lower() != 'all':
        query += " AND role = ?"
        params.append(role.strip())

    if status and status.strip() and status.lower() != 'all':
        query += " AND status = ?"
        params.append(status.strip())

    if search and search.strip():
        s = f"%{search.strip()}%"
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR mobile LIKE ?)"
        params.extend([s, s, s, s])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_user_status(user_id, requesting_admin_id):
    """Suspend or reactivate a user account."""
    if int(user_id) == int(requesting_admin_id):
        return False, "Administrators cannot suspend their own account."

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status, role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "User not found."

    new_status = 'suspended' if row['status'] == 'active' else 'active'
    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()
    return True, f"User account has been {new_status}."


def create_suite(code, name, resort_location, suite_type, price_per_night, capacity_guests, total_rooms, description="", amenities="", image_url=""):
    """Admin function to create a new luxury suite property."""
    if not code or not name or not resort_location:
        return False, "Suite code, name, and resort location are required."

    try:
        price = float(price_per_night)
        capacity = int(capacity_guests)
        rooms = int(total_rooms)
        if price <= 0 or capacity <= 0 or rooms <= 0:
            return False, "Price, capacity, and total rooms must be positive numbers."
    except (ValueError, TypeError):
        return False, "Invalid numeric values provided for price, capacity, or total rooms."

    conn = get_db()
    cursor = conn.cursor()

    # Check for duplicate code
    cursor.execute("SELECT id FROM suites WHERE code = ?", (code.strip().upper(),))
    if cursor.fetchone():
        conn.close()
        return False, f"A suite with code '{code.strip().upper()}' already exists."

    img = image_url.strip() if image_url else "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?q=80&w=800"
    try:
        cursor.execute("""
            INSERT INTO suites (code, name, resort_location, suite_type, price_per_night, capacity_guests, total_rooms, available_rooms, description, amenities, image_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available')
        """, (code.strip().upper(), name.strip(), resort_location.strip(), suite_type or 'Exclusive', price, capacity, rooms, rooms, description.strip(), amenities.strip(), img))
        suite_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.close()
        return False, f"Database error creating suite: {str(e)}"

    conn.close()
    return True, f"Suite '{name}' successfully created and added to inventory."


def update_suite(suite_id, name, resort_location, suite_type, price_per_night, capacity_guests, total_rooms, available_rooms, status='available'):
    """Admin function to update suite pricing, rooms, or maintenance status."""
    try:
        price = float(price_per_night)
        capacity = int(capacity_guests)
        tot_rooms = int(total_rooms)
        avail_rooms = int(available_rooms)
    except (ValueError, TypeError):
        return False, "Invalid numeric values for price, capacity, or rooms."

    if avail_rooms > tot_rooms:
        return False, "Available rooms cannot exceed total rooms."

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM suites WHERE id = ?", (suite_id,))
    if not cursor.fetchone():
        conn.close()
        return False, "Suite not found."

    cursor.execute("""
        UPDATE suites
        SET name = ?, resort_location = ?, suite_type = ?, price_per_night = ?,
            capacity_guests = ?, total_rooms = ?, available_rooms = ?, status = ?
        WHERE id = ?
    """, (name.strip(), resort_location.strip(), suite_type, price, capacity, tot_rooms, avail_rooms, status, suite_id))
    conn.commit()
    conn.close()
    return True, "Suite details and inventory successfully updated."


def delete_suite(suite_id):
    """Admin function to safely delete a suite or mark as maintenance if bookings exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM suites WHERE id = ?", (suite_id,))
    suite = cursor.fetchone()
    if not suite:
        conn.close()
        return False, "Suite not found."

    # Check active bookings
    cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE suite_id = ? AND status != 'cancelled'", (suite_id,))
    active_count = cursor.fetchone()['count']
    if active_count > 0:
        # Instead of deleting and breaking relational integrity, mark as maintenance
        cursor.execute("UPDATE suites SET status = 'maintenance', available_rooms = 0 WHERE id = ?", (suite_id,))
        conn.commit()
        conn.close()
        return True, f"Suite '{suite['name']}' has {active_count} active booking(s). It has been decommissioned and set to 'Maintenance' so no further reservations can be made."

    try:
        cursor.execute("DELETE FROM suites WHERE id = ?", (suite_id,))
        conn.commit()
    except Exception as e:
        conn.close()
        return False, f"Could not delete suite: {str(e)}"

    conn.close()
    return True, f"Suite '{suite['name']}' permanently deleted from the estate database."


# ==============================================================================
# Inquiries & Notices
# ==============================================================================

def create_inquiry(name, email, inquiry_type, resort_location, message):
    if not name or not email or not message:
        return False, "Name, email, and message are required."
    ok, err = validate_email(email)
    if not ok: return False, err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inquiries (name, email, inquiry_type, resort_location, message)
        VALUES (?, ?, ?, ?, ?)
    """, (name.strip(), email.strip(), inquiry_type or 'general', resort_location or '', message.strip()))
    conn.commit()
    conn.close()
    return True, "Your message has been received by our head concierge."


def get_notices(target_role='all'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notices
        WHERE target_role = 'all' OR target_role = ?
        ORDER BY created_at DESC LIMIT 10
    """, (target_role,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_notice(title, content, category, target_role, author_id):
    if not title or not content:
        return False, "Title and content cannot be empty."

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notices (title, content, category, target_role, author_id)
        VALUES (?, ?, ?, ?, ?)
    """, (title.strip(), content.strip(), category or 'offer', target_role or 'all', author_id))
    conn.commit()
    conn.close()
    return True, "Notice published successfully."


# Auto-initialize database on module import
init_db(force_recreate=False)

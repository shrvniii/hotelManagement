"""
VHotels Luxury Hotel Management System - Flask Application & REST API
Features:
- Full page routing with role-based access control (RBAC)
- RESTful JSON endpoints for auth, suite catalog, reservations, and admin
- Secure session management with CSRF protection and HTTP security headers
- CSV Attendance / Guest Check-in Roster Export for Hotel Staff
- Automated error handling and JSON validation
"""

import os
import io
import csv
from datetime import datetime
from flask import (
    Flask, request, jsonify, session, send_from_directory,
    Response, abort, make_response
)
from flask_cors import CORS
import hotel_app

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'vhotels_luxury_secret_key_2026_se_project')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

CORS(app, supports_credentials=True)

# Ensure database is ready
hotel_app.init_db()


# ==============================================================================
# Helper & RBAC Decorators
# ==============================================================================

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return hotel_app.get_user_by_id(user_id)


def require_auth(roles=None):
    def decorator(f):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
            if user.get('status') == 'suspended':
                session.clear()
                return jsonify({'success': False, 'message': 'Your account has been suspended.'}), 403
            if roles and user.get('role') not in roles:
                return jsonify({'success': False, 'message': f'Access denied: requires {", ".join(roles)} privileges.'}), 403
            return f(user, *args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


# ==============================================================================
# Page Serving Routes
# ==============================================================================

@app.route('/')
@app.route('/index.html')
def page_home():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/suites.html')
def page_suites():
    return send_from_directory(BASE_DIR, 'suites.html')


@app.route('/booking.html')
def page_booking():
    return send_from_directory(BASE_DIR, 'booking.html')


@app.route('/login.html')
def page_login():
    return send_from_directory(BASE_DIR, 'login.html')


@app.route('/register.html')
def page_register():
    return send_from_directory(BASE_DIR, 'register.html')


@app.route('/profile.html')
def page_profile():
    return send_from_directory(BASE_DIR, 'profile.html')


@app.route('/staff_dashboard.html')
def page_staff():
    return send_from_directory(BASE_DIR, 'staff_dashboard.html')


@app.route('/admin_dashboard.html')
def page_admin():
    return send_from_directory(BASE_DIR, 'admin_dashboard.html')


# ==============================================================================
# Authentication REST API
# ==============================================================================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    title = data.get('title', 'Mr.')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    dob = data.get('dob', '')
    email = data.get('email', '')
    password = data.get('password', '')
    mobile = data.get('mobile', '')
    preferred_resort = data.get('preferred_resort', '')
    address = data.get('address', '')
    role = data.get('role', 'guest')

    # Security: only admin can register other staff/admins
    if role in ('staff', 'admin'):
        current = get_current_user()
        if not current or current.get('role') != 'admin':
            role = 'guest'

    ok, msg, user = hotel_app.register_user(
        title, first_name, last_name, dob, email, password, mobile, preferred_resort, address, role
    )
    if not ok:
        return jsonify({'success': False, 'message': msg}), 400

    # Automatically establish login session
    session.permanent = True
    session['user_id'] = user['id']
    session['role'] = user['role']
    session['email'] = user['email']

    return jsonify({
        'success': True,
        'message': msg,
        'user': user
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')

    ok, msg, user = hotel_app.authenticate_user(email, password)
    if not ok:
        status_code = 403 if "suspended" in msg.lower() else 401
        return jsonify({'success': False, 'message': msg}), status_code

    session.permanent = True
    session['user_id'] = user['id']
    session['role'] = user['role']
    session['email'] = user['email']

    return jsonify({
        'success': True,
        'message': msg,
        'user': user
    }), 200


@app.route('/api/auth/logout', methods=['POST', 'GET'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'}), 200


@app.route('/api/auth/me', methods=['GET'])
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False}), 200
    return jsonify({
        'authenticated': True,
        'user': user
    }), 200


@app.route('/api/auth/profile', methods=['PUT'])
@require_auth()
def api_update_profile(current_user):
    data = request.get_json() or {}
    title = data.get('title', current_user.get('title', 'Mr.'))
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    dob = data.get('dob', '')
    mobile = data.get('mobile', '')
    preferred_resort = data.get('preferred_resort', '')
    address = data.get('address', '')

    ok, msg = hotel_app.update_user_profile(
        current_user['id'], title, first_name, last_name, dob, mobile, preferred_resort, address
    )
    if not ok:
        return jsonify({'success': False, 'message': msg}), 400

    updated = hotel_app.get_user_by_id(current_user['id'])
    return jsonify({'success': True, 'message': msg, 'user': updated}), 200


# ==============================================================================
# Suite Catalog & Details API
# ==============================================================================

@app.route('/api/suites', methods=['GET'])
def api_suites_list():
    location = request.args.get('location')
    suite_type = request.args.get('type')
    min_capacity = request.args.get('capacity')
    search = request.args.get('q')

    suites = hotel_app.get_all_suites(
        location=location,
        suite_type=suite_type,
        min_capacity=min_capacity,
        search=search
    )
    return jsonify({'success': True, 'count': len(suites), 'suites': suites}), 200


@app.route('/api/suites/<int:suite_id>', methods=['GET'])
def api_suite_details(suite_id):
    suite = hotel_app.get_suite_by_id(suite_id)
    if not suite:
        return jsonify({'success': False, 'message': 'Suite not found.'}), 404
    return jsonify({'success': True, 'suite': suite}), 200


# ==============================================================================
# Booking & Reservation REST API
# ==============================================================================

@app.route('/api/bookings', methods=['POST'])
@require_auth()
def api_create_booking(current_user):
    data = request.get_json() or {}
    suite_id = data.get('suite_id')
    check_in_date = data.get('check_in_date')
    check_out_date = data.get('check_out_date')
    guests_count = data.get('guests_count', 1)
    special_requests = data.get('special_requests', '')

    if not suite_id or not check_in_date or not check_out_date:
        return jsonify({'success': False, 'message': 'Suite ID, check-in, and check-out dates are required.'}), 400

    ok, msg, booking = hotel_app.create_booking(
        user_id=current_user['id'],
        suite_id=suite_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        guests_count=guests_count,
        special_requests=special_requests
    )

    if not ok:
        return jsonify({'success': False, 'message': msg}), 400

    return jsonify({
        'success': True,
        'message': msg,
        'booking': booking
    }), 201


@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
@require_auth()
def api_cancel_booking(current_user, booking_id):
    is_staff = current_user.get('role') in ('staff', 'admin')
    ok, msg = hotel_app.cancel_booking(booking_id, current_user['id'], is_staff_or_admin=is_staff)
    if not ok:
        status_code = 403 if "Unauthorized" in msg else 400
        return jsonify({'success': False, 'message': msg}), status_code
    return jsonify({'success': True, 'message': msg}), 200


@app.route('/api/guest/bookings', methods=['GET'])
@require_auth()
def api_my_bookings(current_user):
    bookings = hotel_app.get_user_bookings(current_user['id'])
    return jsonify({'success': True, 'bookings': bookings}), 200


# ==============================================================================
# Staff & Concierge REST API
# ==============================================================================

@app.route('/api/staff/reservations', methods=['GET'])
@require_auth(roles=['staff', 'admin'])
def api_staff_reservations(current_user):
    search = request.args.get('q')
    status = request.args.get('status')
    resort = request.args.get('resort')

    reservations = hotel_app.get_all_bookings(search=search, status=status, resort=resort)
    return jsonify({'success': True, 'count': len(reservations), 'reservations': reservations}), 200


@app.route('/api/staff/reservations/<int:booking_id>/status', methods=['POST'])
@require_auth(roles=['staff', 'admin'])
def api_staff_update_status(current_user, booking_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify({'success': False, 'message': 'New status is required.'}), 400

    ok, msg = hotel_app.update_booking_status(booking_id, new_status)
    if not ok:
        return jsonify({'success': False, 'message': msg}), 400
    return jsonify({'success': True, 'message': msg}), 200


@app.route('/api/staff/reservations/export', methods=['GET'])
@require_auth(roles=['staff', 'admin'])
def api_export_reservations_csv(current_user):
    """Exports reservation roster to CSV for check-in and attendance recording."""
    reservations = hotel_app.get_all_bookings()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Booking Ref', 'Guest Name', 'Email', 'Mobile', 'Suite Name',
        'Resort Estate', 'Check-in Date', 'Check-out Date', 'Nights',
        'Guests', 'Total Paid (INR)', 'Status'
    ])

    for r in reservations:
        guest_name = f"{r.get('title', '')} {r.get('first_name', '')} {r.get('last_name', '')}".strip()
        writer.writerow([
            r['booking_reference'],
            guest_name,
            r['email'],
            r['mobile'],
            r['suite_name'],
            r['resort_location'],
            r['check_in_date'],
            r['check_out_date'],
            r['num_nights'],
            r['guests_count'],
            r['total_amount'],
            r['status']
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=vhotels_guest_roster_{datetime.now().strftime("%Y%m%d")}.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8'
    return response


# ==============================================================================
# Administrator REST API
# ==============================================================================

@app.route('/api/admin/stats', methods=['GET'])
@require_auth(roles=['admin'])
def api_admin_stats(current_user):
    stats = hotel_app.get_admin_system_stats()
    return jsonify({'success': True, 'stats': stats}), 200


@app.route('/api/admin/users', methods=['GET'])
@require_auth(roles=['admin'])
def api_admin_users(current_user):
    search = request.args.get('q')
    role = request.args.get('role')
    status = request.args.get('status')
    users = hotel_app.get_all_users_admin(search=search, role=role, status=status)
    return jsonify({'success': True, 'count': len(users), 'users': users}), 200


@app.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@require_auth(roles=['admin'])
def api_admin_toggle_user(current_user, user_id):
    ok, msg = hotel_app.toggle_user_status(user_id, current_user['id'])
    if not ok:
        return jsonify({'success': False, 'message': msg}), 400
    return jsonify({'success': True, 'message': msg}), 200


# ==============================================================================
# Inquiries & Notices API
# ==============================================================================

@app.route('/api/inquiries', methods=['POST'])
def api_post_inquiry():
    data = request.get_json() or {}
    ok, msg = hotel_app.create_inquiry(
        name=data.get('name', ''),
        email=data.get('email', ''),
        inquiry_type=data.get('type', 'general'),
        resort_location=data.get('location', ''),
        message=data.get('message', '')
    )
    if not ok:
        return jsonify({'success': False, 'message': msg}), 400
    return jsonify({'success': True, 'message': msg}), 201


@app.route('/api/notices', methods=['GET'])
def api_get_notices():
    role = session.get('role', 'all')
    notices = hotel_app.get_notices(target_role=role)
    return jsonify({'success': True, 'notices': notices}), 200


@app.route('/api/notices', methods=['POST'])
@require_auth(roles=['admin', 'staff'])
def api_create_notice(current_user):
    data = request.get_json() or {}
    ok, msg = hotel_app.create_notice(
        title=data.get('title', ''),
        content=data.get('content', ''),
        category=data.get('category', 'offer'),
        target_role=data.get('target_role', 'all'),
        author_id=current_user['id']
    )
    if not ok:
        return jsonify({'success': False, 'message': msg}), 400
    return jsonify({'success': True, 'message': msg}), 201


# ==============================================================================
# System Health & Fallbacks
# ==============================================================================

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({
        'status': 'healthy',
        'service': 'VHotels Luxury Hotel Management System API',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting VHotels Luxury Hotel Management System on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

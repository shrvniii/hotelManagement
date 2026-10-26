/**
 * VHotels Luxury Hotel Management System - Client Application Controller
 * Handles auth state, dynamic navbar updates, booking vouchers, AJAX forms, and toasts.
 */

const VHotels = {
  currentUser: null,

  async init() {
    await this.checkAuth();
    this.bindGlobalEvents();
  },

  async checkAuth() {
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      if (data.authenticated) {
        this.currentUser = data.user;
      } else {
        this.currentUser = null;
      }
      this.updateNavbar();
    } catch (err) {
      console.warn('Auth check failed:', err);
    }
  },

  updateNavbar() {
    const navLinks = document.getElementById('menu-links');
    if (!navLinks) return;

    if (!this.currentUser) {
      navLinks.innerHTML = `
        <li><a href="index.html">Home</a></li>
        <li><a href="suites.html">Suites & Estates</a></li>
        <li><a href="index.html#dining-experience">Dining</a></li>
        <li><a href="index.html#why-choose-us">Services</a></li>
        <li><a href="register.html">Register</a></li>
        <li class="nav-btn"><a href="login.html" class="btn-gold" style="padding: 10px 22px; font-size: 0.8rem;">Member Login</a></li>
      `;
    } else if (this.currentUser.role === 'admin') {
      navLinks.innerHTML = `
        <li><a href="index.html">Home</a></li>
        <li><a href="suites.html">Suites</a></li>
        <li><a href="admin_dashboard.html" class="active" style="color: var(--color-gold); font-weight: 600;"><i class="fas fa-chart-line"></i> Executive Admin</a></li>
        <li><a href="staff_dashboard.html"><i class="fas fa-concierge-bell"></i> Staff Portal</a></li>
        <li><a href="profile.html">Profile</a></li>
        <li class="nav-btn"><button onclick="VHotels.logout()" class="btn-gold" style="padding: 8px 18px; font-size: 0.8rem; cursor: pointer;">Logout (${this.currentUser.first_name})</button></li>
      `;
    } else if (this.currentUser.role === 'staff') {
      navLinks.innerHTML = `
        <li><a href="index.html">Home</a></li>
        <li><a href="suites.html">Suites</a></li>
        <li><a href="staff_dashboard.html" class="active" style="color: var(--color-gold); font-weight: 600;"><i class="fas fa-concierge-bell"></i> Staff Concierge</a></li>
        <li><a href="profile.html">Profile</a></li>
        <li class="nav-btn"><button onclick="VHotels.logout()" class="btn-gold" style="padding: 8px 18px; font-size: 0.8rem; cursor: pointer;">Logout (${this.currentUser.first_name})</button></li>
      `;
    } else {
      // Guest Member
      navLinks.innerHTML = `
        <li><a href="index.html">Home</a></li>
        <li><a href="suites.html">Suites & Estates</a></li>
        <li><a href="profile.html#my-bookings" style="color: var(--color-gold); font-weight: 600;"><i class="fas fa-calendar-check"></i> My Reservations</a></li>
        <li><a href="profile.html">Profile</a></li>
        <li class="nav-btn"><button onclick="VHotels.logout()" class="btn-gold" style="padding: 8px 18px; font-size: 0.8rem; cursor: pointer;">Logout (${this.currentUser.first_name})</button></li>
      `;
    }
  },

  async logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      this.currentUser = null;
      this.showToast('You have been logged out.', 'info');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 700);
    } catch (e) {
      window.location.href = 'index.html';
    }
  },

  showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = `
        position: fixed;
        bottom: 25px;
        right: 25px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        gap: 12px;
        max-width: 380px;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bg = type === 'error' ? '#c0392b' : type === 'info' ? '#2980b9' : '#1e7e34';
    const icon = type === 'error' ? 'exclamation-circle' : type === 'info' ? 'info-circle' : 'check-circle';

    toast.style.cssText = `
      background: ${bg};
      color: #ffffff;
      padding: 14px 20px;
      border-radius: 8px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 12px;
      animation: slideInToast 0.3s ease;
      font-family: inherit;
    `;
    toast.innerHTML = `<i class="fas fa-${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.4s ease';
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  },

  showVoucherModal(booking) {
    let modal = document.getElementById('voucher-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'voucher-modal';
      modal.className = 'modal-overlay';
      document.body.appendChild(modal);
    }

    const subtotalFormatted = Number(booking.subtotal || 0).toLocaleString('en-IN');
    const taxFormatted = Number(booking.tax_amount || 0).toLocaleString('en-IN');
    const totalFormatted = Number(booking.total_amount || 0).toLocaleString('en-IN');

    modal.innerHTML = `
      <div class="modal-card" style="max-width: 650px; background: #ffffff; color: #111111; border-radius: 12px; padding: 30px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #c9a227; padding-bottom: 15px; margin-bottom: 20px;">
          <div>
            <h2 style="font-family: var(--font-serif); font-size: 1.8rem; margin: 0; color: #111111;">VHOTELS</h2>
            <span style="font-size: 0.75rem; letter-spacing: 0.2em; text-transform: uppercase; color: #c9a227;">Official Luxury Reservation Voucher</span>
          </div>
          <button onclick="document.getElementById('voucher-modal').classList.remove('active')" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #888;">&times;</button>
        </div>

        <div style="background: #fdfaf3; border: 1px dashed #c9a227; border-radius: 8px; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <div>
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #777;">Booking Reference</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #c9a227;">${booking.booking_reference}</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #777;">Reservation Status</div>
            <span style="display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; background: #d4edda; color: #155724; text-transform: uppercase;">
              ${booking.status}
            </span>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; font-size: 0.9rem;">
          <div>
            <div style="color: #777; font-size: 0.75rem; text-transform: uppercase;">Guest Name</div>
            <div style="font-weight: 600;">${booking.title || ''} ${booking.first_name || ''} ${booking.last_name || ''}</div>
          </div>
          <div>
            <div style="color: #777; font-size: 0.75rem; text-transform: uppercase;">Reserved Suite</div>
            <div style="font-weight: 600;">${booking.suite_name || 'VHotels Luxury Suite'}</div>
          </div>
          <div>
            <div style="color: #777; font-size: 0.75rem; text-transform: uppercase;">Check-in Date</div>
            <div style="font-weight: 600;">${booking.check_in_date} (14:00 onwards)</div>
          </div>
          <div>
            <div style="color: #777; font-size: 0.75rem; text-transform: uppercase;">Check-out Date</div>
            <div style="font-weight: 600;">${booking.check_out_date} (11:00 am)</div>
          </div>
          <div>
            <div style="color: #777; font-size: 0.75rem; text-transform: uppercase;">Length of Stay</div>
            <div style="font-weight: 600;">${booking.num_nights} Night(s) | ${booking.guests_count} Guest(s)</div>
          </div>
          <div>
            <div style="color: #777; font-size: 0.75rem; text-transform: uppercase;">Resort Estate</div>
            <div style="font-weight: 600;">${booking.resort_location || 'Global Estate'}</div>
          </div>
        </div>

        <div style="border-top: 1px solid #eee; padding-top: 15px; margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.9rem;">
            <span style="color: #666;">Room Subtotal (${booking.num_nights} nights):</span>
            <span style="font-weight: 600;">₹${subtotalFormatted}</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.9rem;">
            <span style="color: #666;">Luxury Hospitality GST (18%):</span>
            <span style="font-weight: 600;">₹${taxFormatted}</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 1.15rem; font-weight: 700; border-top: 1px dashed #ccc; padding-top: 8px; margin-top: 8px;">
            <span>Total Amount Paid:</span>
            <span style="color: #c9a227;">₹${totalFormatted}</span>
          </div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #eee; padding-top: 15px;">
          <div style="font-size: 0.75rem; color: #888;">
            * Present this digital voucher or QR confirmation upon arrival at the VIP Reception.
          </div>
          <div style="display: flex; gap: 10px;">
            <button onclick="window.print()" class="btn-outline" style="color: #111; border-color: #ccc; padding: 8px 16px; font-size: 0.85rem; cursor: pointer;">
              <i class="fas fa-print"></i> Print
            </button>
            <button onclick="document.getElementById('voucher-modal').classList.remove('active')" class="btn-gold" style="padding: 8px 16px; font-size: 0.85rem; cursor: pointer;">
              Done
            </button>
          </div>
        </div>
      </div>
    `;

    modal.classList.add('active');
  },

  bindGlobalEvents() {
    // Booking search form on index.html
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const dest = document.getElementById('destination')?.value || '';
        const checkin = document.getElementById('checkin')?.value || '';
        const checkout = document.getElementById('checkout')?.value || '';
        const guests = document.getElementById('guests')?.value || '2';

        const params = new URLSearchParams();
        if (dest) params.append('location', dest.split(',')[0]);
        if (checkin) params.append('checkin', checkin);
        if (checkout) params.append('checkout', checkout);
        if (guests) params.append('guests', guests);

        window.location.href = `suites.html?${params.toString()}`;
      });
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  VHotels.init();
});

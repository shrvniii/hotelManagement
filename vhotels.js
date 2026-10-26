/**
 * VHotels Luxury Hotel Management System - Client Application Controller
 * Handles auth state, dynamic navbar updates, booking vouchers, AJAX forms,
 * AI virtual concierge "Aria", weather ticker, and toasts.
 */

const VHotels = {
  currentUser: null,

  async init() {
    await this.checkAuth();
    this.bindGlobalEvents();
    this.initWeatherRibbon();
    this.initConciergeWidget();
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

  /* ========================================================
     VVIP BOARDING PASS & OFFICIAL RESERVATION PASSBOOK
     ======================================================== */
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
    const guestFullName = `${booking.title || ''} ${booking.first_name || ''} ${booking.last_name || ''}`.trim() || 'VIP Esteemed Guest';

    modal.innerHTML = `
      <div class="boarding-pass-card">
        <!-- Passbook Gold Header -->
        <div class="boarding-pass-header">
          <div>
            <div style="font-size: 0.72rem; letter-spacing: 0.25em; text-transform: uppercase; color: #c9a227; margin-bottom: 4px;">
              <i class="fas fa-crown"></i> VHotels Solitaire Hospitality
            </div>
            <h2 style="font-family: var(--font-serif); font-size: 1.8rem; margin: 0; color: #ffffff; letter-spacing: 0.05em;">
              Official Reservation Passbook
            </h2>
          </div>
          <button onclick="document.getElementById('voucher-modal').classList.remove('active')" style="background: none; border: none; font-size: 1.6rem; cursor: pointer; color: #c9a227; line-height: 1;">&times;</button>
        </div>

        <!-- Reference & Status Banner -->
        <div style="background: #faf6ee; border-bottom: 1px solid #ebd9b8; padding: 14px 28px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <span style="font-size: 0.7rem; text-transform: uppercase; color: #777; letter-spacing: 0.1em; display: block;">VVIP Pass Code</span>
            <span style="font-size: 1.35rem; font-weight: 800; color: #111; letter-spacing: 0.08em; font-family: monospace;">
              ${booking.booking_reference}
            </span>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <span style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; background: #e8f5e9; color: #2e7d32; text-transform: uppercase; border: 1px solid #c8e6c9;">
              <i class="fas fa-check-circle"></i> Confirmed & Guaranteed
            </span>
            <span style="display: inline-flex; align-items: center; gap: 5px; padding: 6px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; background: #fdf2d5; color: #8a6d1c; text-transform: uppercase; border: 1px solid #f3dba3;">
              <i class="fas fa-star"></i> Fast-Track VIP
            </span>
          </div>
        </div>

        <!-- Passenger / Stay Details Grid -->
        <div style="padding: 24px 28px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px 24px; font-size: 0.88rem; background: #ffffff;">
          <div>
            <div style="color: #888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px;">Primary Guest</div>
            <div style="font-weight: 700; color: #111; font-size: 1.05rem;">${guestFullName}</div>
          </div>
          <div>
            <div style="color: #888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px;">Estate Residence</div>
            <div style="font-weight: 700; color: #111; font-size: 1.05rem;">${booking.suite_name || 'VHotels Luxury Suite'}</div>
          </div>
          <div>
            <div style="color: #888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px;">Priority Check-In</div>
            <div style="font-weight: 600; color: #222;">
              <i class="fas fa-calendar-alt" style="color: var(--color-gold);"></i> ${booking.check_in_date}
              <span style="font-size: 0.78rem; color: #666; display: block;">From 14:00 (VIP Reception)</span>
            </div>
          </div>
          <div>
            <div style="color: #888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px;">Luxury Check-Out</div>
            <div style="font-weight: 600; color: #222;">
              <i class="fas fa-calendar-check" style="color: var(--color-gold);"></i> ${booking.check_out_date}
              <span style="font-size: 0.78rem; color: #666; display: block;">Until 11:00 (16:00 for Elite)</span>
            </div>
          </div>
          <div>
            <div style="color: #888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px;">Stay Duration & Party</div>
            <div style="font-weight: 600; color: #222;">
              ${booking.num_nights} Night(s) &bull; ${booking.guests_count} Registered Guest(s)
            </div>
          </div>
          <div>
            <div style="color: #888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px;">Resort Destination</div>
            <div style="font-weight: 600; color: #222;">
              <i class="fas fa-map-marker-alt" style="color: var(--color-gold);"></i> ${booking.resort_location || 'Global Luxury Estate'}
            </div>
          </div>
        </div>

        ${booking.special_requests ? `
          <div style="margin: 0 28px 18px; padding: 12px 16px; background: #faf8f4; border: 1px dashed #decbb5; border-radius: 8px; font-size: 0.82rem;">
            <strong style="color: var(--color-gold); text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; display: block; margin-bottom: 3px;">
              <i class="fas fa-concierge-bell"></i> Bespoke Concierge Inclusions & Notes:
            </strong>
            <span style="color: #444;">${booking.special_requests}</span>
          </div>
        ` : ''}

        <!-- Barcode / Digital Seal Strip -->
        <div class="boarding-barcode-strip">
          <div style="display: flex; align-items: center; gap: 14px;">
            <svg width="42" height="42" viewBox="0 0 40 40" fill="none" style="border: 2px solid #111; padding: 2px; border-radius: 4px; background: #fff;">
              <rect x="2" y="2" width="10" height="10" fill="#111" />
              <rect x="5" y="5" width="4" height="4" fill="#fff" />
              <rect x="24" y="2" width="10" height="10" fill="#111" />
              <rect x="27" y="5" width="4" height="4" fill="#fff" />
              <rect x="2" y="24" width="10" height="10" fill="#111" />
              <rect x="5" y="27" width="4" height="4" fill="#fff" />
              <rect x="16" y="4" width="4" height="12" fill="#111" />
              <rect x="16" y="20" width="8" height="4" fill="#111" />
              <rect x="26" y="16" width="8" height="8" fill="#111" />
              <rect x="14" y="28" width="12" height="6" fill="#111" />
            </svg>
            <div>
              <span style="font-size: 0.72rem; text-transform: uppercase; color: #666; display: block;">Digital Boarding Pass</span>
              <span style="font-size: 0.82rem; font-weight: 600; color: #111;">Scan at private estate reception</span>
            </div>
          </div>
          <!-- Barcode simulation -->
          <div style="text-align: right; opacity: 0.85;">
            <div style="font-family: monospace; font-size: 0.7rem; letter-spacing: 4px; color: #111; font-weight: 700;">||| | |||| | || ||||| | |||</div>
            <span style="font-size: 0.68rem; color: #888;">AUTH_TOKEN: ${booking.booking_reference}</span>
          </div>
        </div>

        <!-- Folio Breakdown -->
        <div style="padding: 18px 28px; background: #fafafa; border-top: 1px solid #eee;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.85rem; color: #555;">
            <span>Room Tariff & Accommodations (${booking.num_nights} nights):</span>
            <span style="font-weight: 600; color: #111;">₹${subtotalFormatted}</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.85rem; color: #555;">
            <span>Luxury Hospitality GST & Heritage Surcharge (18%):</span>
            <span style="font-weight: 600; color: #111;">₹${taxFormatted}</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 1.25rem; font-weight: 800; border-top: 1px dashed #ccc; padding-top: 10px; margin-top: 6px; color: #111;">
            <span>Total Folio Amount:</span>
            <span style="color: var(--color-gold);">₹${totalFormatted}</span>
          </div>
        </div>

        <!-- Actions -->
        <div style="padding: 16px 28px; background: #ffffff; border-top: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;" class="no-print">
          <span style="font-size: 0.75rem; color: #888;">
            * Present this digital pass or mention reservation code at check-in.
          </span>
          <div style="display: flex; gap: 10px;">
            <button onclick="window.print()" class="btn-outline" style="color: #111; border-color: #ccc; padding: 9px 18px; font-size: 0.85rem; cursor: pointer; border-radius: 6px;">
              <i class="fas fa-print"></i> Print Official Pass
            </button>
            <button onclick="document.getElementById('voucher-modal').classList.remove('active')" class="btn-gold" style="padding: 9px 20px; font-size: 0.85rem; cursor: pointer; border-radius: 6px;">
              Done
            </button>
          </div>
        </div>
      </div>
    `;

    modal.classList.add('active');
  },

  /* ========================================================
     WORLD DESTINATION WEATHER & LUXURY CLOCK RIBBON
     ======================================================== */
  initWeatherRibbon() {
    if (document.getElementById('vhotels-weather-bar')) return;
    const nav = document.getElementById('nav-header');
    if (!nav) return;

    const bar = document.createElement('div');
    bar.id = 'vhotels-weather-bar';
    bar.className = 'vhotels-weather-bar';
    bar.innerHTML = `
      <div class="container weather-bar-inner">
        <div class="weather-tag">
          <i class="fas fa-globe" style="color: var(--color-gold);"></i>
          <span>GLOBAL ESTATES LIVE:</span>
        </div>
        <div class="weather-tag">
          <strong>Udaipur</strong> <span class="weather-temp">24°C</span> ☀️ Clear
        </div>
        <div class="weather-tag">
          <strong>Goa</strong> <span class="weather-temp">29°C</span> 🏖️ Tropical Breeze
        </div>
        <div class="weather-tag">
          <strong>Kerala</strong> <span class="weather-temp">27°C</span> 🌴 Backwaters
        </div>
        <div class="weather-tag">
          <strong>Gulmarg</strong> <span class="weather-temp">-2°C</span> ❄️ Powder Snow
        </div>
        <div class="weather-tag">
          <strong>Maldives</strong> <span class="weather-temp">31°C</span> 🌊 Turquoise
        </div>
        <div class="weather-tag">
          <strong>Mumbai</strong> <span class="weather-temp">28°C</span> 🏙️ Marine Drive
        </div>
        <div class="weather-tag" style="margin-left: auto;">
          <i class="fas fa-concierge-bell" style="color: var(--color-gold);"></i>
          <span style="color: var(--color-gold);">Concierge Desk: 24/7 Active</span>
        </div>
      </div>
    `;

    nav.parentNode.insertBefore(bar, nav);
  },

  /* ========================================================
     VIRTUAL AI CONCIERGE & BUTLER "ARIA"
     ======================================================== */
  initConciergeWidget() {
    if (document.getElementById('aria-launcher')) return;

    // 1. Create Launcher Pill
    const launcher = document.createElement('div');
    launcher.id = 'aria-launcher';
    launcher.className = 'aria-launcher';
    launcher.innerHTML = `
      <div class="aria-avatar-icon">
        <div class="aria-pulse-ring"></div>
        <i class="fas fa-bell"></i>
      </div>
      <div class="aria-launcher-text">
        <span class="name"><span class="sparkle">&#10024;</span> Aria Butler</span>
        <span class="subtitle">24/7 AI Concierge</span>
      </div>
    `;
    document.body.appendChild(launcher);

    // 2. Create Chat Box
    const chatBox = document.createElement('div');
    chatBox.id = 'aria-chat-box';
    chatBox.className = 'aria-chat-box';
    chatBox.innerHTML = `
      <div class="aria-header">
        <div class="aria-header-info">
          <div class="aria-avatar-icon" style="width: 32px; height: 32px; font-size: 0.9rem;">
            <i class="fas fa-concierge-bell"></i>
          </div>
          <div>
            <h3 class="aria-header-title">Aria Concierge</h3>
            <span class="aria-header-sub">VHotels Virtual Butler</span>
          </div>
        </div>
        <button class="aria-close-btn" id="aria-close-btn">&times;</button>
      </div>

      <div class="aria-messages" id="aria-messages-list">
        <div class="aria-msg assistant">
          <div class="bubble">
            <strong>Greetings & Welcome.</strong><br>
            I am <em>Aria</em>, your 24/7 personal virtual concierge. How may I orchestrate your luxury experience today?
            <div class="aria-chips">
              <button class="aria-chip" onclick="VHotels.sendAriaPrompt('Recommend a romantic suite')">💍 Romantic Suites</button>
              <button class="aria-chip" onclick="VHotels.sendAriaPrompt('Tell me about Michelin dining')">🍽️ Michelin Dining</button>
              <button class="aria-chip" onclick="VHotels.sendAriaPrompt('Airport transfer options')">🚘 Rolls-Royce Transfer</button>
              <button class="aria-chip" onclick="VHotels.sendAriaPrompt('How is price calculated?')">💳 Pricing & Taxes</button>
              <button class="aria-chip" onclick="VHotels.sendAriaPrompt('What are check-in times?')">⏰ Check-in Policies</button>
            </div>
          </div>
        </div>
      </div>

      <form class="aria-footer" id="aria-form">
        <input type="text" class="aria-input" id="aria-input-text" placeholder="Ask Aria anything about your stay..." autocomplete="off">
        <button type="submit" class="aria-send-btn"><i class="fas fa-paper-plane"></i></button>
      </form>
    `;
    document.body.appendChild(chatBox);

    // Toggle logic
    launcher.addEventListener('click', () => {
      chatBox.classList.toggle('active');
      if (chatBox.classList.contains('active')) {
        setTimeout(() => document.getElementById('aria-input-text').focus(), 150);
      }
    });

    document.getElementById('aria-close-btn').addEventListener('click', () => {
      chatBox.classList.remove('active');
    });

    document.getElementById('aria-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const input = document.getElementById('aria-input-text');
      const val = input.value.trim();
      if (!val) return;
      this.sendAriaPrompt(val);
      input.value = '';
    });
  },

  sendAriaPrompt(query) {
    const list = document.getElementById('aria-messages-list');
    if (!list) return;

    // Add user bubble
    const userDiv = document.createElement('div');
    userDiv.className = 'aria-msg user';
    userDiv.innerHTML = `<div class="bubble">${query}</div>`;
    list.appendChild(userDiv);
    list.scrollTop = list.scrollHeight;

    // Add typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'aria-msg assistant';
    typingDiv.id = 'aria-typing-bubble';
    typingDiv.innerHTML = `
      <div class="bubble aria-typing">
        <span></span><span></span><span></span>
      </div>
    `;
    list.appendChild(typingDiv);
    list.scrollTop = list.scrollHeight;

    // Generate intelligent luxury answer
    setTimeout(() => {
      typingDiv.remove();
      const reply = this.generateAriaResponse(query);
      const botDiv = document.createElement('div');
      botDiv.className = 'aria-msg assistant';
      botDiv.innerHTML = `<div class="bubble">${reply}</div>`;
      list.appendChild(botDiv);
      list.scrollTop = list.scrollHeight;
    }, 450);
  },

  generateAriaResponse(q) {
    const text = q.toLowerCase();

    if (text.includes('romantic') || text.includes('couple') || text.includes('honeymoon')) {
      return `For couples, I highly recommend our <strong>VHotels Coastal Beach Villa in Candolim, Goa</strong> (featuring a private lap pool & sunset butler barbecue) or the <strong>VHotels Riviera Overwater Villa in Maldives</strong>.<br><br><a href="booking.html?suite_id=4" style="color: #c9a227; font-weight: 700; text-decoration: underline;">Reserve Goa Villa &rarr;</a>`;
    }

    if (text.includes('palace') || text.includes('udaipur') || text.includes('rajasthan') || text.includes('heritage')) {
      return `Our flagship <strong>VHotels Palace (Udaipur, Rajasthan)</strong> is an authentic 19th-century fortress overlooking Lake Pichola. Includes royal haveli dining and royal carriage tours.<br><br><a href="booking.html?suite_id=1" style="color: #c9a227; font-weight: 700; text-decoration: underline;">View Rajasthan Palace &rarr;</a>`;
    }

    if (text.includes('kerala') || text.includes('boat') || text.includes('cruiser') || text.includes('ayurvedic')) {
      return `<strong>VHotels Backwaters (Kumarakom, Kerala)</strong> features handcrafted teakwood presidential houseboats gliding through palm-fringed lagoons, accompanied by your private Ayurvedic master chef.<br><br><a href="booking.html?suite_id=3" style="color: #c9a227; font-weight: 700; text-decoration: underline;">View Kerala Cruiser &rarr;</a>`;
    }

    if (text.includes('mumbai') || text.includes('marine drive') || text.includes('penthouse') || text.includes('bay')) {
      return `The <strong>VHotels Bay Penthouse (Marine Drive, Mumbai)</strong> occupies the 45th floor with unobstructed vistas of the Queen's Necklace, private infinity plunge pool, and Rolls-Royce chauffeur service.<br><br><a href="booking.html?suite_id=6" style="color: #c9a227; font-weight: 700; text-decoration: underline;">Reserve Mumbai Penthouse &rarr;</a>`;
    }

    if (text.includes('kashmir') || text.includes('gulmarg') || text.includes('snow') || text.includes('ski')) {
      return `<strong>VHotels Himalayan Pine Chalet (Gulmarg, Kashmir)</strong> offers traditional heated Bukhari fireplaces, ski-in/ski-out gondola access, and private mountain hot tubs.<br><br><a href="booking.html?suite_id=5" style="color: #c9a227; font-weight: 700; text-decoration: underline;">Explore Kashmir Chalet &rarr;</a>`;
    }

    if (text.includes('dining') || text.includes('food') || text.includes('restaurant') || text.includes('chef') || text.includes('breakfast')) {
      return `Every VHotels property features gastronomy curated by Michelin-awarded executive chefs. Enjoy 24/7 in-suite white-glove dining, organic regional farm-to-table breakfast, and private sommelier wine tastings included with your stay.`;
    }

    if (text.includes('transfer') || text.includes('car') || text.includes('airport') || text.includes('limousine') || text.includes('pickup') || text.includes('rolls')) {
      return `We provide private airport chauffeur transfers in our fleet of Rolls-Royce Phantoms and BMW 7-Series. Presidential Suite guests receive complimentary roundtrip airport transfers. Simply select the transfer add-on during booking!`;
    }

    if (text.includes('price') || text.includes('cost') || text.includes('tax') || text.includes('gst') || text.includes('calculation')) {
      return `Our pricing is transparent and all-inclusive: room rates are charged per night with a 18% Luxury Hospitality GST. There are zero hidden booking fees. Full breakdown is computed dynamically before you reserve.`;
    }

    if (text.includes('checkin') || text.includes('check-in') || text.includes('checkout') || text.includes('time') || text.includes('hours')) {
      return `<strong>Check-in:</strong> 14:00 onwards (VIP fast-track greeting).<br><strong>Check-out:</strong> 11:00 am.<br><em>Solitaire Elite members enjoy guaranteed late check-out until 16:00.</em>`;
    }

    if (text.includes('cancel') || text.includes('refund')) {
      return `We understand luxury travel schedules can shift. All direct reservations offer <strong>100% complimentary penalty-free cancellation</strong> up to 48 hours prior to check-in, directly manageable from your profile.`;
    }

    return `It is my distinct pleasure to assist with your stay. You can browse our global collection of sanctuaries on the <a href="suites.html" style="color: #c9a227; font-weight: 700;">Suites Catalog</a> or call our 24/7 Royal Concierge at <strong>+91 (022) 6890-VHOTEL</strong>.`;
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

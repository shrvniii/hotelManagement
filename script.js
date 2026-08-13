document.addEventListener('DOMContentLoaded', () => {
  // ==========================================
  // Navigation & Page Effects
  // ==========================================
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        navbar.classList.add('sticky');
      } else {
        navbar.classList.remove('sticky');
      }
    });
  }

  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const navLinks = document.querySelector('.nav-links');
  
  if (mobileMenuBtn && navLinks) {
    mobileMenuBtn.addEventListener('click', () => {
      navLinks.classList.toggle('active');
      
      const spans = mobileMenuBtn.querySelectorAll('span');
      if (spans.length >= 3) {
        spans[0].style.transform = navLinks.classList.contains('active') 
          ? 'rotate(45deg) translate(5px, 6px)' 
          : 'none';
        spans[1].style.opacity = navLinks.classList.contains('active') 
          ? '0' 
          : '1';
        spans[2].style.transform = navLinks.classList.contains('active') 
          ? 'rotate(-45deg) translate(5px, -6px)' 
          : 'none';
      }
    });
  }

  // Scroll Fade-in Intersection Observer
  const fadeSections = document.querySelectorAll('.fade-in-section');
  if (fadeSections.length > 0) {
    if ('IntersectionObserver' in window) {
      const sectionObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      }, {
        threshold: 0.15,
        rootMargin: "0px 0px -50px 0px"
      });
      
      fadeSections.forEach(section => {
        sectionObserver.observe(section);
      });
    } else {
      fadeSections.forEach(section => section.classList.add('is-visible'));
    }
  }

  // Testimonial Carousel
  const testimonialSlides = document.querySelectorAll('.testimonial-slide');
  const dotsContainer = document.querySelector('.testimonial-dots');
  
  if (testimonialSlides.length > 0 && dotsContainer) {
    let currentSlide = 0;
    let slideInterval;

    testimonialSlides.forEach((_, idx) => {
      const dot = document.createElement('div');
      dot.classList.add('dot');
      if (idx === 0) dot.classList.add('active');
      dot.addEventListener('click', () => {
        goToSlide(idx);
        resetTimer();
      });
      dotsContainer.appendChild(dot);
    });

    const dots = document.querySelectorAll('.dot');

    function goToSlide(n) {
      testimonialSlides[currentSlide].classList.remove('active');
      if (dots[currentSlide]) dots[currentSlide].classList.remove('active');
      currentSlide = (n + testimonialSlides.length) % testimonialSlides.length;
      testimonialSlides[currentSlide].classList.add('active');
      if (dots[currentSlide]) dots[currentSlide].classList.add('active');
    }

    function nextSlide() {
      goToSlide(currentSlide + 1);
    }

    function startTimer() {
      slideInterval = setInterval(nextSlide, 6000);
    }

    function resetTimer() {
      clearInterval(slideInterval);
      startTimer();
    }
    startTimer();
  }

  // Floating Labels Behavior for Forms
  const formInputs = document.querySelectorAll('.form-group input, .form-group textarea');
  formInputs.forEach(input => {
    if (input.value !== '') {
      input.placeholder = ' '; 
    }
    
    input.addEventListener('focus', () => {
      const label = input.parentElement.querySelector('label');
      if (label) label.style.color = '#c9a227';
    });

    input.addEventListener('blur', () => {
      const label = input.parentElement.querySelector('label');
      if (label && input.value === '') {
        label.style.color = 'rgba(255, 255, 255, 0.5)';
      }
    });
  });

  // Password Visibility Toggle
  const togglePasswordBtn = document.querySelector('.toggle-password');
  const passwordInput = document.querySelector('#password');
  
  if (togglePasswordBtn && passwordInput) {
    togglePasswordBtn.addEventListener('click', () => {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      
      const icon = togglePasswordBtn.querySelector('i');
      if (icon) {
        if (type === 'text') {
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        } else {
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      }
    });
  }

  // ==========================================
  // Field Validation Engines & Helpers
  // ==========================================

  // Recognized Top-Level Domains (TLDs) whitelist
  const VALID_TLDS = new Set([
    // Standard & Popular
    'com', 'org', 'net', 'edu', 'gov', 'mil', 'int', 'info', 'biz', 'name', 'pro',
    'coop', 'museum', 'aero', 'jobs', 'mobi', 'travel', 'tel', 'cat', 'asia', 'post',
    // Tech & Modern
    'io', 'co', 'ai', 'app', 'dev', 'tech', 'store', 'online', 'site', 'xyz', 'me',
    'cloud', 'digital', 'global', 'group', 'world', 'life', 'live', 'media', 'news',
    'studio', 'space', 'work', 'today', 'club', 'design', 'email', 'link', 'one',
    'top', 'vip', 'win', 'shop', 'events', 'solutions', 'services', 'agency', 'center',
    'systems', 'zone', 'network', 'company', 'estate', 'hotel', 'resort', 'luxury',
    'boutique', 'cc', 'tv', 'info',
    // Country Codes (ccTLDs)
    'in', 'us', 'uk', 'ca', 'de', 'fr', 'au', 'jp', 'cn', 'eu', 'ru', 'ch', 'nl',
    'se', 'no', 'es', 'it', 'br', 'mx', 'kr', 'za', 'sg', 'hk', 'tw', 'ae', 'sa',
    'nz', 'ie', 'pl', 'at', 'be', 'dk', 'fi', 'gr', 'hu', 'is', 'lu', 'pt', 'ro',
    'sk', 'cz', 'ua', 'ar', 'cl', 'co', 'pe', 've', 'id', 'my', 'ph', 'th', 'vn',
    'pk', 'bd', 'ng', 'eg', 'ke', 'ma', 'tn', 'il', 'tr'
  ]);

  // Common Domain Typos Map for Smart Auto-Suggestion
  const COMMON_DOMAIN_TYPOS = {
    'gmai': 'gmail.com',
    'gmai.com': 'gmail.com',
    'gmial': 'gmail.com',
    'gmial.com': 'gmail.com',
    'gamil': 'gmail.com',
    'gamil.com': 'gmail.com',
    'gmal': 'gmail.com',
    'gmal.com': 'gmail.com',
    'gmail': 'gmail.com',
    'yaho': 'yahoo.com',
    'yaho.com': 'yahoo.com',
    'hotmai': 'hotmail.com',
    'hotmai.com': 'hotmail.com',
    'outloo': 'outlook.com',
    'outloo.com': 'outlook.com',
    'iclou': 'icloud.com',
    'iclou.com': 'icloud.com'
  };

  /**
   * Validates Email Address with strict post-'@' domain whitelist & quality check
   */
  function validateEmailDomain(emailValue) {
    const trimmed = (emailValue || '').trim();
    if (!trimmed) {
      return { valid: false, message: 'Email address is required.' };
    }

    // Must contain exactly one '@'
    const parts = trimmed.split('@');
    if (parts.length !== 2) {
      return { valid: false, message: 'Email must contain exactly one "@" symbol.' };
    }

    const [username, domain] = parts;

    // Validate username (local part)
    if (!username || username.trim() === '') {
      return { valid: false, message: 'Username before "@" cannot be empty.' };
    }
    const usernameRegex = /^[a-zA-Z0-9._%+-]+$/;
    if (!usernameRegex.test(username) || username.startsWith('.') || username.endsWith('.') || username.includes('..')) {
      return { valid: false, message: 'Invalid characters in username before "@".' };
    }

    // Validate domain (post '@' part)
    if (!domain || domain.trim() === '') {
      return { valid: false, message: 'Domain name after "@" cannot be empty.' };
    }

    // Smart Typo Check (e.g. "@gmai" or "@gmai.com")
    const domainLower = domain.toLowerCase().trim();
    if (COMMON_DOMAIN_TYPOS[domainLower]) {
      const suggested = COMMON_DOMAIN_TYPOS[domainLower];
      return { valid: false, message: `Did you mean @${suggested}? Please check domain spelling.` };
    }

    if (!domain.includes('.')) {
      return { valid: false, message: 'Domain after "@" must include a valid extension (e.g. gmail.com).' };
    }

    const domainParts = domain.split('.');
    
    // Check for empty parts (e.g., domain..com or .com or domain.)
    if (domainParts.some(part => part.trim() === '')) {
      return { valid: false, message: 'Domain format after "@" is invalid (check for extra or leading dots).' };
    }

    // Validate Top-Level Domain (TLD) - last part after dot against strict TLD list
    const tld = domainParts[domainParts.length - 1].toLowerCase();
    
    if (!VALID_TLDS.has(tld)) {
      return { 
        valid: false, 
        message: `".${tld}" is not a recognized domain extension. Use a valid domain like .com, .org, .net, .in, .co, or .io.` 
      };
    }

    // Validate domain name labels (all parts before TLD)
    const subdomains = domainParts.slice(0, -1);
    const domainLabelRegex = /^[a-zA-Z0-9-]+$/;
    const vowelRegex = /[aeiouy]/i;

    for (const label of subdomains) {
      if (label.length < 2) {
        return { valid: false, message: 'Domain name label after "@" must be at least 2 characters long (e.g. domain.com).' };
      }
      if (!domainLabelRegex.test(label)) {
        return { valid: false, message: 'Domain name after "@" contains invalid characters.' };
      }
      if (!/[a-zA-Z]/.test(label)) {
        return { valid: false, message: `Domain name "${label}" after "@" must contain alphabetic letters (e.g. gmail.com, vhotels.com).` };
      }
      if (label.startsWith('-') || label.endsWith('-')) {
        return { valid: false, message: 'Domain labels after "@" cannot start or end with a hyphen.' };
      }
      // Quality check: Reject longer pure-letter labels with zero vowels (keyboard mash detection e.g. "cgbhnjk")
      if (label.length > 3 && /^[a-zA-Z]+$/.test(label) && !vowelRegex.test(label)) {
        return { valid: false, message: `Domain name "${label}" appears to be invalid or keyboard gibberish.` };
      }
    }

    return { valid: true, message: '' };
  }

  /**
   * Validates Password strength & length
   */
  function validatePassword(passwordValue) {
    if (!passwordValue) {
      return { valid: false, message: 'Password is required.' };
    }
    if (passwordValue.length < 8) {
      return { valid: false, message: 'Password must be at least 8 characters long.' };
    }
    const hasLetter = /[a-zA-Z]/.test(passwordValue);
    const hasDigitOrSpecial = /[0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(passwordValue);
    if (!hasLetter || !hasDigitOrSpecial) {
      return { valid: false, message: 'Password must contain letters and at least one number or symbol.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * Validates Booking Search Destination
   */
  function validateDestination(destVal) {
    if (!destVal || destVal.trim() === '') {
      return { valid: false, message: 'Please select a hotel property or destination.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * Validates Check-in Date
   */
  function validateCheckin(checkinVal) {
    if (!checkinVal) {
      return { valid: false, message: 'Please select a check-in date.' };
    }
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkinDate = new Date(checkinVal);
    
    if (isNaN(checkinDate.getTime())) {
      return { valid: false, message: 'Invalid check-in date format.' };
    }
    if (checkinDate < today) {
      return { valid: false, message: 'Check-in date cannot be in the past.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * Validates Check-out Date
   */
  function validateCheckout(checkoutVal, checkinVal) {
    if (!checkoutVal) {
      return { valid: false, message: 'Please select a check-out date.' };
    }
    const checkoutDate = new Date(checkoutVal);
    if (isNaN(checkoutDate.getTime())) {
      return { valid: false, message: 'Invalid check-out date format.' };
    }
    if (checkinVal) {
      const checkinDate = new Date(checkinVal);
      if (!isNaN(checkinDate.getTime()) && checkoutDate <= checkinDate) {
        return { valid: false, message: 'Check-out date must be after check-in date.' };
      }
    }
    return { valid: true, message: '' };
  }

  /**
   * Validates Guests Count
   */
  function validateGuests(guestsVal) {
    const num = parseInt(guestsVal, 10);
    if (isNaN(num) || num < 1 || num > 4) {
      return { valid: false, message: 'Please select between 1 and 4 guests.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * UI Field State Helper (adds/removes .is-invalid / .is-valid and updates error text)
   */
  function setFieldState(inputEl, errorEl, result) {
    if (!inputEl) return;
    const wrapper = inputEl.closest('.input-wrapper') || inputEl;

    if (!result.valid) {
      wrapper.classList.add('is-invalid');
      wrapper.classList.remove('is-valid');
      if (errorEl) {
        errorEl.textContent = result.message;
        errorEl.classList.add('visible');
      }
    } else {
      wrapper.classList.remove('is-invalid');
      wrapper.classList.add('is-valid');
      if (errorEl) {
        errorEl.textContent = '';
        errorEl.classList.remove('visible');
      }
    }
  }

  // ==========================================
  // Member Login Form Attachment
  // ==========================================
  const loginForm = document.getElementById('member-login-form');
  const loginEmailInput = document.getElementById('email');
  const loginPasswordInput = document.getElementById('password');
  const loginEmailError = document.getElementById('email-error');
  const loginPasswordError = document.getElementById('password-error');

  if (loginForm && loginEmailInput && loginPasswordInput) {
    // Real-time live check on input/blur
    loginEmailInput.addEventListener('input', () => {
      const res = validateEmailDomain(loginEmailInput.value);
      setFieldState(loginEmailInput, loginEmailError, res);
    });
    loginEmailInput.addEventListener('blur', () => {
      const res = validateEmailDomain(loginEmailInput.value);
      setFieldState(loginEmailInput, loginEmailError, res);
    });

    loginPasswordInput.addEventListener('input', () => {
      const res = validatePassword(loginPasswordInput.value);
      setFieldState(loginPasswordInput, loginPasswordError, res);
    });
    loginPasswordInput.addEventListener('blur', () => {
      const res = validatePassword(loginPasswordInput.value);
      setFieldState(loginPasswordInput, loginPasswordError, res);
    });

    // Form submission validation
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const emailRes = validateEmailDomain(loginEmailInput.value);
      const passRes = validatePassword(loginPasswordInput.value);

      setFieldState(loginEmailInput, loginEmailError, emailRes);
      setFieldState(loginPasswordInput, loginPasswordError, passRes);

      if (emailRes.valid && passRes.valid) {
        const submitBtn = document.getElementById('btn-submit');
        if (submitBtn) {
          submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
          submitBtn.style.pointerEvents = 'none';
        }
        setTimeout(() => {
          alert('Authentication successful! Welcome to the VHotels Member Portal.');
          window.location.href = 'index.html';
        }, 1000);
      }
    });
  }

  // ==========================================
  // Newsletter Form Attachment
  // ==========================================
  const newsletterForm = document.getElementById('newsletter-form');
  const newsletterEmailInput = document.getElementById('newsletter-email');
  const newsletterEmailError = document.getElementById('newsletter-email-error');

  if (newsletterForm && newsletterEmailInput) {
    newsletterEmailInput.addEventListener('input', () => {
      const res = validateEmailDomain(newsletterEmailInput.value);
      setFieldState(newsletterEmailInput, newsletterEmailError, res);
    });
    newsletterEmailInput.addEventListener('blur', () => {
      const res = validateEmailDomain(newsletterEmailInput.value);
      setFieldState(newsletterEmailInput, newsletterEmailError, res);
    });

    newsletterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const emailRes = validateEmailDomain(newsletterEmailInput.value);
      setFieldState(newsletterEmailInput, newsletterEmailError, emailRes);

      if (emailRes.valid) {
        alert('Thank you for subscribing to the VHotels Elite newsletter!');
        newsletterForm.reset();
        if (newsletterEmailInput) {
          const wrapper = newsletterEmailInput.closest('.input-wrapper') || newsletterEmailInput;
          wrapper.classList.remove('is-valid', 'is-invalid');
        }
        if (newsletterEmailError) {
          newsletterEmailError.textContent = '';
          newsletterEmailError.classList.remove('visible');
        }
      }
    });
  }

  // ==========================================
  // Search / Booking Form Attachment
  // ==========================================
  const searchForm = document.getElementById('search-form');
  const destinationSelect = document.getElementById('destination');
  const checkinInput = document.getElementById('checkin');
  const checkoutInput = document.getElementById('checkout');
  const guestsSelect = document.getElementById('guests');
  const searchBtn = document.getElementById('search-btn');

  const destinationError = document.getElementById('destination-error');
  const checkinError = document.getElementById('checkin-error');
  const checkoutError = document.getElementById('checkout-error');
  const guestsError = document.getElementById('guests-error');

  if (checkinInput && checkoutInput) {
    const todayStr = new Date().toISOString().split('T')[0];
    checkinInput.min = todayStr;

    checkinInput.addEventListener('change', () => {
      if (checkinInput.value) {
        const checkinDate = new Date(checkinInput.value);
        checkinDate.setDate(checkinDate.getDate() + 1);
        const minCheckout = checkinDate.toISOString().split('T')[0];
        checkoutInput.min = minCheckout;
        if (checkoutInput.value && checkoutInput.value < minCheckout) {
          checkoutInput.value = minCheckout;
        }
      }
      const checkinRes = validateCheckin(checkinInput.value);
      setFieldState(checkinInput, checkinError, checkinRes);
      if (checkoutInput.value) {
        const checkoutRes = validateCheckout(checkoutInput.value, checkinInput.value);
        setFieldState(checkoutInput, checkoutError, checkoutRes);
      }
    });

    checkoutInput.addEventListener('change', () => {
      const checkoutRes = validateCheckout(checkoutInput.value, checkinInput.value);
      setFieldState(checkoutInput, checkoutError, checkoutRes);
    });
  }

  if (destinationSelect) {
    destinationSelect.addEventListener('change', () => {
      const res = validateDestination(destinationSelect.value);
      setFieldState(destinationSelect, destinationError, res);
    });
  }

  if (guestsSelect) {
    guestsSelect.addEventListener('change', () => {
      const res = validateGuests(guestsSelect.value);
      setFieldState(guestsSelect, guestsError, res);
    });
  }

  if (searchForm && searchBtn) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const destRes = validateDestination(destinationSelect ? destinationSelect.value : '');
      const checkinRes = validateCheckin(checkinInput ? checkinInput.value : '');
      const checkoutRes = validateCheckout(checkoutInput ? checkoutInput.value : '', checkinInput ? checkinInput.value : '');
      const guestsRes = validateGuests(guestsSelect ? guestsSelect.value : '');

      setFieldState(destinationSelect, destinationError, destRes);
      setFieldState(checkinInput, checkinError, checkinRes);
      setFieldState(checkoutInput, checkoutError, checkoutRes);
      setFieldState(guestsSelect, guestsError, guestsRes);

      if (destRes.valid && checkinRes.valid && checkoutRes.valid && guestsRes.valid) {
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Finding Suites...';
        searchBtn.style.pointerEvents = 'none';

        setTimeout(() => {
          alert(`Success! Showing available suites at ${destinationSelect.value} for ${checkinInput.value} to ${checkoutInput.value} (${guestsSelect.value} Guests).`);
          searchBtn.innerHTML = 'Search Suites';
          searchBtn.style.pointerEvents = 'auto';
        }, 1200);
      }
    });
  }

  // ==========================================
  // User Registration Validation Engines
  // ==========================================

  function validateTitle(titleVal) {
    if (!titleVal || titleVal.trim() === '') {
      return { valid: false, message: 'Please select a title.' };
    }
    return { valid: true, message: '' };
  }

  function validateDOB(dobVal) {
    if (!dobVal) {
      return { valid: false, message: 'Please select your date of birth.' };
    }
    const dob = new Date(dobVal);
    const today = new Date();
    if (isNaN(dob.getTime())) {
      return { valid: false, message: 'Invalid date of birth.' };
    }
    if (dob >= today) {
      return { valid: false, message: 'Date of birth must be in the past.' };
    }
    return { valid: true, message: '' };
  }

  function validateResort(resortVal) {
    if (!resortVal || resortVal.trim() === '') {
      return { valid: false, message: 'Please select a preferred resort.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * 1. First Name: contains alphabets only and length not less than 6 characters
   */
  function validateFirstName(nameVal) {
    const trimmed = (nameVal || '').trim();
    if (!trimmed) {
      return { valid: false, message: 'First Name is required.' };
    }
    if (!/^[a-zA-Z]+$/.test(trimmed)) {
      return { valid: false, message: 'First Name must contain alphabets only.' };
    }
    if (trimmed.length < 6) {
      return { valid: false, message: 'First Name length should not be less than 6 characters.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * 2. Password: not less than 6 characters length
   */
  function validateRegPassword(passVal) {
    if (!passVal) {
      return { valid: false, message: 'Password is required.' };
    }
    if (passVal.length < 6) {
      return { valid: false, message: 'Password should not be less than 6 characters length.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * 3. Mobile Number: contains 10 digits only
   */
  function validateMobile(mobileVal) {
    const trimmed = (mobileVal || '').trim();
    if (!trimmed) {
      return { valid: false, message: 'Mobile Number is required.' };
    }
    if (!/^[0-9]{10}$/.test(trimmed)) {
      return { valid: false, message: 'Phone number should contain 10 digits only.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * 4. Last Name: should not be Empty
   */
  function validateLastName(nameVal) {
    const trimmed = (nameVal || '').trim();
    if (!trimmed) {
      return { valid: false, message: 'Last Name should not be empty.' };
    }
    return { valid: true, message: '' };
  }

  /**
   * 5. Address: should not be Empty
   */
  function validateAddress(addrVal) {
    const trimmed = (addrVal || '').trim();
    if (!trimmed) {
      return { valid: false, message: 'Address should not be empty.' };
    }
    return { valid: true, message: '' };
  }

  // ==========================================
  // Registration Form Event Handlers
  // ==========================================
  const regForm = document.getElementById('member-register-form');
  const titleInput = document.getElementById('title');
  const firstNameInput = document.getElementById('first-name');
  const lastNameInput = document.getElementById('last-name');
  const dobInput = document.getElementById('dob');
  const regEmailInput = document.getElementById('reg-email');
  const regPasswordInput = document.getElementById('reg-password');
  const mobileInput = document.getElementById('mobile');
  const resortInput = document.getElementById('preferred-resort');
  const addressInput = document.getElementById('address');

  const titleError = document.getElementById('title-error');
  const firstNameError = document.getElementById('first-name-error');
  const lastNameError = document.getElementById('last-name-error');
  const dobError = document.getElementById('dob-error');
  const regEmailError = document.getElementById('reg-email-error');
  const regPasswordError = document.getElementById('reg-password-error');
  const mobileError = document.getElementById('mobile-error');
  const resortError = document.getElementById('resort-error');
  const addressError = document.getElementById('address-error');

  const regEyeToggle = document.getElementById('reg-eye-toggle');
  if (regEyeToggle && regPasswordInput) {
    regEyeToggle.addEventListener('click', () => {
      const type = regPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      regPasswordInput.setAttribute('type', type);
      const icon = regEyeToggle.querySelector('i');
      if (icon) {
        icon.className = type === 'text' ? 'fas fa-eye-slash' : 'fas fa-eye';
      }
    });
  }

  if (regForm && firstNameInput && lastNameInput && regEmailInput && regPasswordInput && mobileInput && addressInput) {
    if (titleInput) titleInput.addEventListener('change', () => setFieldState(titleInput, titleError, validateTitle(titleInput.value)));
    firstNameInput.addEventListener('input', () => setFieldState(firstNameInput, firstNameError, validateFirstName(firstNameInput.value)));
    lastNameInput.addEventListener('input', () => setFieldState(lastNameInput, lastNameError, validateLastName(lastNameInput.value)));
    if (dobInput) dobInput.addEventListener('change', () => setFieldState(dobInput, dobError, validateDOB(dobInput.value)));
    regEmailInput.addEventListener('input', () => setFieldState(regEmailInput, regEmailError, validateEmailDomain(regEmailInput.value)));
    regPasswordInput.addEventListener('input', () => setFieldState(regPasswordInput, regPasswordError, validateRegPassword(regPasswordInput.value)));
    mobileInput.addEventListener('input', () => setFieldState(mobileInput, mobileError, validateMobile(mobileInput.value)));
    if (resortInput) resortInput.addEventListener('change', () => setFieldState(resortInput, resortError, validateResort(resortInput.value)));
    addressInput.addEventListener('input', () => setFieldState(addressInput, addressError, validateAddress(addressInput.value)));

    // Submit handler
    regForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const titleRes = titleInput ? validateTitle(titleInput.value) : { valid: true };
      const fnRes = validateFirstName(firstNameInput.value);
      const lnRes = validateLastName(lastNameInput.value);
      const dobRes = dobInput ? validateDOB(dobInput.value) : { valid: true };
      const emailRes = validateEmailDomain(regEmailInput.value);
      const passRes = validateRegPassword(regPasswordInput.value);
      const mobRes = validateMobile(mobileInput.value);
      const resortRes = resortInput ? validateResort(resortInput.value) : { valid: true };
      const addrRes = validateAddress(addressInput.value);

      if (titleInput) setFieldState(titleInput, titleError, titleRes);
      setFieldState(firstNameInput, firstNameError, fnRes);
      setFieldState(lastNameInput, lastNameError, lnRes);
      if (dobInput) setFieldState(dobInput, dobError, dobRes);
      setFieldState(regEmailInput, regEmailError, emailRes);
      setFieldState(regPasswordInput, regPasswordError, passRes);
      setFieldState(mobileInput, mobileError, mobRes);
      if (resortInput) setFieldState(resortInput, resortError, resortRes);
      setFieldState(addressInput, addressError, addrRes);

      if (titleRes.valid && fnRes.valid && lnRes.valid && dobRes.valid && emailRes.valid && passRes.valid && mobRes.valid && resortRes.valid && addrRes.valid) {
        const userProfile = {
          title: titleInput ? titleInput.value : '',
          firstName: firstNameInput.value.trim(),
          lastName: lastNameInput.value.trim(),
          dob: dobInput ? dobInput.value : '',
          email: regEmailInput.value.trim(),
          mobile: mobileInput.value.trim(),
          preferredResort: resortInput ? resortInput.value : '',
          address: addressInput.value.trim(),
          registeredAt: new Date().toLocaleDateString()
        };

        localStorage.setItem('vhotels_user_profile', JSON.stringify(userProfile));

        const regBtn = document.getElementById('btn-reg-submit');
        if (regBtn) {
          regBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Profile...';
          regBtn.style.pointerEvents = 'none';
        }

        setTimeout(() => {
          alert(`Registration Successful! Welcome to VHotels, ${userProfile.title ? userProfile.title + ' ' : ''}${userProfile.firstName}.`);
          window.location.href = 'profile.html';
        }, 1000);
      } else {
        // Collect first invalid field and auto-scroll focus to it
        const checks = [
          { res: titleRes, el: titleInput },
          { res: fnRes, el: firstNameInput },
          { res: lnRes, el: lastNameInput },
          { res: dobRes, el: dobInput },
          { res: emailRes, el: regEmailInput },
          { res: passRes, el: regPasswordInput },
          { res: mobRes, el: mobileInput },
          { res: resortRes, el: resortInput },
          { res: addrRes, el: addressInput }
        ];

        const invalidItem = checks.find(c => c.res && !c.res.valid);
        if (invalidItem && invalidItem.el) {
          invalidItem.el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          invalidItem.el.focus();
        }
      }
    });
  }

  // ==========================================
  // Member Profile & Edit Profile Modal Logic
  // ==========================================
  const profileContainer = document.getElementById('profile-container');
  const editModal = document.getElementById('edit-profile-modal');
  const openEditBtn = document.getElementById('btn-open-edit-modal');
  const closeEditBtn = document.getElementById('btn-close-edit-modal');
  const cancelEditBtn = document.getElementById('btn-cancel-edit');
  const editForm = document.getElementById('edit-profile-form');

  const editTitleInput = document.getElementById('edit-title');
  const editFirstNameInput = document.getElementById('edit-first-name');
  const editLastNameInput = document.getElementById('edit-last-name');
  const editDOBInput = document.getElementById('edit-dob');
  const editEmailInput = document.getElementById('edit-email');
  const editMobileInput = document.getElementById('edit-mobile');
  const editResortInput = document.getElementById('edit-resort');
  const editAddressInput = document.getElementById('edit-address');

  const editTitleError = document.getElementById('edit-title-error');
  const editFirstNameError = document.getElementById('edit-first-name-error');
  const editLastNameError = document.getElementById('edit-last-name-error');
  const editDOBError = document.getElementById('edit-dob-error');
  const editEmailError = document.getElementById('edit-email-error');
  const editMobileError = document.getElementById('edit-mobile-error');
  const editResortError = document.getElementById('edit-resort-error');
  const editAddressError = document.getElementById('edit-address-error');

  function populateProfileDisplay(user) {
    const fullNameEl = document.getElementById('profile-full-name');
    const emailEl = document.getElementById('profile-email');
    const dispTitle = document.getElementById('disp-title');
    const dispFirstName = document.getElementById('disp-first-name');
    const dispLastName = document.getElementById('disp-last-name');
    const dispDOB = document.getElementById('disp-dob');
    const dispEmail = document.getElementById('disp-email');
    const dispMobile = document.getElementById('disp-mobile');
    const dispResort = document.getElementById('disp-resort');
    const dispAddress = document.getElementById('disp-address');

    if (fullNameEl) fullNameEl.textContent = `${user.title ? user.title + ' ' : ''}${user.firstName} ${user.lastName}`;
    if (emailEl) emailEl.textContent = user.email;
    if (dispTitle) dispTitle.textContent = user.title || '-';
    if (dispFirstName) dispFirstName.textContent = user.firstName;
    if (dispLastName) dispLastName.textContent = user.lastName;
    if (dispDOB) dispDOB.textContent = user.dob || '-';
    if (dispEmail) dispEmail.textContent = user.email;
    if (dispMobile) dispMobile.textContent = user.mobile;
    if (dispResort) dispResort.textContent = user.preferredResort || '-';
    if (dispAddress) dispAddress.textContent = user.address;
  }

  function renderProfileFromStorage() {
    const storedProfile = localStorage.getItem('vhotels_user_profile');
    if (storedProfile) {
      try {
        const user = JSON.parse(storedProfile);
        populateProfileDisplay(user);
      } catch (err) {
        console.error('Error parsing profile data', err);
      }
    }
  }

  if (profileContainer) {
    renderProfileFromStorage();
  }

  function openEditModal() {
    if (!editModal) return;
    const stored = localStorage.getItem('vhotels_user_profile');
    let user = { title: 'Mr.', firstName: '', lastName: '', dob: '', email: '', mobile: '', preferredResort: '', address: '' };
    if (stored) {
      try { user = JSON.parse(stored); } catch (e) {}
    }

    if (editTitleInput) editTitleInput.value = user.title || 'Mr.';
    if (editFirstNameInput) editFirstNameInput.value = user.firstName || '';
    if (editLastNameInput) editLastNameInput.value = user.lastName || '';
    if (editDOBInput) editDOBInput.value = user.dob || '';
    if (editEmailInput) editEmailInput.value = user.email || '';
    if (editMobileInput) editMobileInput.value = user.mobile || '';
    if (editResortInput) editResortInput.value = user.preferredResort || '';
    if (editAddressInput) editAddressInput.value = user.address || '';

    // Clear previous validation error states
    [editTitleInput, editFirstNameInput, editLastNameInput, editDOBInput, editEmailInput, editMobileInput, editResortInput, editAddressInput].forEach(inp => {
      if (inp) {
        const wrapper = inp.closest('.input-wrapper') || inp;
        wrapper.classList.remove('is-invalid', 'is-valid');
      }
    });
    [editTitleError, editFirstNameError, editLastNameError, editDOBError, editEmailError, editMobileError, editResortError, editAddressError].forEach(err => {
      if (err) { err.textContent = ''; err.classList.remove('visible'); }
    });

    editModal.classList.add('active');
  }

  function closeEditModal() {
    if (editModal) editModal.classList.remove('active');
  }

  if (openEditBtn) openEditBtn.addEventListener('click', openEditModal);
  if (closeEditBtn) closeEditBtn.addEventListener('click', closeEditModal);
  if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEditModal);

  if (editForm && editFirstNameInput && editLastNameInput && editEmailInput && editMobileInput && editAddressInput) {
    if (editTitleInput) editTitleInput.addEventListener('change', () => setFieldState(editTitleInput, editTitleError, validateTitle(editTitleInput.value)));
    editFirstNameInput.addEventListener('input', () => setFieldState(editFirstNameInput, editFirstNameError, validateFirstName(editFirstNameInput.value)));
    editLastNameInput.addEventListener('input', () => setFieldState(editLastNameInput, editLastNameError, validateLastName(editLastNameInput.value)));
    if (editDOBInput) editDOBInput.addEventListener('change', () => setFieldState(editDOBInput, editDOBError, validateDOB(editDOBInput.value)));
    editEmailInput.addEventListener('input', () => setFieldState(editEmailInput, editEmailError, validateEmailDomain(editEmailInput.value)));
    editMobileInput.addEventListener('input', () => setFieldState(editMobileInput, editMobileError, validateMobile(editMobileInput.value)));
    if (editResortInput) editResortInput.addEventListener('change', () => setFieldState(editResortInput, editResortError, validateResort(editResortInput.value)));
    editAddressInput.addEventListener('input', () => setFieldState(editAddressInput, editAddressError, validateAddress(editAddressInput.value)));

    editForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const titleRes = editTitleInput ? validateTitle(editTitleInput.value) : { valid: true };
      const fnRes = validateFirstName(editFirstNameInput.value);
      const lnRes = validateLastName(editLastNameInput.value);
      const dobRes = editDOBInput ? validateDOB(editDOBInput.value) : { valid: true };
      const emailRes = validateEmailDomain(editEmailInput.value);
      const mobRes = validateMobile(editMobileInput.value);
      const resortRes = editResortInput ? validateResort(editResortInput.value) : { valid: true };
      const addrRes = validateAddress(editAddressInput.value);

      if (editTitleInput) setFieldState(editTitleInput, editTitleError, titleRes);
      setFieldState(editFirstNameInput, editFirstNameError, fnRes);
      setFieldState(editLastNameInput, editLastNameError, lnRes);
      if (editDOBInput) setFieldState(editDOBInput, editDOBError, dobRes);
      setFieldState(editEmailInput, editEmailError, emailRes);
      setFieldState(editMobileInput, editMobileError, mobRes);
      if (editResortInput) setFieldState(editResortInput, editResortError, resortRes);
      setFieldState(editAddressInput, editAddressError, addrRes);

      if (titleRes.valid && fnRes.valid && lnRes.valid && dobRes.valid && emailRes.valid && mobRes.valid && resortRes.valid && addrRes.valid) {
        const updatedUser = {
          title: editTitleInput ? editTitleInput.value : '',
          firstName: editFirstNameInput.value.trim(),
          lastName: editLastNameInput.value.trim(),
          dob: editDOBInput ? editDOBInput.value : '',
          email: editEmailInput.value.trim(),
          mobile: editMobileInput.value.trim(),
          preferredResort: editResortInput ? editResortInput.value : '',
          address: editAddressInput.value.trim(),
          updatedAt: new Date().toLocaleDateString()
        };

        localStorage.setItem('vhotels_user_profile', JSON.stringify(updatedUser));
        populateProfileDisplay(updatedUser);
        closeEditModal();
        alert('Member profile successfully updated!');
      }
    });
  }

  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      localStorage.removeItem('vhotels_user_profile');
      alert('You have logged out of your VHotels profile.');
      window.location.href = 'index.html';
    });
  }
});

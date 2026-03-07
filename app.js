/* app.js — AIRT AI Red Team Academy interactions */

(function() {
  'use strict';

  /* ========================================
     THEME TOGGLE
     ======================================== */
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const root = document.documentElement;
  let theme = 'dark'; // Default to dark for security course
  root.setAttribute('data-theme', theme);

  function updateToggleIcon() {
    if (!themeToggle) return;
    themeToggle.setAttribute('aria-label',
      'Switch to ' + (theme === 'dark' ? 'light' : 'dark') + ' mode'
    );
    themeToggle.innerHTML = theme === 'dark'
      ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
      : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }

  updateToggleIcon();

  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      theme = theme === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', theme);
      updateToggleIcon();
    });
  }

  /* ========================================
     HEADER SCROLL BEHAVIOR
     ======================================== */
  const header = document.querySelector('.header');
  if (header) {
    let lastScrollY = 0;
    window.addEventListener('scroll', function() {
      const currentScrollY = window.scrollY;
      if (currentScrollY > 60) {
        header.classList.add('header--scrolled');
      } else {
        header.classList.remove('header--scrolled');
      }
      lastScrollY = currentScrollY;
    }, { passive: true });
  }

  /* ========================================
     MOBILE MENU
     ======================================== */
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const headerNav = document.querySelector('.header__nav');

  if (mobileMenuBtn && headerNav) {
    mobileMenuBtn.addEventListener('click', function() {
      const isOpen = headerNav.classList.toggle('open');
      mobileMenuBtn.setAttribute('aria-expanded', isOpen);
      mobileMenuBtn.innerHTML = isOpen
        ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>'
        : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
    });

    // Close mobile menu on link click
    headerNav.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        headerNav.classList.remove('open');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        mobileMenuBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
      });
    });
  }

  /* ========================================
     SMOOTH SCROLLING FOR NAV LINKS
     ======================================== */
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
        // Update URL hash without jump
        if (window.history && window.history.pushState) {
          window.history.pushState(null, null, targetId);
        }
      }
    });
  });

  /* ========================================
     ACTIVE NAV TRACKING
     ======================================== */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.header__nav a');

  function updateActiveNav() {
    const scrollY = window.scrollY + 120;
    let currentSection = '';

    sections.forEach(function(section) {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      if (scrollY >= top && scrollY < top + height) {
        currentSection = section.getAttribute('id');
      }
    });

    navLinks.forEach(function(link) {
      link.classList.remove('active');
      if (link.getAttribute('href') === '#' + currentSection) {
        link.classList.add('active');
      }
    });
  }

  window.addEventListener('scroll', updateActiveNav, { passive: true });
  updateActiveNav();

  /* ========================================
     MODULE EXPAND/COLLAPSE
     ======================================== */
  document.querySelectorAll('.module-card__header').forEach(function(headerBtn) {
    headerBtn.addEventListener('click', function(e) {
      // Don't toggle if clicking the Read Module link
      if (e.target.closest('.module-card__read-link')) return;

      var card = this.closest('.module-card');
      var isOpen = card.classList.contains('is-open');

      // Toggle this card
      card.classList.toggle('is-open');

      // Update aria
      this.setAttribute('aria-expanded', !isOpen);
    });
  });

  /* ========================================
     TERMINAL TYPING ANIMATION
     ======================================== */
  function animateTerminal() {
    var lines = document.querySelectorAll('.terminal-line');
    lines.forEach(function(line, index) {
      line.style.animationDelay = (index * 0.4) + 's';
    });
  }

  // Only animate when hero is visible
  var heroTerminal = document.querySelector('.hero__terminal');
  if (heroTerminal) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          animateTerminal();
          observer.disconnect();
        }
      });
    }, { threshold: 0.3 });
    observer.observe(heroTerminal);
  }

  /* ========================================
     SCROLL REVEAL FALLBACK
     (for browsers without scroll-driven animations)
     ======================================== */
  if (!CSS.supports || !CSS.supports('animation-timeline', 'scroll()')) {
    var revealElements = document.querySelectorAll('.fade-in, .reveal-up');
    if (revealElements.length > 0) {
      var revealObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.clipPath = 'none';
            revealObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

      revealElements.forEach(function(el) {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), clip-path 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
        revealObserver.observe(el);
      });
    }
  }

})();

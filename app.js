/* app.js — AIRT AI 红队学院交互脚本 */

(function() {
  'use strict';

  /* ========================================
     主题切换
     ======================================== */
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const root = document.documentElement;
  let theme = 'dark'; // 安全课程默认使用暗色主题
  root.setAttribute('data-theme', theme);

  function updateToggleIcon() {
    if (!themeToggle) return;
    themeToggle.setAttribute('aria-label',
      '切换到' + (theme === 'dark' ? '浅色' : '暗色') + '模式'
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
     头部滚动行为
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
     移动端菜单
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

    // 点击链接时关闭移动端菜单
    headerNav.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        headerNav.classList.remove('open');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        mobileMenuBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
      });
    });
  }

  /* ========================================
     导航链接平滑滚动
     ======================================== */
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
        // 更新 URL 哈希但不跳转
        if (window.history && window.history.pushState) {
          window.history.pushState(null, null, targetId);
        }
      }
    });
  });

  /* ========================================
     活动导航追踪
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
     模块展开/折叠
     ======================================== */
  document.querySelectorAll('.module-card__header').forEach(function(headerBtn) {
    headerBtn.addEventListener('click', function(e) {
      // 如果点击的是"阅读模块"链接，则不切换
      if (e.target.closest('.module-card__read-link')) return;

      var card = this.closest('.module-card');
      var isOpen = card.classList.contains('is-open');

      // 切换此卡片
      card.classList.toggle('is-open');

      // 更新 aria 属性
      this.setAttribute('aria-expanded', !isOpen);
    });
  });

  /* ========================================
     终端打字动画
     ======================================== */
  function animateTerminal() {
    var lines = document.querySelectorAll('.terminal-line');
    lines.forEach(function(line, index) {
      line.style.animationDelay = (index * 0.4) + 's';
    });
  }

  // 仅在 hero 区域可见时播放动画
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
     滚动显示回退方案
     （用于不支持滚动驱动动画的浏览器）
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

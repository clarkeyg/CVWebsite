// George Clarke's CV / portfolio
// Nav state, mobile menu, scroll progress, active-link highlight, scroll reveals.

document.addEventListener('DOMContentLoaded', () => {
  const nav      = document.querySelector('.nav');
  const burger   = document.querySelector('.nav-burger');
  const navLinks = document.querySelector('.nav-links');
  const progress = document.querySelector('.progress');
  const links    = [...document.querySelectorAll('.nav-links a[href^="#"]')];
  const sections = links
    .map(a => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);

  /* ---- Mobile menu -------------------------------------------------- */
  if (burger && navLinks) {
    const toggle = (open) => {
      navLinks.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', String(open));
    };
    burger.addEventListener('click', () => toggle(!navLinks.classList.contains('open')));
    navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => toggle(false)));
  }

  /* ---- Scroll-driven UI (batched in one rAF) ----------------------- */
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;

    if (nav) nav.classList.toggle('scrolled', y > 40);

    if (progress) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (h > 0 ? (y / h) * 100 : 0) + '%';
    }

    // Highlight the nav link for the section currently in view.
    let current = '';
    for (const sec of sections) {
      if (sec.getBoundingClientRect().top <= 120) current = '#' + sec.id;
    }
    links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === current));

    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();

  /* ---- Scroll reveals ---------------------------------------------- */
  const revealEls = [...document.querySelectorAll('.reveal')];

  // Stagger children of any [data-stagger] container.
  document.querySelectorAll('[data-stagger]').forEach(group => {
    group.querySelectorAll('.reveal').forEach((el, i) => {
      el.style.transitionDelay = (i * 70) + 'ms';
    });
  });

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced || !('IntersectionObserver' in window)) {
    revealEls.forEach(el => el.classList.add('in'));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => io.observe(el));
  }
});

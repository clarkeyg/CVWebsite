// George Clarke's CV / portfolio — "Nebula"
// Canvas constellation, scroll reveals, magnetic buttons, nav + progress,
// count-ups, card glow, hero parallax, and a pinned horizontal experience rail.

document.addEventListener('DOMContentLoaded', () => {
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $  = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const pad = (n) => String(n).padStart(2, '0');

  /* ---- Hero constellation canvas ----------------------------------- */
  (function initCanvas() {
    const cv = document.getElementById('nb-canvas');
    if (!cv) return;
    const ctx = cv.getContext('2d');
    let W, H, raf;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const mouse = { x: -9999, y: -9999, on: false };

    const resize = () => {
      const r = cv.getBoundingClientRect();
      W = r.width; H = r.height;
      cv.width = W * dpr; cv.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', (e) => {
      const r = cv.getBoundingClientRect();
      mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
      mouse.on = mouse.y > 0 && mouse.y < H;
    }, { passive: true });

    const colors = ['34,211,238', '139,92,246', '244,114,182'];
    const LINES = 22;
    const draw = (t) => {
      ctx.clearRect(0, 0, W, H);
      for (let i = 0; i < LINES; i++) {
        const p = i / (LINES - 1);
        const baseY = H * 0.1 + p * H * 0.8;
        const col = colors[i % 3];
        const amp = 16 + 16 * Math.sin(i * 0.7);
        ctx.beginPath();
        for (let x = 0; x <= W + 14; x += 14) {
          const k = x / W;
          let y = baseY
            + Math.sin(k * 5 + t * 1.1 + i * 0.45) * amp
            + Math.sin(k * 11 - t * 0.8 + i * 0.9) * 9
            + Math.cos(k * 2.3 + t * 0.5) * 14;
          if (mouse.on) {
            const gx = Math.exp(-((x - mouse.x) ** 2) / (2 * 150 * 150));
            const gy = Math.exp(-((baseY - mouse.y) ** 2) / (2 * 230 * 230));
            y += gx * gy * (mouse.y - baseY) * 0.55;
          }
          if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = `rgba(${col},${0.08 + 0.09 * (0.5 + 0.5 * Math.sin(t * 0.8 + i))})`;
        ctx.lineWidth = 1.4;
        ctx.stroke();
      }
    };

    if (reduce) { draw(0.6); return; }
    let t = 0;
    const tick = () => { t += 0.006; draw(t); raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
  })();

  /* ---- Scroll reveals ---------------------------------------------- */
  (function initReveals() {
    const els = $$('.reveal');
    if (reduce || !('IntersectionObserver' in window)) { els.forEach(el => el.classList.add('in')); return; }
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.style.transitionDelay = (e.target.getAttribute('data-delay') || 0) + 'ms';
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -7% 0px' });
    els.forEach(el => io.observe(el));
  })();

  /* ---- Magnetic buttons -------------------------------------------- */
  if (!reduce) $$('[data-magnetic]').forEach(el => {
    el.addEventListener('mousemove', (e) => {
      const r = el.getBoundingClientRect();
      const x = e.clientX - r.left - r.width / 2;
      const y = e.clientY - r.top - r.height / 2;
      el.style.transform = `translate(${x * 0.18}px, ${y * 0.26}px)`;
    });
    el.addEventListener('mouseleave', () => { el.style.transform = 'translate(0,0)'; });
  });

  /* ---- Count-ups --------------------------------------------------- */
  (function initCounts() {
    const counters = $$('.count[data-to]');
    if (reduce || !('IntersectionObserver' in window)) { counters.forEach(el => el.textContent = el.dataset.to); return; }
    const run = (el) => {
      const to = parseInt(el.dataset.to, 10), dur = 1200, start = performance.now();
      const step = (now) => {
        const p = Math.min((now - start) / dur, 1);
        el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * to);
        if (p < 1) requestAnimationFrame(step); else el.textContent = to;
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { run(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.6 });
    counters.forEach(el => io.observe(el));
  })();

  /* ---- Project-card cursor glow ------------------------------------ */
  if (!reduce) $$('[data-card]').forEach(card => {
    const glow = $('.glow', card);
    if (!glow) return;
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      glow.style.left = (e.clientX - r.left) + 'px';
      glow.style.top = (e.clientY - r.top) + 'px';
    });
  });

  /* ---- Pinned horizontal experience rail --------------------------- */
  const pinSection = $('[data-pin-section]');
  const track = $('[data-track]');
  const pinProgress = $('[data-pin-progress]');
  let pinDist = 0, pinOn = false;

  const setupPin = () => {
    if (!pinSection || !track) return;
    const canPin = !reduce && window.innerWidth >= 900;
    if (canPin && !pinOn) { pinSection.classList.add('pin-active'); pinOn = true; }
    else if (!canPin && pinOn) {
      pinSection.classList.remove('pin-active');
      pinSection.style.height = ''; track.style.transform = ''; pinOn = false;
    }
    if (pinOn) {
      pinDist = Math.max(0, track.scrollWidth - window.innerWidth + 80);
      pinSection.style.height = (window.innerHeight + pinDist * 1.05) + 'px';
    }
  };
  const updatePin = () => {
    if (!pinOn) return;
    const total = pinSection.offsetHeight - window.innerHeight;
    const p = Math.min(Math.max(-pinSection.getBoundingClientRect().top / total, 0), 1);
    track.style.transform = `translateX(${-pinDist * p}px)`;
    if (pinProgress) {
      const cards = track.children.length;
      pinProgress.textContent = pad(Math.min(cards, Math.floor(p * cards) + 1)) + ' / ' + pad(cards);
    }
  };
  setupPin();
  window.addEventListener('resize', setupPin);

  /* ---- Hero parallax ----------------------------------------------- */
  const hero = $('[data-herocontent]');
  const aurora = $('[data-aurora]');

  /* ---- Nav, progress bar, scroll-spy (one batched handler) --------- */
  const nav = $('.nav');
  const progress = $('.progress');
  const navLinks = $$('.nav-links a[href^="#"]');
  const sections = navLinks.map(a => $(a.getAttribute('href'))).filter(Boolean);

  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY || 0;
    const h = document.documentElement.scrollHeight - window.innerHeight;

    if (progress) progress.style.width = (h > 0 ? (y / h) * 100 : 0) + '%';
    if (nav) nav.classList.toggle('scrolled', y > 30);

    if (!reduce && y < window.innerHeight * 1.2) {
      if (hero) {
        hero.style.transform = `translateY(${y * 0.26}px)`;
        hero.style.opacity = String(Math.max(0, 1 - y / (window.innerHeight * 0.78)));
      }
      if (aurora) aurora.style.transform = `translateY(${y * 0.12}px)`;
    }

    updatePin();

    let cur = '';
    for (const s of sections) { if (s.getBoundingClientRect().top <= 120) cur = '#' + s.id; }
    navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === cur));

    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();
});

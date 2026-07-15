/* ============================================================================
   main.js — theme toggle, animated hero field, scroll-reveal, small helpers.
   Vanilla JS, no dependencies.
   ========================================================================== */
(function () {
  "use strict";

  /* ---------- theme toggle (persisted) ---------- */
  const root = document.documentElement;
  const saved = localStorage.getItem("goc-theme");
  if (saved) root.setAttribute("data-theme", saved);
  const btn = document.getElementById("themeBtn");
  if (btn) btn.addEventListener("click", function () {
    const cur = root.getAttribute("data-theme") ||
      (matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light");
    const next = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("goc-theme", next);
    window.dispatchEvent(new CustomEvent("themechange"));
  });

  /* ---------- animated "poleward displacement" hero field ---------- */
  const c = document.getElementById("field");
  if (c) {
    const ctx = c.getContext("2d");
    let W, H, parts = [];
    const reduce = matchMedia("(prefers-reduced-motion:reduce)").matches;
    function inkRGBA() {
      const d = root.getAttribute("data-theme") ||
        (matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light");
      return d === "dark" ? "rgba(224,122,74," : "rgba(200,90,43,";
    }
    function size() {
      W = c.width = c.offsetWidth; H = c.height = c.offsetHeight;
      parts = [];
      const n = Math.min(150, Math.floor(W * H / 9000));
      for (let i = 0; i < n; i++)
        parts.push({ x: Math.random() * W, y: Math.random() * H,
          s: 0.2 + Math.random() * 0.7, len: 8 + Math.random() * 22 });
    }
    function step() {
      ctx.clearRect(0, 0, W, H);
      const col = inkRGBA();
      for (const p of parts) {
        const vx = Math.sin((p.y + p.x) * 0.004) * 0.35, vy = -(0.5 + p.s);
        ctx.strokeStyle = col + (0.10 + p.s * 0.18) + ")";
        ctx.lineWidth = p.s * 1.1;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - vx * p.len, p.y - vy * p.len * 0.1 + p.len);
        ctx.stroke();
        p.x += vx; p.y += vy;
        if (p.y < -20) { p.y = H + 10; p.x = Math.random() * W; }
        if (p.x < 0) p.x += W; if (p.x > W) p.x -= W;
      }
      if (!reduce) requestAnimationFrame(step);
    }
    size(); window.addEventListener("resize", size);
    step();
  }

  /* ---------- scroll reveal ---------- */
  const io = new IntersectionObserver(function (entries) {
    for (const e of entries) if (e.isIntersecting) {
      e.target.classList.add("in"); io.unobserve(e.target);
    }
  }, { threshold: 0.08 });
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));

  /* ---------- shared tooltip helper (exposed globally) ---------- */
  const tip = document.getElementById("tooltip");
  window.GOC = window.GOC || {};
  window.GOC.tip = {
    show(html, x, y) {
      tip.innerHTML = html;
      tip.style.opacity = "1";
      const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
      let left = x + pad, top = y + pad;
      if (left + w > innerWidth) left = x - w - pad;
      if (top + h > innerHeight) top = y - h - pad;
      tip.style.left = left + "px"; tip.style.top = top + "px";
    },
    hide() { tip.style.opacity = "0"; }
  };
  window.GOC.cssVar = name =>
    getComputedStyle(root).getPropertyValue(name).trim();

  /* ---------- interactive pipeline strip (rephrases Fig 1c's pipeline) ---------- */
  (function () {
    const strip = document.getElementById("pipeStrip");
    if (!strip) return;
    const desc = document.getElementById("pipeDesc");
    const nodes = [...strip.querySelectorAll(".pipe-node")];
    const TEXT = [
      "We begin with 57,838 open-access GBIF observations, representing presence-only records for seven conflict-prone mammal species across Europe.",
      "Using these observations, we built our habitat models from scratch using a maximum entropy approach, implemented through its mathematically equivalent formulation as a penalized Poisson point process. These models allow us to generate habitat suitability maps for both present-day and future climate conditions.",
      "We then use entropic optimal transport to model how species redistribute as their habitats shift under climate change. This produces a displacement field that estimates where populations are likely to move, as well as a measure of Coexistence Friction, which captures the difficulty of moving through areas with increasing human pressure.",
      "Next, we identify the routes wildlife is most likely to take during this redistribution process. Spectral circuit theory highlights important movement corridors and bottlenecks, while persistent homology measures how habitats become fragmented or remain connected over time.",
      "Finally, we combine these geometric signals into a single Coexistence Risk Index that estimates where interactions between wildlife and people are most likely to occur. We then evaluate these predictions using independent datasets that were never seen during model development."
    ];
    let cur = -1, t = null;
    function set(i) {
      if (i === cur) return; cur = i;
      nodes.forEach((n, k) => n.classList.toggle("active", k === i));
      desc.style.opacity = "0"; clearTimeout(t);
      t = setTimeout(() => { desc.textContent = TEXT[i]; desc.style.opacity = "1"; }, 120);
    }
    nodes.forEach((n, i) => {
      n.addEventListener("mouseenter", () => set(i));
      n.addEventListener("focus", () => set(i));
      n.addEventListener("click", () => set(i));
    });
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { if (cur === -1) set(0); io.disconnect(); }
    }), { threshold: 0.4 });
    io.observe(strip);
  })();

  /* ---------- stat-band count-up on scroll ---------- */
  (function () {
    const band = document.getElementById("statBand");
    if (!band) return;
    const reduce = matchMedia("(prefers-reduced-motion:reduce)").matches;
    const render = (el, val) => {
      const dec = +el.dataset.dec || 0, suf = el.dataset.suffix || "";
      el.innerHTML = val.toFixed(dec) + (suf ? `<small>${suf}</small>` : "");
    };
    function run(el) {
      const target = +el.dataset.count, dur = 1100, t0 = performance.now();
      if (reduce) { render(el, target); return; }
      (function frame(now) {
        const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3);
        render(el, target * e);
        if (p < 1) requestAnimationFrame(frame); else render(el, target);
      })(t0);
    }
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { run(e.target); io.unobserve(e.target); }
    }), { threshold: 0.6 });
    const nums = [...band.querySelectorAll(".n[data-count]")];
    if (!reduce) nums.forEach(el => render(el, 0));   // start at 0 → no flash of the final value
    nums.forEach(n => io.observe(n));
  })();

  /* ---------- nav scrollspy (highlight the section you're reading) ---------- */
  (function () {
    const map = {}, sections = [];
    document.querySelectorAll(".nav a.navlink").forEach(a => {
      const id = (a.getAttribute("href") || "").slice(1);
      const s = id && document.getElementById(id);
      if (s) { map[id] = a; sections.push(s); }
    });
    if (!sections.length) return;
    let active = null;
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) {
        if (active) active.classList.remove("active");
        active = map[e.target.id];
        if (active) active.classList.add("active");
      }
    }), { rootMargin: "-45% 0px -50% 0px", threshold: 0 });
    sections.forEach(s => io.observe(s));
  })();
})();

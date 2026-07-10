/* ============================================================================
   maps.js — interactive present ↔ 2090 habitat-suitability viewer.
   Drag the divider to wipe; hover to read the (real) coarse suitability grid.
   ========================================================================== */
(function () {
  "use strict";
  const tip = window.GOC.tip;
  const b64ToU8 = s => { const b = atob(s); const a = new Uint8Array(b.length);
    for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; };

  fetch("assets/data/sdm_grids.json").then(r => r.json()).then(setup)
    .catch(err => console.error("sdm grids load failed", err));

  function setup(grids) {
    const [gh, gw] = grids.coarse_shape;
    const mask = b64ToU8(grids.mask);
    const stage = document.getElementById("sdmStage");
    const imgP = document.getElementById("sdmPresent");
    const imgF = document.getElementById("sdmFuture");
    const divider = document.getElementById("sdmDivider");
    const chips = document.getElementById("sdmChips");
    const readout = document.getElementById("sdmReadout");
    const cap = document.getElementById("sdmCap");
    const title = document.getElementById("sdmTitle");
    let cur = null, gp = null, gfu = null, wipe = 50;

    function fname(key, epoch) { return `assets/img/sdm/${key.replace(/ /g, "_")}_${epoch}.png`; }

    function select(sp) {
      cur = sp;
      gp = b64ToU8(grids.species[sp.key].present);
      gfu = b64ToU8(grids.species[sp.key].future);
      imgP.src = fname(sp.key, "present");
      imgF.src = fname(sp.key, "future");
      title.textContent = `Interactive · ${sp.common} — habitat today ↔ 2090`;
      cap.innerHTML = `Climate forces <b>${sp.common}</b> habitat <b>${sp.W_km} km</b> poleward by 2090 (SSP2-4.5). Bright = more suitable; the two epochs share the same colour scale so the retreat is comparable.`;
      chips.querySelectorAll(".chip").forEach(c =>
        c.setAttribute("aria-pressed", String(c.dataset.key === sp.key)));
      readout.textContent = "Hover the map to read habitat suitability.";
    }

    function setWipe(pct) {
      wipe = Math.max(0, Math.min(100, pct));
      stage.style.setProperty("--wipe", wipe + "%");
      divider.setAttribute("aria-valuenow", Math.round(wipe));
    }

    /* ----- divider drag (mouse + touch + keyboard) ----- */
    function dragTo(clientX) {
      const r = stage.getBoundingClientRect();
      setWipe((clientX - r.left) / r.width * 100);
    }
    let dragging = false;
    divider.addEventListener("mousedown", e => { dragging = true; e.preventDefault(); });
    window.addEventListener("mousemove", e => { if (dragging) dragTo(e.clientX); });
    window.addEventListener("mouseup", () => dragging = false);
    divider.addEventListener("touchstart", e => { dragging = true; }, { passive: true });
    window.addEventListener("touchmove", e => { if (dragging && e.touches[0]) dragTo(e.touches[0].clientX); }, { passive: true });
    window.addEventListener("touchend", () => dragging = false);
    divider.addEventListener("keydown", e => {
      if (e.key === "ArrowLeft") { setWipe(wipe - 4); e.preventDefault(); }
      if (e.key === "ArrowRight") { setWipe(wipe + 4); e.preventDefault(); }
    });

    /* ----- hover readout from the real coarse grid ----- */
    function readAt(clientX, clientY) {
      const r = stage.getBoundingClientRect();
      const fx = (clientX - r.left) / r.width, fy = (clientY - r.top) / r.height;
      if (fx < 0 || fx > 1 || fy < 0 || fy > 1) return;
      const col = Math.min(gw - 1, Math.floor(fx * gw));
      const row = Math.min(gh - 1, Math.floor(fy * gh));
      const idx = row * gw + col;
      if (!mask[idx]) { readout.textContent = "— sea / outside study area —"; tip.hide(); return; }
      const epoch = (fx * 100 < wipe) ? "present" : "2090";
      const val = (epoch === "present" ? gp[idx] : gfu[idx]);
      const other = (epoch === "present" ? gfu[idx] : gp[idx]);
      const delta = gfu[idx] - gp[idx];
      const arrow = delta > 4 ? "▲ gains" : delta < -4 ? "▼ loses" : "≈ stable";
      readout.innerHTML = `<b>${cur.common}</b> · ${epoch}: suitability <b>${val}%</b> &nbsp;·&nbsp; this cell ${arrow} by 2090 (${delta > 0 ? "+" : ""}${delta}%)`;
      tip.show(`<span class="tt-t">${cur.common} · ${epoch}</span>relative suitability ${val}%`, clientX, clientY);
    }
    stage.addEventListener("mousemove", e => { if (!dragging) readAt(e.clientX, e.clientY); });
    stage.addEventListener("mouseleave", () => { tip.hide(); });

    /* ----- init once species meta is available ----- */
    function init() {
      if (!window.GOC.species) { setTimeout(init, 60); return; }
      if (!chips.children.length)
        window.GOC.species.forEach((sp, i) => {
          const c = document.createElement("button");
          c.className = "chip"; c.dataset.key = sp.key;
          c.setAttribute("aria-pressed", String(i === 0));
          c.innerHTML = `<span class="sw" style="background:${sp.color}"></span>${sp.common}`;
          c.addEventListener("click", () => select(sp));
          chips.appendChild(c);
        });
      setWipe(50);
      select(window.GOC.species[0]);
    }
    // species chips may already be added above if data was ready; guard dup
    chips.innerHTML = "";
    window.addEventListener("goc-data-ready", init);
    if (window.GOC.species) init();
  }
})();

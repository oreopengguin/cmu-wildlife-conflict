/* ============================================================================
   charts.js — interactive SVG charts (niche PCA, skill dot-plot) built from the
   real exported pipeline data, plus the future-research cards.
   ========================================================================== */
(function () {
  "use strict";
  const SVGNS = "http://www.w3.org/2000/svg";
  const tip = window.GOC.tip;
  const el = (t, a) => { const e = document.createElementNS(SVGNS, t);
    for (const k in (a || {})) e.setAttribute(k, a[k]); return e; };

  /* draw a colourblind-redundant marker (matches matplotlib shapes) */
  function marker(g, shape, x, y, r, fill, stroke) {
    let m;
    if (shape === "o") m = el("circle", { cx: x, cy: y, r });
    else if (shape === "s") m = el("rect", { x: x - r, y: y - r, width: 2 * r, height: 2 * r, rx: 1 });
    else if (shape === "^") m = el("polygon", { points: `${x},${y - r} ${x - r},${y + r} ${x + r},${y + r}` });
    else if (shape === "v") m = el("polygon", { points: `${x},${y + r} ${x - r},${y - r} ${x + r},${y - r}` });
    else if (shape === "D") m = el("polygon", { points: `${x},${y - r} ${x + r},${y} ${x},${y + r} ${x - r},${y}` });
    else if (shape === "P") { const w = r * 0.5;
      m = el("polygon", { points: `${x - w},${y - r} ${x + w},${y - r} ${x + w},${y - w} ${x + r},${y - w} ${x + r},${y + w} ${x + w},${y + w} ${x + w},${y + r} ${x - w},${y + r} ${x - w},${y + w} ${x - r},${y + w} ${x - r},${y - w} ${x - w},${y - w}` }); }
    else { const w = r * 0.42, R = r; // X
      m = el("polygon", { points: `${x - R + w},${y - R} ${x},${y - w} ${x + R - w},${y - R} ${x + R},${y - R + w} ${x + w},${y} ${x + R},${y + R - w} ${x + R - w},${y + R} ${x},${y + w} ${x - R + w},${y + R} ${x - R},${y + R - w} ${x - w},${y} ${x - R},${y - R + w}` }); }
    m.setAttribute("fill", fill); m.setAttribute("stroke", stroke || "#fff");
    m.setAttribute("stroke-width", "0.8"); g.appendChild(m); return m;
  }

  const load = url => fetch(url).then(r => r.json());

  /* ===================== NICHE CHART ===================== */
  function niche(data) {
    const svg = document.getElementById("nicheChart");
    if (!svg) return;
    const W = 760, H = 460, M = { l: 46, r: 16, t: 14, b: 40 };
    const bg = data.background;
    const xs = bg.map(p => p[0]), ys = bg.map(p => p[1]);
    const xmin = Math.min(...xs), xmax = Math.max(...xs);
    const ymin = Math.min(...ys), ymax = Math.max(...ys);
    const px = v => M.l + (v - xmin) / (xmax - xmin) * (W - M.l - M.r);
    const py = v => H - M.b - (v - ymin) / (ymax - ymin) * (H - M.t - M.b);
    svg.innerHTML = "";

    // axes
    svg.appendChild(el("line", { x1: M.l, y1: H - M.b, x2: W - M.r, y2: H - M.b, stroke: "var(--faint)", "stroke-width": 1 }));
    svg.appendChild(el("line", { x1: M.l, y1: M.t, x2: M.l, y2: H - M.b, stroke: "var(--faint)", "stroke-width": 1 }));
    const xl = el("text", { x: (M.l + W - M.r) / 2, y: H - 6, "text-anchor": "middle", fill: "var(--slate)", "font-size": 12 });
    xl.textContent = `Climate PC1 (${data.pc1var}%)  →  warmer / drier`; svg.appendChild(xl);
    const yl = el("text", { x: 14, y: (M.t + H - M.b) / 2, "text-anchor": "middle", fill: "var(--slate)", "font-size": 12, transform: `rotate(-90 14 ${(M.t + H - M.b) / 2})` });
    yl.textContent = `Climate PC2 (${data.pc2var}%)`; svg.appendChild(yl);

    // background cloud
    const bgg = el("g", { opacity: 0.5 });
    for (const p of bg) bgg.appendChild(el("circle", { cx: px(p[0]), cy: py(p[1]), r: 1.4, fill: "var(--faint)" }));
    svg.appendChild(bgg);

    // species density contours (Gaussian-KDE isoline at 0.4·max — identical
    // construction to Figure 1B) + redundant shape marker at the niche centroid
    const groups = {}, hidden = {};
    function spotlight(key, on) {
      for (const k in groups) {
        if (hidden[k]) continue;
        groups[k].style.opacity = (!on || k === key) ? "1" : "0.16";
      }
    }
    for (const sp of window.GOC.species) {
      const s = data.species[sp.key]; if (!s || !s.contours) continue;
      const g = el("g", { class: "niche-sp", tabindex: 0, role: "img",
        "aria-label": `${sp.common} realized climatic niche, ${s.n} grid cells` });
      const polys = [];
      for (const path of s.contours) {
        const pts = path.map(p => `${px(p[0])},${py(p[1])}`).join(" ");
        const poly = el("polygon", { points: pts, fill: sp.color, "fill-opacity": 0.07,
          stroke: sp.color, "stroke-width": 1.8, "stroke-linejoin": "round",
          "stroke-linecap": "round", "pointer-events": "all" });
        g.appendChild(poly); polys.push(poly);
      }
      marker(g, sp.marker, px(s.centroid[0]), py(s.centroid[1]), 6, sp.color);
      const hi = on => {
        polys.forEach(p => { p.setAttribute("fill-opacity", on ? 0.24 : 0.07);
          p.setAttribute("stroke-width", on ? 2.8 : 1.8); });
        spotlight(sp.key, on);
      };
      g.addEventListener("mousemove", e => tip.show(
        `<span class="tt-t">${sp.common}</span>Realized climatic niche<br>${s.n.toLocaleString()} occupied grid cells`, e.clientX, e.clientY));
      g.addEventListener("mouseenter", () => hi(true));
      g.addEventListener("mouseleave", () => { hi(false); tip.hide(); });
      g.addEventListener("focus", () => hi(true));
      g.addEventListener("blur", () => hi(false));
      groups[sp.key] = g; svg.appendChild(g);
    }

    // legend chips: click to isolate/toggle · hover to spotlight
    const leg = document.getElementById("nicheLegend"); leg.innerHTML = "";
    for (const sp of window.GOC.species) {
      if (!data.species[sp.key]) continue;
      const chip = document.createElement("button");
      chip.className = "chip"; chip.setAttribute("aria-pressed", "true");
      chip.innerHTML = `<span class="sw" style="background:${sp.color}"></span>${sp.common}`;
      chip.addEventListener("click", () => {
        const on = chip.getAttribute("aria-pressed") === "true";
        chip.setAttribute("aria-pressed", String(!on));
        hidden[sp.key] = on;
        if (groups[sp.key]) groups[sp.key].style.display = on ? "none" : "";
      });
      chip.addEventListener("mouseenter", () => { if (!hidden[sp.key]) spotlight(sp.key, true); });
      chip.addEventListener("mouseleave", () => spotlight(sp.key, false));
      leg.appendChild(chip);
    }
  }

  /* ===================== SKILL DOT-PLOT ===================== */
  function skill(rows) {
    const svg = document.getElementById("skillChart");
    if (!svg) return;
    const W = 760, H = 420, M = { l: 118, r: 20, t: 16, b: 44 };
    const px = v => M.l + v * (W - M.l - M.r);
    const n = rows.length, band = (H - M.t - M.b) / n;
    svg.innerHTML = "";
    // gridlines
    for (let t = 0; t <= 1.0001; t += 0.2) {
      svg.appendChild(el("line", { x1: px(t), y1: M.t, x2: px(t), y2: H - M.b, stroke: "var(--line)", "stroke-width": 1 }));
      const tx = el("text", { x: px(t), y: H - M.b + 16, "text-anchor": "middle", fill: "var(--slate)", "font-size": 11 });
      tx.textContent = t.toFixed(1); svg.appendChild(tx);
    }
    // random line
    svg.appendChild(el("line", { x1: px(0.5), y1: M.t, x2: px(0.5), y2: H - M.b, stroke: "var(--faint)", "stroke-width": 1.4, "stroke-dasharray": "4 4" }));
    const rl = el("text", { x: px(0.5), y: M.t - 3, "text-anchor": "middle", fill: "var(--slate)", "font-size": 10 });
    rl.textContent = "random"; svg.appendChild(rl);
    const xl = el("text", { x: (M.l + W - M.r) / 2, y: H - 6, "text-anchor": "middle", fill: "var(--slate)", "font-size": 12 });
    xl.textContent = "spatial cross-validation skill"; svg.appendChild(xl);

    rows.forEach((r, i) => {
      const cy = M.t + band * (i + 0.5);
      const lab = el("text", { x: M.l - 10, y: cy + 4, "text-anchor": "end", fill: "var(--ink)", "font-size": 12 });
      lab.textContent = r.common; svg.appendChild(lab);
      const metrics = [["auc", "AUC", 0.16, "circle"], ["boyce", "Boyce", -0.16, "square"]];
      for (const [key, name, off, shp] of metrics) {
        const [m, sd] = r[key], y = cy + off * band;
        const col = key === "auc" ? "#0072B2" : "#009E73";
        svg.appendChild(el("line", { x1: px(Math.max(0, m - sd)), y1: y, x2: px(Math.min(1, m + sd)), y2: y, stroke: col, "stroke-width": 2, opacity: 0.5 }));
        const g = el("g", { tabindex: 0, role: "img", "aria-label": `${r.common} ${name} ${m}` });
        if (shp === "circle") g.appendChild(el("circle", { cx: px(m), cy: y, r: 5.5, fill: col, stroke: "#fff", "stroke-width": 1 }));
        else g.appendChild(el("rect", { x: px(m) - 5, y: y - 5, width: 10, height: 10, rx: 1.5, fill: col, stroke: "#fff", "stroke-width": 1 }));
        const tt = e => tip.show(`<span class="tt-t">${r.common}</span>${name} = ${m.toFixed(3)} ± ${sd.toFixed(3)}<br>(mean ± SD, 4 spatial folds)`, e.clientX, e.clientY);
        g.addEventListener("mousemove", tt);
        g.addEventListener("mouseleave", () => tip.hide());
        g.addEventListener("focus", () => tip.show(`${r.common}: ${name} ${m.toFixed(3)}`, px(m) + 40, y + 120));
        g.addEventListener("blur", () => tip.hide());
        svg.appendChild(g);
      }
    });
    // legend
    const lg = el("g");
    lg.appendChild(el("circle", { cx: M.l + 6, cy: H - M.b + 34, r: 5, fill: "#0072B2" }));
    const t1 = el("text", { x: M.l + 16, y: H - M.b + 38, fill: "var(--slate)", "font-size": 11 }); t1.textContent = "AUC"; lg.appendChild(t1);
    lg.appendChild(el("rect", { x: M.l + 62, y: H - M.b + 29, width: 10, height: 10, rx: 1.5, fill: "#009E73" }));
    const t2 = el("text", { x: M.l + 78, y: H - M.b + 38, fill: "var(--slate)", "font-size": 11 }); t2.textContent = "Boyce index"; lg.appendChild(t2);
    svg.appendChild(lg);
  }

  /* ===================== FUTURE RESEARCH CARDS ===================== */
  const FRONTIERS = [
    { tag: "Corridor triage", title: "Where to build the first wildlife bridge",
      body: "Our pinch-point map already shows the exact cells where climate-forced movement is squeezed through human land. Rank those by current × human pressure to decide where a wildlife overpass or underpass buys the most safe passage per dollar.",
      plain: "The map <b>already marks the funnels</b> where animals get bottlenecked near people — so build the crossings there first." },
    { tag: "Coupled transport", title: "Move predator and prey together",
      body: "Extend the optimal-transport step to shift a predator's range and its prey's range at once. New conflict triangles appear where both land near people — e.g. wolves following deer into farmland.",
      plain: "Slide the <b>wolf and the deer north at the same time</b>; trouble is wherever both end up next to a town." },
    { tag: "Early-warning topology", title: "Count the holes before a range collapses",
      body: "Track the persistent-homology loops (interior gaps) of a range through time. A rising number of holes is a leading signal that a range is fragmenting toward collapse — an alarm that fires before the population crashes.",
      plain: "As a habitat starts breaking into islands, <b>holes appear first</b>. Counting them warns us early." },
    { tag: "Inverse transport", title: "Plant a few reserves so animals can flow north",
      body: "Flip the problem around: instead of measuring friction, solve for the handful of new stepping-stone patches that would lower total transport cost the most — the cheapest reserves that let a species migrate poleward without hitting cities.",
      plain: "Ask the model: <b>where do a few small new parks</b> let wildlife move north most smoothly?" },
    { tag: "Two moving fields", title: "When people move too",
      body: "People are redistributing as well. Treat human expansion as its own transport field and compute where the wildlife field and the human field collide — conflict as the intersection of two moving measures, not one shifting into a fixed backdrop.",
      plain: "Both <b>wildlife and people are on the move</b>; the worst spots are where the two flows crash into each other." },
    { tag: "Zoom in", title: "One Alpine valley at 100 metres",
      body: "Run the identical geometry at fine resolution inside a single valley. Same math, actionable output: exactly which slope, road, or pasture becomes a conflict pinch-point, at a scale a local planner can act on.",
      plain: "Take the whole method and <b>zoom into one valley</b> so a park ranger can use the map street-by-street." }
  ];
  function frontiers() {
    const host = document.getElementById("frontierCards"); if (!host) return;
    host.innerHTML = FRONTIERS.map(f => `
      <article class="fcard reveal">
        <div class="tag">${f.tag}</div>
        <h4>${f.title}</h4>
        <p>${f.body}</p>
        <div class="plain">🗣️ ${f.plain}</div>
      </article>`).join("");
    host.querySelectorAll(".reveal").forEach(e => e.classList.add("in"));
  }

  /* ===================== shared helpers for the new panels ===================== */
  const b64ToU8 = s => { const b = atob(s); const a = new Uint8Array(b.length);
    for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; };
  function svgXY(svg, e) {                       // client px -> viewBox coords
    const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
    const m = svg.getScreenCTM(); return m ? p.matrixTransform(m.inverse()) : { x: 0, y: 0 };
  }
  const signed = v => (v > 0 ? "+" : "") + v;

  /* ===================== FIG 2C — species shift-vs-latitude ===================== */
  function fig2c(data) {
    const svg = document.getElementById("fig2cChart"); if (!svg) return;
    const W = 760, H = 440, M = { l: 60, r: 18, t: 16, b: 46 };
    const xmin = data.lat_min, xmax = data.lat_max, ymin = 0, ymax = data.shift_max * 1.06;
    const px = v => M.l + (v - xmin) / (xmax - xmin) * (W - M.l - M.r);
    const py = v => H - M.b - (v - ymin) / (ymax - ymin) * (H - M.t - M.b);
    svg.innerHTML = "";
    for (let t = 0; t <= ymax; t += 200) {
      svg.appendChild(el("line", { x1: M.l, y1: py(t), x2: W - M.r, y2: py(t), stroke: "var(--line)", "stroke-width": 1 }));
      const tx = el("text", { x: M.l - 8, y: py(t) + 3, "text-anchor": "end", fill: "var(--slate)", "font-size": 11 }); tx.textContent = t; svg.appendChild(tx);
    }
    for (let lat = 35; lat <= 70; lat += 5) {
      const tx = el("text", { x: px(lat), y: H - M.b + 16, "text-anchor": "middle", fill: "var(--slate)", "font-size": 11 }); tx.textContent = lat; svg.appendChild(tx);
    }
    const xl = el("text", { x: (M.l + W - M.r) / 2, y: H - 6, "text-anchor": "middle", fill: "var(--slate)", "font-size": 12 }); xl.textContent = "Latitude (°N)"; svg.appendChild(xl);
    const yl = el("text", { x: 16, y: (M.t + H - M.b) / 2, "text-anchor": "middle", fill: "var(--slate)", "font-size": 12, transform: `rotate(-90 16 ${(M.t + H - M.b) / 2})` }); yl.textContent = "Required range shift (km)"; svg.appendChild(yl);
    const guide = el("line", { y1: M.t, y2: H - M.b, stroke: "var(--faint)", "stroke-width": 1, "stroke-dasharray": "3 3", opacity: 0 }); svg.appendChild(guide);
    const dot = el("circle", { r: 4.5, fill: "var(--card)", stroke: "var(--ink)", "stroke-width": 1.6, opacity: 0 }); svg.appendChild(dot);

    const groups = {}, hidden = {};
    function spotlight(key, on) { for (const k in groups) { if (hidden[k]) continue; groups[k].style.opacity = (!on || k === key) ? "1" : "0.14"; } }
    const interp = (pts, lat) => {
      if (lat <= pts[0][0]) return pts[0][1];
      if (lat >= pts[pts.length - 1][0]) return pts[pts.length - 1][1];
      for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1];
        if (lat >= a[0] && lat <= b[0]) return a[1] + (lat - a[0]) / (b[0] - a[0] + 1e-9) * (b[1] - a[1]); }
      return pts[pts.length - 1][1];
    };
    for (const sp of data.species) {
      const pts = sp.points; if (pts.length < 2) continue;
      const g = el("g", { class: "fig2c-sp", tabindex: 0, role: "img", "aria-label": `${sp.common} range shift vs latitude` });
      const d = pts.map((p, i) => `${i ? "L" : "M"}${px(p[0])},${py(p[1])}`).join(" ");
      const line = el("path", { d, fill: "none", stroke: sp.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" });
      g.appendChild(line);
      for (const p of pts) marker(g, sp.marker, px(p[0]), py(p[1]), 4, sp.color);
      const hit = el("path", { d, fill: "none", stroke: "transparent", "stroke-width": 16, "stroke-linecap": "round" });
      g.appendChild(hit);
      const hi = on => { line.setAttribute("stroke-width", on ? 3.4 : 2); spotlight(sp.key, on); };
      hit.addEventListener("mousemove", e => {
        const loc = svgXY(svg, e);
        let lat = xmin + (loc.x - M.l) / (W - M.l - M.r) * (xmax - xmin);
        lat = Math.max(pts[0][0], Math.min(pts[pts.length - 1][0], lat));
        const val = interp(pts, lat);
        guide.setAttribute("x1", px(lat)); guide.setAttribute("x2", px(lat)); guide.setAttribute("opacity", 1);
        dot.setAttribute("cx", px(lat)); dot.setAttribute("cy", py(val)); dot.setAttribute("stroke", sp.color); dot.setAttribute("opacity", 1);
        tip.show(`<span class="tt-t">${sp.common}</span>at ${lat.toFixed(0)}°N → required shift ≈ <b>${Math.round(val)} km</b>`, e.clientX, e.clientY);
      });
      hit.addEventListener("mouseenter", () => hi(true));
      hit.addEventListener("mouseleave", () => { hi(false); tip.hide(); guide.setAttribute("opacity", 0); dot.setAttribute("opacity", 0); });
      g.addEventListener("focus", () => hi(true)); g.addEventListener("blur", () => hi(false));
      groups[sp.key] = g; svg.appendChild(g);
    }
    const leg = document.getElementById("fig2cLegend"); leg.innerHTML = "";
    for (const sp of data.species) {
      const chip = document.createElement("button"); chip.className = "chip"; chip.setAttribute("aria-pressed", "true");
      chip.innerHTML = `<span class="sw" style="background:${sp.color}"></span>${sp.common}`;
      chip.addEventListener("click", () => { const on = chip.getAttribute("aria-pressed") === "true"; chip.setAttribute("aria-pressed", String(!on)); hidden[sp.key] = on; if (groups[sp.key]) groups[sp.key].style.display = on ? "none" : ""; });
      chip.addEventListener("mouseenter", () => { if (!hidden[sp.key]) spotlight(sp.key, true); });
      chip.addEventListener("mouseleave", () => spotlight(sp.key, false));
      leg.appendChild(chip);
    }
  }

  /* ===================== FIG 3B — corridor map + pinch-points ===================== */
  function fig3b(data) {
    const stage = document.getElementById("fig3bStage"); if (!stage) return;
    const img = document.getElementById("fig3bImg"); img.src = "assets/img/corridor_map.png";
    const marks = document.getElementById("fig3bMarks");
    const readout = document.getElementById("fig3bReadout");
    const [gh, gw] = data.coarse_shape, mask = b64ToU8(data.mask), grid = b64ToU8(data.grid), E = data.extent;
    const toFrac = (lon, lat) => [(lon - E[0]) / (E[1] - E[0]), (E[3] - lat) / (E[3] - E[2])];
    marks.innerHTML = "";
    data.circles.forEach(c => {
      const [fx, fy] = toFrac(c.lon, c.lat);
      const pin = document.createElement("div");
      pin.className = "pin"; pin.style.left = fx * 100 + "%"; pin.style.top = fy * 100 + "%";
      pin.setAttribute("tabindex", "0"); pin.setAttribute("role", "img");
      pin.setAttribute("aria-label", `Pinch-point rank ${c.rank}, ${c.place || ""}, corridor intensity ${c.intensity}`);
      pin.innerHTML = `<span class="rk">${c.rank}</span>`;
      pin.addEventListener("mousemove", e => { e.stopPropagation(); pin.classList.add("on");
        tip.show(`<span class="tt-t">Pinch-point #${c.rank}${c.place ? " · " + c.place : ""}</span>${c.lat.toFixed(1)}°N, ${c.lon.toFixed(1)}°E<br>corridor intensity <b>${c.intensity}</b> · ${c.rel}% of the p97 scale`, e.clientX, e.clientY); });
      pin.addEventListener("mouseleave", () => { pin.classList.remove("on"); tip.hide(); });
      marks.appendChild(pin);
    });
    stage.addEventListener("mousemove", e => {
      const r = stage.getBoundingClientRect();
      const fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
      if (fx < 0 || fx > 1 || fy < 0 || fy > 1) return;
      const col = Math.min(gw - 1, Math.floor(fx * gw)), row = Math.min(gh - 1, Math.floor(fy * gh)), idx = row * gw + col;
      if (!mask[idx]) { readout.textContent = "— sea / outside study area —"; return; }
      const lon = E[0] + fx * (E[1] - E[0]), lat = E[3] - fy * (E[3] - E[2]);
      readout.innerHTML = `At ${lat.toFixed(1)}°N, ${lon.toFixed(1)}°E · conflict-corridor intensity ≈ <b>${grid[idx]}%</b> of the peak &nbsp;·&nbsp; rings = the 16 strongest pinch-points.`;
    });
    stage.addEventListener("mouseleave", () => { readout.textContent = "Hover the map to read conflict-corridor intensity; hover a ring for a ranked pinch-point."; });
  }

  /* ===================== FIG 4A — CRI map (reuses risk_grid) ===================== */
  function fig4a(data) {
    const stage = document.getElementById("fig4aStage"); if (!stage) return;
    const readout = document.getElementById("fig4aReadout");
    const [gh, gw] = data.coarse_shape, mask = b64ToU8(data.mask), cri = b64ToU8(data.cri), E = data.extent;
    stage.addEventListener("mousemove", e => {
      const r = stage.getBoundingClientRect();
      const fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
      if (fx < 0 || fx > 1 || fy < 0 || fy > 1) return;
      const col = Math.min(gw - 1, Math.floor(fx * gw)), row = Math.min(gh - 1, Math.floor(fy * gh)), idx = row * gw + col;
      if (!mask[idx]) { readout.textContent = "— sea / outside study area —"; return; }
      const lon = E[0] + fx * (E[1] - E[0]), lat = E[3] - fy * (E[3] - E[2]), v = cri[idx];
      const band = v >= 80 ? "very high" : v >= 60 ? "high" : v >= 40 ? "moderate" : v >= 20 ? "low" : "very low";
      readout.innerHTML = `At ${lat.toFixed(1)}°N, ${lon.toFixed(1)}°E · relative Coexistence Risk ≈ <b>${v}/100</b> (${band}).`;
    });
    stage.addEventListener("mouseleave", () => { readout.textContent = "Hover the map to read the relative Coexistence Risk Index (0–100, percentile-scaled as displayed)."; });
  }

  /* ===================== FIG 4A labels — named bright clusters ===================== */
  function fig4aLabels(data) {
    const marks = document.getElementById("fig4aMarks"); if (!marks) return;
    const E = data.extent || [-12, 40, 34, 72];
    marks.innerHTML = "";
    for (const l of data.labels) {
      const fx = (l.lon - E[0]) / (E[1] - E[0]), fy = (E[3] - l.lat) / (E[3] - E[2]);
      const dot = document.createElement("div"); dot.className = "map-dot";
      dot.style.left = fx * 100 + "%"; dot.style.top = fy * 100 + "%"; marks.appendChild(dot);
      const lab = document.createElement("div"); lab.className = "map-label";
      lab.style.left = fx * 100 + "%"; lab.style.top = fy * 100 + "%"; lab.textContent = l.name;
      marks.appendChild(lab);
    }
  }

  /* ===================== FIG 4B — predicted vs observed shift ===================== */
  function fig4b(meta) {
    const svg = document.getElementById("fig4bChart"); if (!svg) return;
    const pts = meta.species.filter(s => s.obs_dlat != null).map(s => ({ ...s, x: s.obs_dlat, y: s.pred_dlat }));
    if (!pts.length) return;
    const W = 560, H = 470, M = { l: 56, r: 18, t: 20, b: 50 };
    const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
    let lo = Math.min(...xs, ...ys, 0), hi = Math.max(...xs, ...ys, 0);
    const pad = 0.12 * (hi - lo + 1e-9); lo -= pad; hi += pad;
    const px = v => M.l + (v - lo) / (hi - lo) * (W - M.l - M.r);
    const py = v => H - M.b - (v - lo) / (hi - lo) * (H - M.t - M.b);
    svg.innerHTML = "";
    svg.appendChild(el("line", { x1: px(0), y1: M.t, x2: px(0), y2: H - M.b, stroke: "var(--line)", "stroke-width": 1 }));
    svg.appendChild(el("line", { x1: M.l, y1: py(0), x2: W - M.r, y2: py(0), stroke: "var(--line)", "stroke-width": 1 }));
    svg.appendChild(el("line", { x1: px(lo), y1: py(lo), x2: px(hi), y2: py(hi), stroke: "var(--faint)", "stroke-width": 1.4, "stroke-dasharray": "5 4" }));
    const t11 = el("text", { x: px(hi) - 4, y: py(hi) + 14, "text-anchor": "end", fill: "var(--slate)", "font-size": 10 }); t11.textContent = "1:1 (perfect prediction)"; svg.appendChild(t11);
    const xl = el("text", { x: (M.l + W - M.r) / 2, y: H - 8, "text-anchor": "middle", fill: "var(--slate)", "font-size": 11.5 }); xl.textContent = "Observed Δlatitude (°)"; svg.appendChild(xl);
    const yl = el("text", { x: 15, y: (M.t + H - M.b) / 2, "text-anchor": "middle", fill: "var(--slate)", "font-size": 11.5, transform: `rotate(-90 15 ${(M.t + H - M.b) / 2})` }); yl.textContent = "OT-predicted Δlatitude (°)"; svg.appendChild(yl);
    for (const p of pts) {
      const g = el("g", { tabindex: 0, role: "img", "aria-label": `${p.common} observed ${p.x} predicted ${p.y}` });
      marker(g, p.marker, px(p.x), py(p.y), 7, p.color);
      const note = p.key === "Canis lupus" ? "<br><i>recolonization-driven outlier</i>" : "";
      const tt = e => tip.show(`<span class="tt-t">${p.common}</span>observed <b>${signed(p.x)}°</b> · predicted <b>${signed(p.y)}°</b>${note}`, e.clientX, e.clientY);
      g.addEventListener("mousemove", tt); g.addEventListener("mouseleave", () => tip.hide());
      g.addEventListener("focus", () => tip.show(`${p.common}: observed ${signed(p.x)}, predicted ${signed(p.y)}`, px(p.x) + 40, py(p.y) + 140)); g.addEventListener("blur", () => tip.hide());
      svg.appendChild(g);
    }
    const r = meta.results || {};
    const st = el("text", { x: M.l + 6, y: M.t + 10, fill: "var(--ink)", "font-size": 11, "font-weight": 600 });
    st.textContent = `Spearman ρ = ${r.spearman} · Pearson r = ${r.pearson}`; svg.appendChild(st);
  }

  /* ===================== FIG 4D — per-species risk decomposition ===================== */
  function fig4d(data) {
    const svg = document.getElementById("fig4dChart"); if (!svg) return;
    const sps = data.species, metrics = data.metrics, nR = sps.length, nC = metrics.length;
    const W = 560, H = 470, M = { l: 104, r: 14, t: 78, b: 14 };
    const cw = (W - M.l - M.r) / nC, ch = (H - M.t - M.b) / nR;
    const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
    const NEG = [94, 60, 153], MID = [247, 247, 247], POS = [178, 24, 43];
    const zcol = z => { if (z == null) return "var(--card2)"; const t = Math.max(-1, Math.min(1, z / 2));
      const c = t < 0 ? mix(MID, NEG, -t) : mix(MID, POS, t); return `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})`; };
    svg.innerHTML = "";
    metrics.forEach((mn, j) => {
      const cx = M.l + cw * (j + 0.5);
      const tx = el("text", { x: cx, y: M.t - 10, "text-anchor": "start", fill: "var(--slate)", "font-size": 10, transform: `rotate(-40 ${cx} ${M.t - 10})` }); tx.textContent = mn; svg.appendChild(tx);
    });
    sps.forEach((sp, i) => {
      const ty = el("text", { x: M.l - 8, y: M.t + ch * (i + 0.5) + 3, "text-anchor": "end", fill: "var(--ink)", "font-size": 11 }); ty.textContent = sp.common; svg.appendChild(ty);
      metrics.forEach((mn, j) => {
        const z = sp.z[j], v = sp.vals[j], x = M.l + cw * j, y = M.t + ch * i;
        const g = el("g", { tabindex: 0, role: "img", "aria-label": `${sp.common} ${mn} ${v}` });
        g.appendChild(el("rect", { x: x + 1.5, y: y + 1.5, width: cw - 3, height: ch - 3, rx: 3, fill: zcol(z), stroke: "var(--card)", "stroke-width": 1 }));
        const dark = z != null && Math.abs(z) > 1.1;
        const vt = el("text", { x: x + cw / 2, y: y + ch / 2 + 3.5, "text-anchor": "middle", "font-size": 10.5, fill: dark ? "#fff" : "#17241f" });
        vt.textContent = v == null ? "—" : (Math.abs(v) >= 10 ? Math.round(v) : v.toFixed(2)); g.appendChild(vt);
        const tt = e => tip.show(`<span class="tt-t">${sp.common}</span>${mn}: <b>${v == null ? "n/a" : v}</b>${z == null ? "" : ` &nbsp;·&nbsp; z = ${signed(z)}`}`, e.clientX, e.clientY);
        g.addEventListener("mousemove", tt); g.addEventListener("mouseleave", () => tip.hide());
        g.addEventListener("focus", () => tip.show(`${sp.common} ${mn} ${v}`, x + cw, y + ch)); g.addEventListener("blur", () => tip.hide());
        svg.appendChild(g);
      });
    });
  }

  /* ===================== BOOT ===================== */
  const j = n => load(`assets/data/${n}.json`);
  Promise.all([j("meta"), j("skill"), j("niche")])
    .then(([meta, sk, nch]) => {
      window.GOC.species = meta.species;
      window.GOC.meta = meta;
      niche(nch); skill(sk); frontiers(); fig4b(meta);
      window.dispatchEvent(new CustomEvent("goc-data-ready"));
      // secondary interactive panels — load independently so one failure can't
      // break the others or the primary charts
      j("fig2c").then(fig2c).catch(e => console.error("fig2c", e));
      j("fig3b").then(fig3b).catch(e => console.error("fig3b", e));
      j("fig4d").then(fig4d).catch(e => console.error("fig4d", e));
      j("risk_grid").then(fig4a).catch(e => console.error("fig4a", e));
      j("fig4a").then(fig4aLabels).catch(e => console.error("fig4a labels", e));
    })
    .catch(err => { console.error("chart data load failed", err); frontiers(); });
})();

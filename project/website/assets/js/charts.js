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

  /* ===================== BOOT ===================== */
  Promise.all([load("assets/data/meta.json"), load("assets/data/skill.json"),
               load("assets/data/niche.json")])
    .then(([meta, sk, nch]) => {
      window.GOC.species = meta.species;
      window.GOC.meta = meta;
      niche(nch); skill(sk); frontiers();
      window.dispatchEvent(new CustomEvent("goc-data-ready"));
    })
    .catch(err => { console.error("chart data load failed", err); frontiers(); });
})();

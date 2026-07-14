/* ============================================================================
   game.js — "Escape Room: Save the Wildlife Before It's Too Late"
   Four research stations reinforce the project's pipeline. No new science is
   introduced — every fact mirrors the rest of the site. Fully keyboard- and
   touch-accessible; progress persists within a session.
   ========================================================================== */
(function () {
  "use strict";
  const root = document.getElementById("gameRoot");
  if (!root) return;

  /* ---------- helpers ---------- */
  const h = (tag, attrs, kids) => {
    const e = document.createElement(tag);
    for (const k in (attrs || {})) {
      if (k === "class") e.className = attrs[k];
      else if (k === "html") e.innerHTML = attrs[k];
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), attrs[k]);
      else e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(c => e.appendChild(typeof c === "string" ? document.createTextNode(c) : c));
    return e;
  };
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

  /* ---------- persistent-ish state ---------- */
  const STEPS = ["Habitat Model", "Animal Movement", "Human Conflict", "Risk Prediction"];
  const state = { room: 0, solved: [false, false, false, false], keys: 0,
    wrong: 0, hints: 0, notes: [] };
  try { const s = JSON.parse(sessionStorage.getItem("goc-game")); if (s) Object.assign(state, s); } catch (e) {}
  const save = () => { try { sessionStorage.setItem("goc-game", JSON.stringify(state)); } catch (e) {} };

  /* facts logged to the notebook — all already stated elsewhere on the site */
  const NOTES = [
    "Habitat models (MaxEnt) are built from <b>climate data</b> and species sightings.",
    "Warming pushes European species <b>~484 km north</b> on average by 2090.",
    "Conflict concentrates where wildlife moves into <b>farmland and cities</b> (high human modification).",
    "The risk map flags hotspots — the <b>Alps</b>, the <b>Poland–Belarus lowlands</b>, and the <b>north-eastern Baltic</b> — <b>without using any historical conflict data</b>."
  ];

  /* ---------- varied wrong-answer feedback ----------------------------------
     A large, rotating pool so a second (or tenth) wrong guess always reads
     differently — the player can tell a new attempt registered. Kept short,
     kind, and non-nagging: a small red ✗ beside the action, nothing more. */
  const WRONG_MSGS = [
    "Incorrect", "Not quite — try again", "Almost there!", "So close!",
    "Give it another go", "Hmm, not that one", "Keep going — you've got this",
    "Not this time", "Close! Rethink it", "Try again", "Not the one",
    "Almost! One more try", "Not quite right", "You're on the trail — retry",
    "Getting warmer… try again", "Have another go", "Missed it — try again",
    "Not yet — keep at it", "Re-examine and retry", "Nearly! Adjust and retry",
    "Off by a bit — try again", "Not the answer we need"
  ];
  let wrongSeq = shuffle(WRONG_MSGS), wrongPtr = 0;
  function nextWrongMsg() {
    if (wrongPtr >= wrongSeq.length) { wrongSeq = shuffle(WRONG_MSGS); wrongPtr = 0; }
    return wrongSeq[wrongPtr++];
  }
  /* "already found" pool (Room 4) — neutral, not counted as a wrong answer */
  const ALREADY_MSGS = [
    "You've already found that one — try another cluster.",
    "Already flagged — look for a different hotspot.",
    "That spot's already marked. Find another.",
    "Already discovered — hunt down the other bright areas.",
    "Yep, that one's on the board — pick a new region.",
    "Already found it — seek the remaining hotspots.",
    "Been there! Try a different bright cluster."
  ];
  let alreadySeq = shuffle(ALREADY_MSGS), alreadyPtr = 0;
  function nextAlreadyMsg() {
    if (alreadyPtr >= alreadySeq.length) { alreadySeq = shuffle(ALREADY_MSGS); alreadyPtr = 0; }
    return alreadySeq[alreadyPtr++];
  }
  /* small inline indicator that lives next to the action / check button */
  function inlineFb() { return h("span", { class: "g-inline-fb", id: "gInlineFb",
    role: "status", "aria-live": "assertive" }, []); }
  function inlineMsg(msg, kind) {           // kind: "wrong" (red ✕, counts) | "info" (amber ℹ, neutral)
    if (kind !== "info") { state.wrong++; save(); }
    const box = document.getElementById("gInlineFb");
    if (!box) return;
    box.className = "g-inline-fb" + (kind === "info" ? " info" : "");
    box.innerHTML = `<span class="x" aria-hidden="true">${kind === "info" ? "ℹ" : "✕"}</span><span class="msg">${msg}</span>`;
    void box.offsetWidth; box.classList.add("show");   // re-trigger the pop animation
  }
  function showWrong() { inlineMsg(nextWrongMsg(), "wrong"); }
  function showAlready() { inlineMsg(nextAlreadyMsg(), "info"); }
  function clearWrong() {
    const box = document.getElementById("gInlineFb");
    if (box) { box.className = "g-inline-fb"; box.innerHTML = ""; }
  }

  /* ---------- shell ---------- */
  let stage, keysTray, notebookUl;
  function shell() {
    root.innerHTML = "";
    const game = h("div", { class: "game" });

    const header = h("div", { class: "g-progress" }, [
      h("div", { class: "g-title" }, [
        h("span", {}, ["Research Progress"]),
        h("span", { id: "gPct", style: "color:var(--slate)" }, [""])
      ]),
      h("div", { class: "g-bar" }, [h("i", { id: "gBar" })]),
      (() => {
        const st = h("div", { class: "g-steps" });
        STEPS.forEach((s, i) => st.appendChild(h("div", { class: "g-step", id: "gStep" + i }, [
          h("span", { class: "box" }, [""]), h("span", {}, [s])
        ])));
        return st;
      })()
    ]);

    stage = h("div", { class: "g-body", id: "gStage" });
    game.appendChild(header); game.appendChild(stage);
    root.appendChild(game);
    updateProgress();
    render();
  }

  function updateProgress() {
    const done = state.solved.filter(Boolean).length;
    const bar = document.getElementById("gBar");
    if (bar) bar.style.width = (done / 4 * 100) + "%";
    const pct = document.getElementById("gPct");
    if (pct) pct.textContent = `${done} / 4 stations`;
    STEPS.forEach((_, i) => {
      const st = document.getElementById("gStep" + i);
      if (!st) return;
      st.classList.toggle("done", state.solved[i]);
      st.classList.toggle("active", i === state.room && !state.solved[i]);
      st.querySelector(".box").textContent = state.solved[i] ? "✓" : "";
    });
  }

  /* side rail: keys + notebook (rendered inside each room) */
  function sideRail() {
    const keys = h("div", { class: "g-keys" });
    for (let i = 0; i < 4; i++) keys.appendChild(
      h("div", { class: "g-key" + (i < state.keys ? " have" : ""), id: "gKey" + i }, ["🔑"]));
    keysTray = keys;
    const nb = h("div", { class: "g-notebook" }, [
      h("h5", {}, ["🔬 Field notebook"]),
      (() => { const ul = h("ul", { id: "gNotes" }); notebookUl = ul;
        state.notes.forEach(n => ul.appendChild(h("li", { html: n }))); return ul; })()
    ]);
    if (!state.notes.length) nb.querySelector("ul").appendChild(
      h("li", { style: "list-style:none;margin-left:-18px" }, ["Solve a station to record what you learned…"]));
    return h("div", { class: "g-side" }, [keys, nb]);
  }

  function feedback(msg, ok) {
    let fb = document.getElementById("gFb");
    if (!fb) return;
    fb.className = "g-feedback show " + (ok === true ? "ok" : ok === "info" ? "info" : "no");
    fb.innerHTML = msg;
  }

  function awardKey(roomIdx) {
    if (state.solved[roomIdx]) return;         // idempotent — never double-award or double-log a note
    state.solved[roomIdx] = true;
    state.keys = state.solved.filter(Boolean).length;
    if (!state.notes.includes(NOTES[roomIdx])) state.notes.push(NOTES[roomIdx]);
    save(); updateProgress();
    const k = document.getElementById("gKey" + (state.keys - 1));
    if (k) k.classList.add("have");
    if (notebookUl) {
      const first = notebookUl.querySelector("li[style]");
      if (first) first.remove();
      notebookUl.appendChild(h("li", { html: NOTES[roomIdx] }));
    }
  }

  function nextControls(roomIdx) {
    const allDone = state.solved.every(Boolean);
    return h("div", { class: "g-controls" }, [
      h("button", { class: "g-btn primary", onclick: () => {
        if (allDone) { state.room = 4; render(); }
        else { state.room = state.solved.findIndex(s => !s); render(); }
      } }, [allDone ? "Unlock the final map →" : "Next station →"])
    ]);
  }

  function hintControl(roomIdx, text) {
    const box = h("div", { class: "g-hintbox", id: "gHint" });
    const btn = h("button", { class: "g-btn", onclick: () => {
      box.classList.add("show"); box.innerHTML = "💡 " + text;
      state.hints++; save(); btn.disabled = true;
    } }, ["Need a hint?"]);
    return h("div", {}, [h("div", { class: "g-controls" }, [btn]), box]);
  }

  /* ============================ ROUND ROUTER ============================ */
  function render() {
    if (state.room >= 4 || state.solved.every(Boolean) && state.room === 4) return finalScreen();
    // route to first unsolved room if current is solved
    if (state.solved[state.room]) {
      const nx = state.solved.findIndex(s => !s);
      state.room = nx === -1 ? 4 : nx;
    }
    if (state.room === 4 || state.solved.every(Boolean)) return finalScreen();
    [room1, room2, room3, room4][state.room]();
    updateProgress();
  }

  /* ============================ ROOM 1 ============================ */
  /* Live, pointer-based sortable: the whole strip re-flows as you drag —
     the held tab tracks the cursor with no drop-shadow, the others slide to
     make room, and the order updates the instant the cursor crosses a slot. */
  function room1() {
    const correct = ["Climate Data", "Habitat Model", "Animal Movement", "Coexistence Risk Map"];
    const icons = { "Climate Data": "🌡️", "Habitat Model": "🧬", "Animal Movement": "🦌", "Coexistence Risk Map": "🗺️" };
    let order = shuffle(correct);
    if (order.join() === correct.join()) order = shuffle(correct); // avoid pre-solved

    stage.innerHTML = "";
    const list = h("div", { class: "g-cards", id: "gDrag", role: "list",
      "aria-label": "Order the four pipeline stages, top to bottom" });
    const nodes = {};              // name -> element
    const GAP = 10;
    let cardH = 0, step = 0, listTop = 0;
    let held = null, heldName = null, grabDY = 0, locked = false;

    function layout() {            // position every card (except the held one) by its slot
      order.forEach((name, i) => {
        const el = nodes[name];
        if (el === held) return;
        el.style.setProperty("--ty", (i * step) + "px");
      });
    }
    function measure() {
      cardH = nodes[order[0]].offsetHeight;
      step = cardH + GAP;
      list.style.height = (order.length * step - GAP) + "px";
      list.classList.add("abs");
      layout();
    }
    function moveByButton(name, dir) {
      if (locked) return;
      const i = order.indexOf(name), j = i + dir;
      if (j < 0 || j >= order.length) return;
      order.splice(j, 0, order.splice(i, 1)[0]);
      layout();
    }
    function onGrab(e, name, card) {
      if (locked || e.target.closest("button")) return;   // let ▲▼ work; no drag once solved
      if (e.button !== undefined && e.button !== 0) return; // left / primary only
      if (e.pointerType === "touch" && !e.target.closest(".g-grip")) return; // mobile: grip only, so the page can still scroll
      e.preventDefault();
      held = card; heldName = name;
      listTop = list.getBoundingClientRect().top;
      grabDY = e.clientY - card.getBoundingClientRect().top;
      card.classList.add("dragging");
      try { card.setPointerCapture(e.pointerId); } catch (_) {}
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onDrop, { once: true });
      window.addEventListener("pointercancel", onDrop, { once: true });
    }
    function onMove(e) {
      if (!held) return;
      const maxY = (order.length - 1) * step;
      let y = Math.max(0, Math.min(maxY, e.clientY - grabDY - listTop));
      held.style.transform = `translateY(${y}px)`;         // held tracks cursor, no transition
      const desired = Math.max(0, Math.min(order.length - 1, Math.round(y / step)));
      const cur = order.indexOf(heldName);
      if (desired !== cur) {                                // live re-order the instant a slot is crossed
        order.splice(desired, 0, order.splice(cur, 1)[0]);
        layout();
      }
    }
    function onDrop() {
      if (!held) return;
      window.removeEventListener("pointermove", onMove);
      const cur = order.indexOf(heldName);
      held.classList.remove("dragging");
      held.style.transform = "";                            // hand back to stylesheet (var --ty)
      held.style.setProperty("--ty", (cur * step) + "px");
      held = heldName = null;
    }
    function finalizeOrder() {      // solved → return to normal flow so the snap animation is clean
      locked = true;
      list.classList.remove("abs");
      list.style.height = "";
      order.forEach((name, i) => {
        const el = nodes[name];
        el.style.transform = ""; el.style.removeProperty("--ty");
        list.appendChild(el);                                // reinsert in solved order
        setTimeout(() => el.classList.add("correct", "snap"), i * 90);
      });
    }

    function buildCard(name) {
      const card = h("div", { class: "g-card", "data-name": name, tabindex: "0", role: "listitem",
        "aria-roledescription": "sortable stage", "aria-label": name }, [
        h("span", { class: "g-grip", "aria-hidden": "true", title: "drag to reorder" }, ["⠿"]),
        h("span", { class: "h" }, [icons[name]]),
        h("span", { class: "lbl" }, [name]),
        h("span", { class: "ord" }, [
          h("button", { class: "g-mini", title: "move up", "aria-label": `move ${name} up`,
            onclick: (e) => { e.stopPropagation(); moveByButton(name, -1); } }, ["▲"]),
          h("button", { class: "g-mini", title: "move down", "aria-label": `move ${name} down`,
            onclick: (e) => { e.stopPropagation(); moveByButton(name, 1); } }, ["▼"])
        ])
      ]);
      card.addEventListener("pointerdown", e => onGrab(e, name, card));
      card.addEventListener("keydown", e => {
        if (e.key === "ArrowUp") { e.preventDefault(); moveByButton(name, -1); nodes[name].focus(); }
        if (e.key === "ArrowDown") { e.preventDefault(); moveByButton(name, 1); nodes[name].focus(); }
      });
      return card;
    }
    order.forEach(name => { const c = buildCard(name); nodes[name] = c; list.appendChild(c); });
    requestAnimationFrame(measure);

    stage.append(
      h("div", { class: "g-room" }, [
        h("div", { class: "g-station" }, ["Research Station 1 · Habitat Model"]),
        h("h3", {}, ["Restore the Pipeline"]),
        h("p", { class: "g-story" }, ["A system failure erased the workflow. Rebuild the pipeline our project uses to turn raw data into a conflict forecast — drag the cards (or use ▲▼) into the right order."]),
        list,
        h("div", { class: "g-controls" }, [
          h("button", { class: "g-btn primary", onclick: () => {
            if (locked) return;
            if (order.join() === correct.join()) {
              clearWrong();
              finalizeOrder();
              feedback("<b>✅ Pipeline Restored.</b> Climate data trains the habitat model; the model's maps drive the animal-movement step; that produces the Coexistence Risk Map. <b>Key 1 earned.</b>", true);
              awardKey(0);
              setTimeout(() => stage.querySelector(".g-room").appendChild(nextControls(0)), 500);
            } else {
              Object.values(nodes).forEach(c => { c.classList.add("nudge"); setTimeout(() => c.classList.remove("nudge"), 500); });
              showWrong();
            }
          } }, ["Check order"]),
          inlineFb()
        ]),
        hintControl(0, "The forecast is the last step. It needs animal movement, which needs a habitat model, which needs the raw climate data first."),
        h("div", { class: "g-feedback", id: "gFb" }),
        sideRail()
      ]));
  }

  /* ============================ ROOM 2 ============================ */
  function room2() {
    stage.innerHTML = "";
    const dirs = [["⬆", "North"], ["⬇", "South"], ["➡", "East"], ["⬅", "West"]];
    const choices = h("div", { class: "g-choices dir" });
    let locked = false;
    dirs.forEach(([ic, name]) => {
      const b = h("button", { class: "g-choice", "aria-pressed": "false" }, [
        h("span", { class: "ic" }, [ic]), h("span", {}, [name])]);
      b.addEventListener("click", () => {
        if (locked) return;
        if (name === "North") {
          locked = true; b.classList.add("correct"); clearWrong();
          feedback("<b>Correct!</b> As temperatures rise, many European species shift <b>north</b> to stay within suitable climates — about 484 km on average by 2090. <b>Key 2 earned.</b>", true);
          awardKey(1); arrowsNorth();
          setTimeout(() => stage.querySelector(".g-room").appendChild(nextControls(1)), 500);
        } else {
          b.classList.add("wrong"); setTimeout(() => b.classList.remove("wrong"), 450);
          showWrong();
        }
      });
      choices.appendChild(b);
    });

    const compass = h("div", { style: "position:relative;width:150px;height:150px;margin:8px 0 4px" }, [
      h("div", { id: "gCompass", style: "position:absolute;inset:0;border:2px solid var(--line);border-radius:50%;display:grid;place-items:center;font-size:13px;color:var(--slate)" }, ["🐾"])]);

    stage.append(h("div", { class: "g-room" }, [
      h("div", { class: "g-station" }, ["Research Station 2 · Animal Movement"]),
      h("h3", {}, ["Predict the Migration"]),
      h("p", { class: "g-story" }, ["The climate is warming. Which direction will most European species move to stay comfortable?"]),
      compass, choices,
      h("div", { class: "g-controls" }, [inlineFb()]),
      hintControl(1, "Cooler temperatures are found toward the poles. Europe's pole is at the top of the map."),
      h("div", { class: "g-feedback", id: "gFb" }),
      sideRail()
    ]));
  }
  function arrowsNorth() {
    const c = document.getElementById("gCompass"); if (!c) return;
    c.innerHTML = "⬆"; c.style.fontSize = "44px"; c.style.color = "var(--good)";
    c.animate([{ transform: "translateY(10px)", opacity: .3 }, { transform: "translateY(-8px)", opacity: 1 }],
      { duration: 700, easing: "cubic-bezier(.2,.8,.2,1)" });
  }

  /* ============================ ROOM 3 ============================ */
  function room3() {
    stage.innerHTML = "";
    const opts = [["🌲", "Forest", false], ["🌾", "Farmland", true], ["🏔", "Mountains", false], ["🏙", "City", true]];
    const picked = new Set();
    let locked = false;
    const grid = h("div", { class: "g-choices multi" });
    opts.forEach(([ic, name]) => {
      const b = h("button", { class: "g-choice", "aria-pressed": "false" }, [
        h("span", { class: "ic" }, [ic]), h("span", {}, [name])]);
      b.addEventListener("click", () => {
        const on = picked.has(name);
        if (on) picked.delete(name); else picked.add(name);
        b.setAttribute("aria-pressed", String(!on));
      });
      grid.appendChild(b);
    });

    stage.append(h("div", { class: "g-room" }, [
      h("div", { class: "g-station" }, ["Research Station 3 · Human Conflict"]),
      h("h3", {}, ["Spot the Conflict Zones"]),
      h("p", { class: "g-story" }, ["An animal is moving into new habitat. Select every landscape where it is most likely to clash with people. (Pick all that apply.)"]),
      grid,
      h("div", { class: "g-controls" }, [
        h("button", { class: "g-btn primary", onclick: () => {
          if (locked) return;
          const want = new Set(["Farmland", "City"]);
          const ok = picked.size === want.size && [...want].every(x => picked.has(x));
          if (ok) {
            locked = true; clearWrong();
            grid.querySelectorAll(".g-choice").forEach(b => {
              const n = b.textContent.trim(); if (want.has(n)) b.classList.add("correct");
            });
            feedback("<b>Correct!</b> Wildlife conflict is most likely where animals move into land heavily used by people — <b>farmland and cities</b>. Forests and mountains have low human modification. <b>Key 3 earned.</b>", true);
            awardKey(2);
            setTimeout(() => stage.querySelector(".g-room").appendChild(nextControls(2)), 500);
          } else {
            grid.querySelectorAll(".g-choice").forEach(b => { b.classList.add("wrong"); setTimeout(() => b.classList.remove("wrong"), 450); });
            showWrong();
          }
        } }, ["Submit selection"]),
        inlineFb()
      ]),
      hintControl(2, "Think about where the human-modification value is highest. Two of these are wild; two are dominated by people."),
      h("div", { class: "g-feedback", id: "gFb" }),
      sideRail()
    ]));
  }

  /* ============================ ROOM 4 ============================ */
  const EXTENT = [-12, 40, 34, 72]; // lonmin, lonmax, latmin, latmax
  // Accept-regions = the three genuinely bright clusters on the committed CRI map
  // (verified against results/analysis.npz). Boxes are generous so a click anywhere
  // in the area counts; the centre is only used for labels.
  const REGIONS = [
    { name: "Alps",                box: [5.5, 15, 44.5, 48] },
    { name: "NE Baltic",           box: [23, 33, 57.5, 61.5] },
    { name: "Poland–Belarus belt", box: [16, 32, 50.5, 56.5] }
  ];
  const SCOTLAND = [-8, -1.5, 55, 59.5];  // the over-water optimal-transport friction artefact
  const SCOTLAND_MSGS = [
    "That's <b>Scotland</b> — a trap. The model piles <b>artificial friction</b> here because it assumes any animal leaving the island must travel huge distances across open sea. In reality (Figure 2a) Scotland's habitat barely gains or loses, so its brightness is an <b>artefact</b>, not a real hotspot. Try the mainland clusters.",
    "<b>Scotland again.</b> Its glow is an <b>over-water artefact</b>: shifting habitat off an island costs the transport step enormous distance, which inflates friction even though the actual habitat change there is minimal (Figure 2a). Look to the mainland.",
    "Careful — <b>Scotland</b> looks bright but shouldn't be picked. The model thinks its wildlife must cross the ocean to move, so it adds <b>false friction</b>; the real habitat gain or loss there is tiny (Figure 2a). Aim for the Alps, the Poland–Belarus belt, or the north-eastern Baltic."
  ];
  let scotPtr = 0;
  const nextScotlandMsg = () => SCOTLAND_MSGS[scotPtr++ % SCOTLAND_MSGS.length];

  function room4() {
    stage.innerHTML = "";
    const found = new Set();
    const map = h("div", { class: "g-map", id: "gMap", role: "img", "aria-label": "Coexistence risk map — click the three brightest predicted hotspots" }, [
      h("img", { src: "assets/img/risk_map.png", alt: "Coexistence Risk Index map of Europe" })
    ]);
    function toLonLat(fx, fy) {
      return [EXTENT[0] + fx * (EXTENT[1] - EXTENT[0]), EXTENT[3] - fy * (EXTENT[3] - EXTENT[2])];
    }
    const inBox = (lon, lat, b) => lon >= b[0] && lon <= b[1] && lat >= b[2] && lat <= b[3];
    function place(label, fx, fy) {
      map.appendChild(h("div", { class: "g-hot", style: `left:${fx * 100}%;top:${fy * 100}%` }));
      map.appendChild(h("div", { class: "g-maplabel", style: `left:${fx * 100}%;top:${fy * 100}%` }, [label]));
    }
    map.addEventListener("click", e => {
      const r = map.getBoundingClientRect();
      const fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
      const [lon, lat] = toLonLat(fx, fy);
      // 1) Scotland — the artefact: explain, don't penalise
      if (inBox(lon, lat, SCOTLAND)) { feedback(nextScotlandMsg(), "info"); return; }
      // 2) an accept-region?
      const reg = REGIONS.find(R => inBox(lon, lat, R.box));
      if (reg) {
        if (found.has(reg.name)) { showAlready(); return; }   // already found → neutral reminder
        found.add(reg.name); clearWrong();
        place(reg.name, fx, fy);
        if (found.size === REGIONS.length) {
          feedback("<b>Excellent!</b> The model's brightest conflict hotspots — the <b>Alps</b>, the <b>Poland–Belarus lowland belt</b>, and the <b>north-eastern Baltic</b> corner — found <b>without any historical conflict data</b>. <b>Final key earned.</b>", true);
          awardKey(3);
          setTimeout(() => stage.querySelector(".g-room").appendChild(nextControls(3)), 500);
        } else {
          feedback(`Hotspot found: <b>${reg.name}</b>. ${REGIONS.length - found.size} to go — look for the other bright clusters.`, true);
        }
        return;
      }
      // 3) genuine miss
      const m = h("div", { class: "g-miss", style: `left:${fx * 100}%;top:${fy * 100}%` });
      map.appendChild(m); setTimeout(() => m.remove(), 600);
      showWrong();
    });

    stage.append(h("div", { class: "g-room" }, [
      h("div", { class: "g-station" }, ["Research Station 4 · Risk Prediction"]),
      h("h3", {}, ["Find the Future Hotspots"]),
      h("p", { class: "g-story" }, ["This is our Coexistence Risk Index — bright = high predicted conflict. Click the three biggest hotspots to confirm the model's forecast."]),
      map,
      h("div", { class: "g-controls" }, [inlineFb()]),
      h("p", { class: "cap", style: "margin-top:10px" }, ["Tip: the brightest bands trace the Alps, the Poland–Belarus lowlands, and the north-eastern Baltic (Gulf-of-Finland) corner. Scotland looks bright too — but click it to see why that's a trap."]),
      hintControl(3, "Look at the Alpine arc, the Poland–Belarus lowlands, and the far north-east around the Gulf of Finland — the brightest clusters. Scotland's glow is a coastal artefact, not a real hotspot."),
      h("div", { class: "g-feedback", id: "gFb" }),
      sideRail()
    ]));
  }

  /* ============================ FINAL ============================ */
  function starRating() {
    const penalty = Math.min(2, Math.floor((state.wrong + state.hints) / 2));
    return 5 - penalty; // 3..5
  }
  function finalScreen() {
    stage.innerHTML = "";
    updateProgress();
    const badges = [
      ["🧬", "Habitat Expert", "You learned how habitat suitability is predicted from climate."],
      ["🦌", "Wildlife Tracker", "You learned how a warming climate shifts animal ranges north."],
      ["🗺️", "Conflict Mapper", "You learned where wildlife and people are most likely to meet."],
      ["🌍", "Conservation Scientist", "You completed the entire Geometry of Coexistence pipeline."]
    ];
    const stars = starRating();
    const wrap = h("div", { class: "g-room" }, [
      h("div", { class: "g-door", id: "gDoor" }, [h("div", { class: "leaf l" }), h("div", { class: "leaf r" })]),
      h("div", { class: "g-final", style: "opacity:0", id: "gFinal" }, [
        h("span", { class: "g-lock", id: "gLock" }, ["🔒"]),
        h("h3", {}, ["Mission Complete!"]),
        h("p", { class: "sub" }, ["You successfully predicted future human–wildlife conflict without using any historical conflict data."]),
        (() => { const g = h("div", { class: "g-badges" });
          badges.forEach((b, i) => g.appendChild(h("div", { class: "g-badge", style: `animation-delay:${i * .12}s` }, [
            h("div", { class: "em" }, [b[0]]), h("h5", {}, [b[1]]), h("p", {}, [b[2]])]))); return g; })(),
        h("div", { class: "g-score" }, ["Research Accuracy"]),
        h("div", { class: "g-stars" }, ["★".repeat(stars) + "☆".repeat(5 - stars)]),
        h("div", { style: "color:var(--slate);font-size:14px;margin:4px 0 20px" }, ["4 / 4 Stations Completed"]),
        h("div", { class: "g-controls", style: "justify-content:center" }, [
          h("button", { class: "g-btn primary", onclick: () => window.scrollTo({ top: 0, behavior: "smooth" }) }, ["Explore the Project Again"]),
          h("button", { class: "g-btn", onclick: () => { Object.assign(state, { room: 0, solved: [false, false, false, false], keys: 0, wrong: 0, hints: 0, notes: [] }); save(); shell(); document.getElementById("game").scrollIntoView({ behavior: "smooth" }); } }, ["Play again"])
        ])
      ])
    ]);
    stage.appendChild(wrap);

    // key-fly + door-open sequence
    const lock = () => document.getElementById("gLock");
    setTimeout(() => {
      const door = document.getElementById("gDoor");
      const finalEl = document.getElementById("gFinal");
      // four keys fly to the lock
      for (let i = 0; i < 4; i++) {
        const fk = h("div", { class: "g-flykey", style: `left:${10 + i * 8}%;top:20%` }, ["🔑"]);
        stage.appendChild(fk);
        setTimeout(() => { fk.style.left = "50%"; fk.style.top = "34%"; fk.style.opacity = "0"; }, 60 + i * 120);
        setTimeout(() => fk.remove(), 1100 + i * 120);
      }
      setTimeout(() => { if (lock()) lock().textContent = "🔓"; }, 700);
      setTimeout(() => { if (door) door.classList.add("open"); }, 900);
      setTimeout(() => { if (finalEl) { finalEl.style.transition = "opacity .8s"; finalEl.style.opacity = "1"; } confetti(); }, 1500);
    }, 200);
  }

  /* elegant, small confetti */
  function confetti() {
    if (matchMedia("(prefers-reduced-motion:reduce)").matches) return;
    const game = root.querySelector(".game");
    const cols = ["#E69F00", "#009E73", "#0072B2", "#D55E00", "#CC79A7", "#c85a2b"];
    const W = game.clientWidth;
    for (let i = 0; i < 44; i++) {
      const c = h("div", { class: "g-confetti", style:
        `left:${Math.random() * W}px;background:${cols[i % cols.length]};transform:rotate(${Math.random() * 360}deg)` });
      game.appendChild(c);
      const dx = (Math.random() - 0.5) * 120, dy = 260 + Math.random() * 220, rot = Math.random() * 720;
      c.animate([{ transform: `translate(0,0) rotate(0)`, opacity: 1 },
        { transform: `translate(${dx}px,${dy}px) rotate(${rot}deg)`, opacity: 0 }],
        { duration: 1600 + Math.random() * 900, easing: "cubic-bezier(.2,.7,.3,1)" });
      setTimeout(() => c.remove(), 2600);
    }
  }

  /* ---------- boot ---------- */
  shell();
})();

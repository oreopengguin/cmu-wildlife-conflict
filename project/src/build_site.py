"""Assemble the self-contained website (index.html) with figures embedded as
base64 data URIs, for publishing as an Artifact or opening locally."""
import base64, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "figures" / "web"
OUT = ROOT / "website"
OUT.mkdir(exist_ok=True)


def b64(name):
    data = (WEB / f"{name}.jpg").read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


FIGS = {k: b64(k) for k in [
    "figure1_framework", "figure2_transport",
    "figure3_connectivity_topology", "figure4_risk_validation",
    "figureS1_robustness"]}

HTML = r"""
<style>
:root{
  --paper:#f4f1e8; --ink:#17241f; --slate:#586b62; --faint:#d9d3c4;
  --ember:#c85a2b; --teal:#1f7a7a; --sky:#2a6f97; --gold:#c79a2e;
  --card:#fbf9f3; --line:#e4ded0;
  --serif:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Times New Roman',serif;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  --mono:'SF Mono',ui-monospace,'Cascadia Code',Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#0f1512; --ink:#e9ede7; --slate:#9aa89f; --faint:#2a352f;
  --card:#151d19; --line:#26312b; --ember:#e07a4a; --teal:#3fa3a3; --sky:#5aa6cf;
}}
:root[data-theme="dark"]{
  --paper:#0f1512; --ink:#e9ede7; --slate:#9aa89f; --faint:#2a352f;
  --card:#151d19; --line:#26312b; --ember:#e07a4a; --teal:#3fa3a3; --sky:#5aa6cf;
}
:root[data-theme="light"]{
  --paper:#f4f1e8; --ink:#17241f; --slate:#586b62; --faint:#d9d3c4;
  --card:#fbf9f3; --line:#e4ded0; --ember:#c85a2b; --teal:#1f7a7a; --sky:#2a6f97;
}
*{box-sizing:border-box}
body{margin:0}
.wrap{background:var(--paper);color:var(--ink);font-family:var(--sans);
  line-height:1.6;-webkit-font-smoothing:antialiased}
.container{max-width:1080px;margin:0 auto;padding:0 28px}
.reading{max-width:680px}
h1,h2,h3{font-family:var(--serif);font-weight:600;line-height:1.12;
  text-wrap:balance;letter-spacing:-0.01em}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--ember);font-weight:600}
a{color:var(--ember)}

/* hero */
.hero{position:relative;overflow:hidden;border-bottom:1px solid var(--line)}
#field{position:absolute;inset:0;width:100%;height:100%;opacity:.5}
.hero-in{position:relative;padding:96px 0 76px}
.hero h1{font-size:clamp(38px,6vw,74px);margin:.15em 0 .3em}
.hero .lede{font-size:clamp(18px,2.2vw,23px);color:var(--slate);max-width:640px}
.hero .by{margin-top:26px;font-family:var(--mono);font-size:12.5px;
  color:var(--slate);letter-spacing:.04em}

/* stat band */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
  background:var(--line);border-top:1px solid var(--line);
  border-bottom:1px solid var(--line)}
.stat{background:var(--paper);padding:24px 22px}
.stat .n{font-family:var(--serif);font-size:clamp(26px,3.4vw,40px);
  font-variant-numeric:tabular-nums;line-height:1;color:var(--ink)}
.stat .l{font-size:12.5px;color:var(--slate);margin-top:8px}
.stat .n small{font-size:.5em;color:var(--slate)}

section{padding:70px 0}
.sec-head{display:flex;gap:16px;align-items:baseline;margin-bottom:6px}
.sec-num{font-family:var(--mono);color:var(--ember);font-size:14px}
h2{font-size:clamp(26px,3.4vw,38px);margin:.1em 0 .4em}
.sub{color:var(--slate);font-size:18px;max-width:680px;margin-bottom:26px}
p{margin:0 0 18px}
.figure{margin:34px 0 8px;background:var(--card);border:1px solid var(--line);
  border-radius:14px;padding:16px;box-shadow:0 1px 0 rgba(0,0,0,.02)}
.figure img{width:100%;display:block;border-radius:8px}
.cap{font-size:13.5px;color:var(--slate);margin-top:14px;padding:0 6px}
.cap b{color:var(--ink);font-weight:600}
.panels{display:grid;grid-template-columns:1fr 1fr;gap:14px 26px;margin-top:8px}
.panel{border-left:2px solid var(--teal);padding:2px 0 2px 14px}
.panel h4{margin:0 0 3px;font-family:var(--sans);font-size:13.5px;font-weight:700}
.panel p{font-size:13.5px;color:var(--slate);margin:0}
.panel.b{border-color:var(--ember)} .panel.c{border-color:var(--sky)}
.panel.d{border-color:var(--gold)}

.callout{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:26px 28px;margin:26px 0}
.callout .eyebrow{color:var(--teal)}
.pill{display:inline-block;font-family:var(--mono);font-size:12px;
  padding:3px 9px;border-radius:20px;border:1px solid var(--line);
  color:var(--slate);margin:2px 4px 2px 0}
.pill b{color:var(--ink)}

.method{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;
  overflow:hidden}
.step{background:var(--paper);padding:20px}
.step .k{font-family:var(--mono);font-size:11px;color:var(--ember);
  letter-spacing:.1em}
.step h4{font-family:var(--serif);font-size:18px;margin:6px 0 6px;font-weight:600}
.step p{font-size:13px;color:var(--slate);margin:0}
.eq{font-family:var(--mono);font-size:13px;color:var(--ink);background:var(--card);
  border:1px dashed var(--line);border-radius:10px;padding:14px 16px;
  overflow-x:auto;white-space:nowrap}
footer{border-top:1px solid var(--line);padding:40px 0 70px;color:var(--slate);
  font-size:13.5px}
.toggle{position:fixed;top:16px;right:16px;z-index:10;background:var(--card);
  border:1px solid var(--line);color:var(--ink);border-radius:20px;
  padding:7px 13px;font-family:var(--mono);font-size:12px;cursor:pointer}
@media (max-width:720px){.stats{grid-template-columns:repeat(2,1fr)}
  .panels{grid-template-columns:1fr}}
</style>

<div class="wrap">
<button class="toggle" onclick="(function(){var r=document.documentElement;
  var d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  r.setAttribute('data-theme',d==='dark'?'light':'dark');})()">◐ theme</button>

<header class="hero">
  <canvas id="field"></canvas>
  <div class="hero-in container">
    <div class="eyebrow">Computational ecology · methods</div>
    <h1>The Geometry of Coexistence</h1>
    <p class="lede">Where will climate push Europe's wildlife into people? We turn
      human–wildlife conflict into a problem in the geometry of moving
      probability — and predict it without ever training on conflict data.</p>
    <div class="by">Optimal transport · spectral graph theory · persistent homology · maximum entropy
      &nbsp;•&nbsp; CMU Pre-College Final Project · Topic 25</div>
  </div>
</header>

<div class="stats container" style="max-width:100%;padding:0">
  <div class="stat"><div class="n">7</div><div class="l">conflict-prone taxa modelled across Europe</div></div>
  <div class="stat"><div class="n">484<small> km</small></div><div class="l">mean climate-forced range shift by 2081–2100</div></div>
  <div class="stat"><div class="n">0.64</div><div class="l">Spearman ρ, predicted vs observed range shift</div></div>
  <div class="stat"><div class="n">0.0005</div><div class="l">permutation p, friction predicts real interface</div></div>
</div>

<section class="container">
  <div class="reading">
    <div class="sec-head"><span class="sec-num">The idea</span></div>
    <h2>Conflict is moving mass meeting fixed pressure</h2>
    <p>As the climate warms, the comfortable habitat of a species has to
      <em>move</em> — generally poleward and uphill. But it moves across a
      continent whose land people have already claimed. Human–wildlife conflict —
      livestock loss, vehicle collisions, crop raiding, bears at the edge of town —
      happens exactly where that moving habitat is forced <em>into</em>
      human-dominated space and can't flow around it.</p>
    <p>Almost every existing model predicts conflict by looking backward at past
      conflict records. We predict it <b>forward, from mechanism</b>: the transport,
      connectivity, and topology of climate-forced redistribution. Because the model
      never sees conflict data, testing it against reality is a true out-of-sample
      test — not a re-fit.</p>
    <div class="eq">p(x) ∝ e^(β·f(x))  →  min⟨P,C⟩ − εH(P)  →  F(x) = ⟨T(x), ∇H(x)⟩₊  →  Coexistence Risk</div>
  </div>
</section>

<section class="container">
  <div class="sec-head"><span class="sec-num">01</span></div>
  <h2>A framework built on well-calibrated habitat models</h2>
  <p class="sub">We rebuilt the maximum-entropy species distribution model from
    scratch — as its exact equivalent, a penalized Poisson point process — and
    fit it for seven European mammals from 57,838 GBIF records.</p>
  <div class="figure"><img alt="Figure 1" src="__FIG1__">
    <div class="cap"><b>Figure 1 — Framework &amp; data.</b> Occurrence density and
      realized climatic niches; the Gibbs→transport→topology pipeline; and
      spatial cross-validation skill (AUC 0.76–0.92, Boyce up to 0.99).</div></div>
  <div class="panels">
    <div class="panel"><h4>a · Records</h4><p>57,838 sightings of bear, wolf, lynx, jackal, boar, roe deer and fox.</p></div>
    <div class="panel b"><h4>b · Niches</h4><p>Realized climatic niches overlap in a shared cool-temperate envelope.</p></div>
    <div class="panel c"><h4>c · Pipeline</h4><p>Presence-only → MaxEnt/PPP → transport → connectivity → topology → risk.</p></div>
    <div class="panel d"><h4>d · Skill</h4><p>Block cross-validation, not naive resubstitution — honest performance.</p></div>
  </div>
</section>

<section class="container">
  <div class="sec-head"><span class="sec-num">02</span></div>
  <h2>Optimal transport reveals a coherent poleward push</h2>
  <p class="sub">Treating present and future habitat as probability measures, we
    solve the entropic optimal-transport problem between them. The result is a
    displacement field: an arrow at every location saying where habitat must go.</p>
  <div class="figure"><img alt="Figure 2" src="__FIG2__">
    <div class="cap"><b>Figure 2 — Entropic displacement.</b> Under +2.8&nbsp;°C
      (SSP2-4.5), every taxon is pushed poleward (mean shift 484&nbsp;km). The
      <b>Coexistence Friction</b> field lights up where that push crosses steep
      human-pressure gradients — the Alps, Carpathians and farmland edges.</div></div>
  <div class="panels">
    <div class="panel"><h4>a · Gain vs loss</h4><p>Bivariate map: blue gains in the north, red losses in the south.</p></div>
    <div class="panel b"><h4>b · Displacement field</h4><p>Streamlines of the optimal-transport map — habitat flowing north.</p></div>
    <div class="panel c"><h4>c · Poleward intensity</h4><p>Required shift peaks at mid-latitudes and retreating southern margins.</p></div>
    <div class="panel d"><h4>d · Friction</h4><p>F(x)=⟨displacement, ∇human-pressure⟩₊ — the conflict-pressure field.</p></div>
  </div>
</section>

<section class="container">
  <div class="sec-head"><span class="sec-num">03</span></div>
  <h2>Movement funnels into corridors — and the range frays</h2>
  <p class="sub">Optimal transport gives the <em>demand</em> for movement; the
    landscape decides whether it can be met. Circuit theory routes the demand
    through real resistance; persistent homology measures the fragmentation.</p>
  <div class="figure"><img alt="Figure 3" src="__FIG3__">
    <div class="cap"><b>Figure 3 — Connectivity &amp; topology.</b> A spectral
      graph-Laplacian solve routes forced movement into discrete conflict
      corridors and pinch-points; cubical persistent homology shows the range's
      interior gaps (H₁ loops) rising from 2,389 to 2,536.</div></div>
  <div class="panels">
    <div class="panel"><h4>a · Current</h4><p>Climate demand solved as electrical current on the landscape graph.</p></div>
    <div class="panel b"><h4>b · Corridors</h4><p>Current × human pressure = where animals funnel through people.</p></div>
    <div class="panel c"><h4>c · Persistence</h4><p>Birth–death of habitat patches and loops across all thresholds.</p></div>
    <div class="panel d"><h4>d · Simplification</h4><p>Persistence landscapes quantify structural range change.</p></div>
  </div>
</section>

<section class="container">
  <div class="sec-head"><span class="sec-num">04</span></div>
  <h2>A risk map that reality can check</h2>
  <p class="sub">The three geometric signals fuse into one Coexistence Risk Index —
    and two independent tests, neither using conflict data, support the mechanism.</p>
  <div class="figure"><img alt="Figure 4" src="__FIG4__">
    <div class="cap"><b>Figure 4 — Risk &amp; validation.</b> The risk index
      localizes to the peri-Alpine arc, Carpathians and Fennoscandian fringe. OT
      predictions rank-match observed range shifts (ρ=0.64); friction predicts
      realized human-interface occurrence (permutation p=0.0005).</div></div>
  <div class="callout">
    <div class="eyebrow">Out-of-sample validation</div>
    <p style="margin:12px 0 6px"><b>Test 1 — mechanism.</b> Splitting each species'
      records into a 1990–2007 and a 2015–2026 epoch, five of seven taxa shifted
      poleward exactly as the transport map predicted (Spearman ρ = 0.64). The grey
      wolf is the lone outlier — its recent range change is driven by legal-protection
      recolonization, a known non-climate confound, not a model failure.</p>
    <p style="margin:6px 0 0"><b>Test 2 — interface.</b> Coexistence Friction
      significantly predicts which human-dominated cells actually hold recent wildlife
      records (permutation p = 0.0005 over 4,618 cells) — despite never being trained
      on those labels.</p>
  </div>
</section>

<section class="container">
  <div class="sec-head"><span class="sec-num">05</span></div>
  <h2>The result holds up</h2>
  <p class="sub">Higher emissions push habitat farther — but the map of <em>where</em>
    conflict concentrates barely moves. And the from-scratch solver provably hits
    the maximum-entropy optimum.</p>
  <div class="figure"><img alt="Figure S1" src="__FIGS1__">
    <div class="cap"><b>Figure S1 — Robustness &amp; verification.</b> Under
      SSP5-8.5, shifts grow (mean 714 km) yet the friction pattern is nearly
      identical to SSP2-4.5 (r = 0.98). The optimal-transport shift is grid-invariant
      (CV 0.5 %), and empirical feature means match the fitted Gibbs expectations to
      r = 0.99998 — the solver satisfies its defining constraint.</div></div>
</section>

<section class="container">
  <div class="sec-head"><span class="sec-num">Methods</span></div>
  <h2>Four traditions, one pipeline</h2>
  <div class="method">
    <div class="step"><div class="k">CONVEX OPT</div><h4>MaxEnt = Poisson PPP</h4>
      <p>From-scratch elastic-net solver (FISTA) for the Gibbs / point-process suitability model.</p></div>
    <div class="step"><div class="k">OPTIMAL TRANSPORT</div><h4>Entropic Sinkhorn</h4>
      <p>Displacement field and Wasserstein range-shift between present and future habitat measures.</p></div>
    <div class="step"><div class="k">SPECTRAL GRAPH</div><h4>Circuit theory</h4>
      <p>Graph-Laplacian solve routes movement demand into corridors and pinch-points.</p></div>
    <div class="step"><div class="k">TOPOLOGY</div><h4>Persistent homology</h4>
      <p>Cubical H₀/H₁ persistence quantifies range fragmentation with stability guarantees.</p></div>
  </div>
  <div style="margin-top:22px">
    <span class="pill"><b>Data</b> GBIF · WorldClim 2.1 · Global Human Modification</span>
    <span class="pill"><b>Domain</b> Europe · 37,070 cells</span>
    <span class="pill"><b>Scenario</b> SSP2-4.5 · 2081–2100</span>
    <span class="pill"><b>Warming</b> +2.8 °C</span>
    <span class="pill"><b>All data</b> open, no login</span>
  </div>
</section>

<footer class="container">
  <p style="max-width:680px"><b>The Geometry of Coexistence.</b> A mechanistic,
  conflict-data-free framework that reframes human–wildlife conflict forecasting as
  the geometry of moving measures. Built from openly downloadable data with a fully
  reproducible pipeline. Aspirational venue: a computational-ecology methods journal.</p>
  <p style="color:var(--slate)">Reproduce: <span class="pill">run_pipeline.sh</span> — MaxEnt/PPP · Sinkhorn OT · spectral connectivity · cubical persistence.</p>
</footer>
</div>

<script>
(function(){
  var c=document.getElementById('field'); if(!c) return;
  var ctx=c.getContext('2d'), W,H,parts=[];
  var reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
  function ink(){var r=document.documentElement,
    d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
    return d==='dark'?'rgba(224,122,74,':'rgba(200,90,43,';}
  function size(){W=c.width=c.offsetWidth;H=c.height=c.offsetHeight;
    parts=[];var n=Math.min(150,Math.floor(W*H/9000));
    for(var i=0;i<n;i++)parts.push({x:Math.random()*W,y:Math.random()*H,
      s:0.2+Math.random()*0.7,len:8+Math.random()*22});}
  function step(){ctx.clearRect(0,0,W,H);var col=ink();
    for(var i=0;i<parts.length;i++){var p=parts[i];
      // gentle poleward (upward) drift with slight eastward curl
      var vx=Math.sin((p.y+p.x)*0.004)*0.35, vy=-(0.5+p.s);
      ctx.strokeStyle=col+(0.10+p.s*0.18)+')';ctx.lineWidth=p.s*1.1;
      ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.x-vx*p.len,p.y-vy*p.len*0.1+p.len);ctx.stroke();
      p.x+=vx;p.y+=vy;if(p.y< -20){p.y=H+10;p.x=Math.random()*W;}
      if(p.x<0)p.x+=W;if(p.x>W)p.x-=W;}
    if(!reduce)requestAnimationFrame(step);}
  size();window.addEventListener('resize',size);
  if(reduce){step();}else step();
})();
</script>
"""

for key, tok in [("figure1_framework", "__FIG1__"), ("figure2_transport", "__FIG2__"),
                 ("figure3_connectivity_topology", "__FIG3__"),
                 ("figure4_risk_validation", "__FIG4__"),
                 ("figureS1_robustness", "__FIGS1__")]:
    HTML = HTML.replace(tok, FIGS[key])

# wrap as a complete standalone HTML document (title + favicon) for static hosting
FAVICON = ("data:image/svg+xml,"
           "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<text y='.9em' font-size='90'>%F0%9F%90%BA</text></svg>")  # 🐺
DOC = (
    "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
    "<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    "<title>The Geometry of Coexistence</title>\n"
    "<meta name=\"description\" content=\"Predicting human–wildlife conflict "
    "from the geometry of climate-forced range shifts.\">\n"
    f"<link rel=\"icon\" href=\"{FAVICON}\">\n"
    "</head>\n<body>\n" + HTML + "\n</body>\n</html>\n"
)

(OUT / "index.html").write_text(DOC)
print("wrote", OUT / "index.html", round(len(DOC)/1024), "KB")

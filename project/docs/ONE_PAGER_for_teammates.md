# Our Project, in Plain English 🐻🐺🦊

*(For teammates — no jargon. One page.)*

## The big question
As the climate warms, animals have to move to stay in comfortable places (cooler, wetter, etc.). But the map of Europe is already covered with cities, farms, and roads. **Our project predicts where animals will be pushed *into* human areas in the future — because that's where "human–wildlife conflict" (car accidents with deer, wolves eating livestock, bears near towns) will happen.**

The cool part: we predict conflict **without ever using conflict data**. We predict it purely from *where the animals' comfortable habitat has to move*. Then we check our prediction against reality.

## What we actually did (the recipe)
1. **Got real data, all free, all from the terminal.**
   - Where 7 animals have been seen in Europe (brown bear, wolf, lynx, golden jackal, wild boar, roe deer, red fox) — ~50,000 sightings from a giant biodiversity database called GBIF.
   - The climate today, and the predicted climate in ~2090 (it's about **+2.8 °C warmer**).
   - A map of how much humans have modified each place (0 = wild, 1 = totally urban).

2. **Built a "comfort map" for each animal** (a *species distribution model*). We re-built the classic method (called MaxEnt) from scratch in code. It learns what climate each animal likes, then colors in every part of Europe by how suitable it is — today and in the future.

3. **Measured how the comfort map has to "move"** from today to the future. We used a beautiful piece of math called **optimal transport** (think: the cheapest way to shovel a pile of sand from one shape into another). This gives us an arrow at every location: *this habitat has to slide this way.*

4. **The key new idea — "Coexistence Friction."** If the arrows point animals *toward* more human-dominated land, that's trouble. We measure exactly that. High friction = future conflict hotspot.

5. **Two more layers of clever math:**
   - **Circuit theory** (like electricity flowing through wires): we find the "pinch-points" where moving animals get funneled through human areas because there's no way around.
   - **Topology** (the math of shapes and holes): we measure how the habitat is *breaking into pieces*, because animals at the fragmented edges bump into people more.

6. **Combined everything into one "Coexistence Risk Index"** — a single map of Europe showing where conflict will emerge.

## How we know it's not just made up (validation)
- **Test 1:** We split the animal sightings into "old" (before 2008) and "recent" (after 2008) and measured which way each animal's range *actually* moved. Our optimal-transport math **predicted the same directions.**
- **Test 2:** Our "friction" measure correctly points to the human-dominated places where animals are *actually* being seen today — far better than chance (we checked with a statistical shuffle test).

## Why it's a big deal
Almost everyone else predicts conflict by looking backward at past conflicts. We predict it **forward, from physics-like principles**, and it works. It combines four different areas of advanced math that are almost never used together, and every piece produces a gorgeous, information-dense figure.

## What each of us can say in the presentation
- *"We turned 'where will animals clash with people' into a geometry problem."*
- *"Optimal transport tells us how habitat must move; we flag it as risky when it moves toward humans."*
- *"We validated the whole thing against real observed range shifts — the model never saw the answer."*

**Deliverables:** 4 flagship figures, a full research manuscript, a reproducible codebase, and a website.

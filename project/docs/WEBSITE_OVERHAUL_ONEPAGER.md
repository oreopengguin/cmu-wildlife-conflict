# What I Did — Website Overhaul & Game (one-pager)

*Plain summary of the second build pass, for teammates.*

## The goal
Take the already-finished research project and turn its Vercel website into a
**breathtaking, interactive, colourblind-friendly, and genuinely fun** experience —
without changing any scientific result and without inventing anything.

## What changed, in plain English

**1. Every figure is now colourblind-friendly.** 🎨
I swapped the 7-species colours to the *Okabe–Ito* palette — the gold-standard set
that people with red-green colourblindness can still tell apart — and added a
**different shape** for each species (circle, square, triangle…) so colour is never
the only clue. The maps already used colourblind-safe colours; I verified them.

**2. New "today vs 2090" habitat maps.** 🗺️
A new figure shows each animal's suitable habitat now and in 2090, with a dashed line
and an arrow showing how far north it must move. On the website this became an
**interactive slider**: drag to wipe between today and 2090, and hover anywhere to
read that spot's habitat score. (I brightened the maps with a clearly-labelled
"relative suitability" stretch so the habitat is actually visible.)

**3. Interactive charts.** ✨
- The **climatic-niche chart** — hover any species' blob to see which species it is
  and how many places it occupies.
- The **model-skill chart** — hover any dot for the exact accuracy numbers.
- I **removed TSS** from the skill figure (it's the wrong metric for this kind of
  data) — keeping the honest AUC and Boyce scores. The TSS numbers are still in the
  data files, just not shown; I wrote down exactly why in `CHANGES.md`.

**4. A much bigger, clearer Results section.** 📊
Six headline stat cards plus five explained findings, all matching the paper's real
numbers. Added a **"Why this matters"** section and a **"Frontiers"** section with six
specific, niche future-research ideas (e.g. *"where to build the first wildlife
bridge," "move predator and prey together," "count the holes in a range as an early
warning"*) — each with a one-line plain-English explanation.

**5. An escape-room game.** 🎮
*"Save the Wildlife Before It's Too Late."* Four research stations that teach the whole
pipeline:
1. **Restore the Pipeline** — drag cards into order (Climate → Habitat → Movement → Risk).
2. **Predict the Migration** — pick which way species move (North).
3. **Spot the Conflict Zones** — choose where conflict happens (Farmland + City).
4. **Find the Future Hotspots** — click the three real hotspots on our risk map.
Finish all four to fly the keys into a lock, open a door, and unlock a
**Mission Complete** screen with badges, a star rating, and confetti. Extras I added:
a **hint button** on every room, a **field notebook** that records what you learned, a
**star score**, **progress that survives a refresh**, and **full keyboard + mobile
support**. Every fact in the game is already on the site — no new science.

## How I built it
- Rebuilt the site as clean, commented, modular files (HTML + CSS + 4 JS modules).
- All interactive data comes from the **real pipeline output** via one export script.
- I rendered the site locally and inspected every piece — hero, charts, maps, results,
  and all four game rooms + the finale — in both **light and dark themes** and on
  **mobile**, fixing issues as I went (e.g. niche blobs were too big; map labels were
  unreadable; the "random" label overlapped a title).

## The honesty guarantee
Nothing was faked. Every number matches `results/summary.json` and the manuscript.
The only "changes" are a labelled display brightening of the maps and the principled
removal of one metric (TSS) — both documented in `docs/CHANGES.md`.

**Live site:** https://cmu-wildlife-conflict.vercel.app/

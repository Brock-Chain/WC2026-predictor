---
name: edge-finder
description: External-signal research skill for the Gamba football predictor. Given an upcoming fixture and a model-vs-market divergence, research everything the goals-only model is BLIND to (qualification stakes, lineups/rotation, injuries, motivation, weather/venue, money flow) and classify whether the divergence is a genuine edge or a model blind spot the market already prices. Use when analyzing upcoming fixtures, explaining a model-vs-market gap, or deciding which divergences are worth a bet.
---

# Edge-finder — research the model's blind spots to validate market divergences

The Gamba model is **goals-only and at its information ceiling**. The Polymarket line is liquid and prices things the model can't see — lineups, injuries, motivation, money flow. So a model-vs-market divergence is **a hypothesis about our blind spot, not a +EV bet** (the project's own Model-vs-Market tab says exactly this). This skill is the research layer that finds the outside information needed to **classify each divergence**: is the market right (blind spot), or do we have a genuine edge?

## The governing rule

**Divergence ≠ value.** Default assumption: a high-liquidity, low-vig market is right and the divergence reflects something the model can't see. To flip a divergence into an edge you must produce a **specific, named piece of information** the market hasn't priced, or identify a structural misprice. No named reason → model blind spot → no bet.

## What the model is blind to (the research targets)

Research these, in rough order of impact:
1. **Competition context & stakes** — qualification math; what each team needs; dead rubber / must-win / playing-for-seeding. *(Engine of most edges.)*
2. **Team news** — confirmed XI / predicted lineups; rotation; who's rested. Lineups drop ~75–90 min pre-KO.
3. **Injuries & suspensions** — key players only.
4. **Motivation & psychology** — dead rubber, must-win desperation, pride, manager's stated intentions, what's at stake.
5. **Environment** — venue (roof vs open-air), weather/heat, altitude, kickoff time, travel & rest.
6. **Tactical & H2H** — style mismatches; current form not captured by the model's goals window.
7. **Market microstructure** — liquidity, vig, line movement, where the money is. Tells you *how much to trust* the price — a thin market is far more mispriceable than a $9M one.

## How to research (source discipline)

- Prefer primary/reliable sources: FIFA, ESPN, BBC, Reuters, official federations, beat reporters, predicted-XI sites, national weather services.
- **Fetch pages; don't trust search snippets** — they have repeatedly garbled standings/results in this tournament. Cross-check ≥2 independent sources.
- Distinguish **CONFIRMED vs rumored**; flag what's unconfirmed.
- Prioritize the **last 24–48h**; the teamsheet is the moment of truth (confirms or *falsifies* the thesis).

## How to classify each divergence (the output)

For each model-vs-market gap, find the external info and decide:
- **MARKET-RIGHT (blind spot)** — divergence explained by info the model can't see and the market already has it → no edge.
- **GENUINE EDGE** — you found info the market hasn't fully priced, or a structural misprice → actionable; state direction + side.
- **UNCONFIRMED** — hinges on team news not yet out → revisit at the teamsheet.

Watch the **systematic-bias tell**: the Gamba model under-rates favorites, over-rates draws, and leans Under. If a slate's divergences all point the same way, that's *one bias showing up N times*, not N edges — filter it out.

## Edge archetypes (checklist of what to look for)

- **Resting favorite** — secured/eliminated favorite rotates a B-team → opponent underpriced vs reputation.
- **Must-win desperation vs a content opponent** — asymmetric motivation (but often resolves to a *draw*).
- **Draw-gravity** — mutual no-stakes (both advance on a draw) → bet the draw / Under / underdog double-chance, not a side to win.
- **Reputation misprice** — market anchored on a famous team's past results; stale once it rotates.
- **Environment** — afternoon heat / open-air → lean Under.
- **Unpriced key absence** — a late injury/suspension the line hasn't moved on.

*(Türkiye v USA, 2026-06-25, was one instance of "resting favorite" — not the template. The template is the research process above.)*

## Getting the numbers in THIS project

- **Model + market, all upcoming games:** `python run_pipeline.py odds` (resolves fixtures → fetches live Polymarket), or read the `window.POLY` blob in `wc2026_predictions.html`, or the live site's **Model vs Market** tab (Refresh for live odds).
- **Polymarket (keyless Gamma API):** `GET https://gamma-api.polymarket.com/events?slug=fifwc-{home}-{away}-{YYYY-MM-DD}` → `markets[].outcomePrices`; de-vig by dividing each price by the sum. Series id `11433`.
- **Model only:** `models/trace.nc` via `footpred.predict.predict(idata, home, away, neutral=...)`.
- **Full pipeline reference:** project `CLAUDE.md` → "Model + Market data pipeline" (all 7 steps, Gamma API details, file paths, data formats, verified `odds` output).
- **Scan ALL bundle markets (totals at every line, team totals, BTTS, spreads, 1st/2nd-half):** `python scripts/edge_scan.py` — prints model-derived markets (from the scoreline grid) vs every Polymarket more-markets market, per fixture.

## Decision & sizing (if betting)

- Bet only a **named** edge; most spots are Pass (correct for a near-zero-vig market).
- **Size to conviction**; smallest stake on the thinnest edge and the sharpest market.
- **Exit a falsified thesis** — when the teamsheet kills the premise, close the position; don't ride it for the swing.
- **Passes are alpha** — declining to follow the model into a fade of a motivated, full-strength favorite is often the best output.

## Validated lessons (update as we go)

- **2026-06-25 (WC2026 final matchday, 6 games):** +$5.54 day; all 3 passes correct; the resting-favorite edge (Türkiye) won; a falsified rotation thesis (Sweden) held to $0 was the one process error. Dead rubbers gravitated to draws (2/6). Model out-RPS'd the market 0.170 vs 0.203 — but only because the slate was rotation-heavy (favorites rested and lost): regime luck, n=6, market still sharper on a normal slate. **Log the mechanism, not the narrative.**
- **2026-06-26/27 (10 games): no actionable edges — Pass across the board was the correct answer.** Key refinement: the **resting-favorite edge only exists when the market hasn't already priced the rotation.** Jordan–Argentina (Scaloni's rotation publicized) → market 83.5% ≈ model 83%; Colombia–Portugal (rest/must-win) → market already loaded Portugal to 52%; Algeria–Austria draw-gravity → market already at 45% draw. Türkiye worked because the market stayed anchored to USA's 7-0; here the markets adjusted. **Always compare the market to a "full-strength" baseline to check whether the rotation is already in the price.**
- **Triangulation technique:** when the Gamba model is the lone outlier on a big divergence, cross-check a second independent model (e.g. Opta's supercomputer). Egypt–Iran: Gamba had Iran 42%, but Polymarket (25%) *and* Opta (24.6%) agreed Iran ~25% — plus Iran had key injuries, brutal US travel restrictions, and must-win pressure. Two independent estimates agreeing *against* our model = our model is wrong (blind spot), not an edge.
- **2026-06-26/27 totals scan (10 games, all bundle markets):** the model is systematically UNDER the market on EVERY goals market — mean O2.5 ≈41% vs market ≈49%, under on 8/10, and the same on BTTS and team totals. This is the model's **under-bias, not an edge**: June 25 confirmed the model under-predicts goals (the ECU–GER under lost as the game went over), and the slate narratives corroborate the market (must-win / strong favourites — Belgium, England, Spain — pile on weak opponents; the model also under-rates favourites' *team totals*). **Do not bet unders / under-BTTS off the model.** The lone reversal (Algeria–Austria: model over 43% vs market 30.5%) is explained by draw-gravity → market correctly low. Possible model upgrade, not a bet: a totals calibration offset that raises expected goals.

## Log per game (for the next review)

`Game · model H/D/A + O2.5 + BTTS · market (de-vigged) + vig + volume · the *named* external reason · archetype · classification (market-right / edge / unconfirmed) · Bet/Lean/Pass · stake · entry · teamsheet-confirmed? · result · P&L · actual mechanism`

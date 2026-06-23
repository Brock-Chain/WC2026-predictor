# Plan — "Model vs Market" (Polymarket) tab

> Status: **PLAN ONLY — not built.** Awaiting decisions on the open questions below.
> Researched + live-verified 2026-06-22.

## What it is

A new tab — alongside **All / Upcoming / Results / Method** — that surfaces where our
Bayesian double-Poisson 1X2 probabilities **disagree** with Polymarket's market-implied
probabilities. Framed as a *"where do we differ from a sharp market, and why"* lens —
**analysis/hypotheses, never betting tips.** Existing tabs are untouched.

## Feasibility — verified, free, easy

Checked live against `gamma-api.polymarket.com` on 2026-06-22:

- WC2026 **per-match 1X2 events exist**: slug `fifwc-{home3}-{away3}-{YYYY-MM-DD}`, each with
  exactly 3 binary YES/NO markets (Home / Draw / Away) mapping 1:1 onto our P(h/d/a).
- Gamma `outcomePrices[0]` **already equals the CLOB midpoint** (e.g. Portugal 0.825 / Draw
  0.125 / Uzbekistan 0.045) → read probabilities directly, **keyless GET, no wallet/CLOB/auth**.
- ~34 keyless GETs per build (≈33 group matches + 1 winner event) — far under rate limits.
- `requests` is already a dependency; `data/raw/` is already gitignored; `render_report`
  already degrades gracefully on missing optional data; the tab mechanism (`setFilter` +
  `body[data-filter=…]` CSS) is already proven by the Method tab. **No CSP `<meta>` is emitted**
  — the CSP is host-enforced, so the only rule is "no runtime fetch", satisfied by a build-time bake.

**Honest read on edge:** an exploitable edge is **unlikely to be real**. Our model is goals-only
(no lineups/injuries/money-flow) and at its information ceiling; the WC market is liquid and prices
what we can't see. So most divergences mean *the market is right and we're missing info.* The
feature's value is the divergence lens itself, not "+EV bets."

## Architecture (fits our constraints exactly)

Build-time fetch → cache to JSON → bake into HTML. **Zero runtime fetch.**

```
run_pipeline.py odds        # NEW verb: fetch Polymarket odds → data/polymarket_odds.json
run_pipeline.py report      # loads the cached JSON (try/except → tab simply absent if missing)
run_pipeline.py update      # best-effort odds fetch folded in (never in `all`, never blocks core build)
```

The fetcher lives **outside** the CC0 core (never imported by data/model/predict), so a Polymarket
or network failure can never break the model pipeline.

## Phases

| # | Deliverable | Files |
|---|---|---|
| 1 | **Fetcher** `fetch_polymarket_odds(fixtures)` — build per-match slug, keyless GET Gamma, `json.loads()` the double-encoded `outcomes`/`outcomePrices` strings, identify Home/Draw/Away by `groupItemTitle`, normalize `p_i = price_i / S` (proportional de-vig), store `vig=S−1`, `volume`, `fetched_at`. Home/away slug-order fallback. One-time `/public-search` discovery pass to verify FIFA 3-letter codes. Per-fixture fail-soft → `None`. | **NEW** `src/footpred/polymarket.py` |
| 2 | **Cache + wiring** — write `data/polymarket_odds.json`; add `cmd_odds()` + `odds` verb; best-effort fetch in `cmd_update`; keep out of `all`. | `run_pipeline.py`, (cache) `data/polymarket_odds.json` |
| 3 | **Join + edge math** — load cache (fail-soft), join market rows to upcoming preds by unordered pair + date (reuse `sync_played_results` idiom so orientation self-corrects). Group-stage upcoming only. Per outcome: `edge = p_model − p_market` (pp), `EV% = p_model/p_market − 1`, illustrative quarter-Kelly. Gate on `|vig|` + `volume`; min `p_market` floor before ranking. | `src/footpred/report.py` (`render_report`) |
| 4 | **The tab UI** — `_value_section(rows, asof)` cloning the Method-tab pattern: prominent disclaimer panel, then a "Model vs Market" table (fixture, outcome, p_model, p_market, edge pp, EV%, vig, volume, confidence). 5th nav button `Value`; CSS mirrors `.method`; inline-SVG mini-bars, **no new JS/network**. | `src/footpred/report.py` (`_value_section`, nav, CSS) |

## Value math (the formulas we'd implement)

- Market implied prob (de-vig, proportional): `p_market_i = price_i / Σ price`, with overround `vig = Σ price − 1`.
- Edge (percentage points): `edge_i = p_model_i − p_market_i`.
- Expected value of a unit YES position: `EV_i = p_model_i / p_market_i − 1`.
- Illustrative stake (NOT advice): quarter-Kelly `f = 0.25 · max(0, (p_model_i − p_market_i)/(1 − p_market_i))`, small cap.
- Read straight from Gamma midpoint — **no** bid/ask/spread call. Quality signal is `vig` + `volume`.

## Risks (and mitigations)

- **Edge is probably illusory** — goals-only vs a sharp liquid market. UI must say so; frame as hypotheses, not value. *(biggest ethos risk: reading as a tipster)*
- **Favourite-longshot bias** — `EV% = p_model/m − 1` blows up as `m→0`, so draws/underdogs dominate any |EV| ranking with noise. Mitigate: min `p_market` floor + show edge in pp alongside EV%.
- **Slug/name-code fragility** — depends on Polymarket's home/away choice, kickoff-date timezone, exact FIFA 3-code (only ~8/48 verified live). Mitigate: discovery pass + home/away swap fallback + per-fixture fail-soft. Watch Turkey=TUR vs "Türkiye", Curaçao diacritic.
- **Double-encoded JSON** — `outcomes`/`outcomePrices`/`clobTokenIds` are stringified arrays; forgetting `json.loads()` is the most likely bug. `outcomePrices` is `null` for placeholder slots — guard it.
- **Static snapshot drift** — odds move; a baked page can freeze a stale/illiquid quote into a fake edge. Mitigate: `as of` stamp + vig/volume gating.
- **ToS / legal / responsible-gambling** — Polymarket data is personal/non-commercial, no scraping/reselling. Keep fetcher out of core, attribute source, frame as education, Kelly illustrative only, likely gitignore the cache.
- **Knockout markets differ** — moneyline 'win' may settle on ET/penalties, not regulation 1X2. Scope the tab to **group-stage** for an apples-to-apples comparison.
- **Multiple comparisons** — ~100 comparisons; some "edges" appear by chance. Present as exploratory.

## Decisions to confirm before building

1. **Cache policy** — gitignore `data/polymarket_odds.json` (regenerate per build, ToS-conservative — *recommended*) or commit it for reproducible/offline builds?
2. **Scope** — per-match 1X2 only (*recommended*), or also add the title-odds model-vs-market table (winner market vs our `simulate_tournament` p_champion) in the same tab?
3. **Kelly column** — show the illustrative quarter-Kelly stake (risks reading as advice even when labelled), or drop it and keep edge + EV% + divergence only?
4. **Quality thresholds** — confirm `|vig|` cutoff (~0.05 vs 0.08), a min-volume grey-out, and the min `p_market` floor for ranking.
5. **Pipeline** — separate `odds` verb only, or also best-effort fetch inside `update`? *(recommended: both — separate verb + best-effort in update, never in `all`)*
6. **Tab label** — "Value" vs "Market" vs "Model vs Market"?

## Recommendation

**GO — but ship it as a "Model vs Market" divergence explorer, not a value/betting tab.** The build
is cheap, free, low-risk, reuses proven patterns, and touches zero existing tabs. Data access is
verified and trivial. The honest caveat (no real edge expected) makes it a good fit for the project's
honest-about-uncertainty ethos — *interesting, not actionable.* Confirm the six decisions above
(especially #1 cache policy and #2 scope) before implementation.

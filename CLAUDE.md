# CLAUDE.md — Gamba Project (WC2026 Football Predictor)

Bayesian double-Poisson WC2026 match predictor (goals-only, MCMC/PyMC). Full overview in [README.md](README.md).
Betting / edge research uses the **`edge-finder`** skill (`.claude/skills/edge-finder/SKILL.md`), which references the data pipeline below.

---

# Model + Market data pipeline (reference)

Mapped via codebase recon; the `odds` command was **verified working on 2026-06-26**.

## Quick routes to current model + market numbers

- **`python run_pipeline.py odds`** → resolves fixtures + fetches LIVE Polymarket prices, prints per-match `H/D/A` + volume to stdout. *(Fastest for just the numbers.)*
- **`python run_pipeline.py render`** → regenerates `wc2026_predictions.html` with model + market baked into a `window.POLY` JSON blob (uses committed trace, no refit; ~1–2 min).
- **Live site:** https://wc-2026-predictor-pied.vercel.app/ → "Model vs Market" tab → Refresh. *(WebFetch can't read the market column — it's client-rendered JS; use `odds` or the Gamma API instead.)*

Verified `odds` output (2026-06-26). The `H/D/A` values are **raw Polymarket `outcomePrices`** (overround ≈ 1.016 → de-vig by dividing each by the sum):

```
2026-06-26  Uruguay v Spain     H/D/A=0.135/0.255/0.605  vol=$7.0M  more=Y
2026-06-26  New Zealand v Belgium  H/D/A=0.065/0.115/0.815  vol=$1.1M  more=Y
...
[odds] N matches, M title teams, overround=1.016
```

## 1. Where model predictions are generated and stored

- **MCMC trace:** `models/trace.nc` (35MB NetCDF) — posterior samples of attack/defense strengths, home advantage, intercept. Loaded by `footpred.model.load_trace()` → `az.InferenceData`.
- **Prediction engine:** `src/footpred/predict.py` — `predict(idata, home_team, away_team, neutral=bool, posterior_spread=True)` → `Prediction` object with full scoreline grid, P(home/draw/away), expected goals, over 2.5, BTTS.
- **Fixtures input:** `data/wc2026_fixtures.csv` — schema `stage,group,date,time_et,home_team,away_team,home_score,away_score`. Upcoming = blank scores; played = filled from Polymarket live results.
- **No cached predictions JSON** — model outputs are computed on-the-fly from the trace.

## 2. How the live site gets its data

- **Build-time:** `run_pipeline.py report` generates `wc2026_predictions.html` (1.9MB), embedding: all match predictions (`footpred.report.build_predictions()`), resolved Polymarket slugs/identifiers (`footpred.polymarket.resolve_odds()`), a baked price snapshot (fallback), and full tournament simulations.
- **Runtime:** inline `_MARKET_JS` (in `report.py`, ~line 1778) — the browser fetches LIVE prices from the Gamma API on load, falls back to the baked snapshot, de-vigs, computes edges, renders tables.
- **Deploy:** `public/index.html` (copy of `wc2026_predictions.html`) served by Vercel; config in `vercel.json`. A GitHub Actions cron (`.github/workflows/refresh.yml`, every 2h) re-renders with live results.

## 3. Polymarket data fetching & joining

- **Module:** `src/footpred/polymarket.py`. Base URL `https://gamma-api.polymarket.com`, **keyless**. WC2026 series id `SERIES_ID = 11433`.
- **Build-time `resolve_odds()`** (~line 227): `GET /events?series_id=11433&closed=false&limit=100&offset=0`; match per-match events by regex `^fifwc-[a-z]+-[a-z]+-\d{4}-\d{2}-\d{2}$` (e.g. `fifwc-uruguay-spain-2026-06-26`); extract `groupItemTitle` (1X2 Home/Draw/Away) and `question` (BTTS / O-2.5 from the `-more-markets` bundle); resolve title market via `GET /events?slug=world-cup-winner`; bake into a `window.POLY` blob.
- **Runtime (browser JS):** batch-fetch open events by slug (15/request): `GET /events?slug=<s1>&slug=<s2>...`; parse `outcomePrices` JSON array; de-vig; edges = `model_prob − market_prob` (percentage points).

## 4. Fastest route to current numbers (e.g. June 26/27)

- **A)** Live site → Model vs Market tab → Refresh (or inspect `window.POLY` in browser console).
- **B)** `python run_pipeline.py render` (committed trace + live odds → HTML).
- **C)** Python: load trace → `predict.predict(...)` per fixture; `polymarket.resolve_odds(targets, teams)` for market.

## 5. Pipeline execution (`run_pipeline.py`)

```
data                  download + clean historical data
fit                   fit MCMC model → models/trace.nc
predict "Home" "Away" single-fixture demo
report                render HTML with model + live odds
odds                  resolve + print Polymarket markets (stdout)
render                re-render only (no refit, load Polymarket)
all                   data → fit → report
update                redownload data → refit → report
```

## 6. Data formats

- **Gamma per-match event:** `{ slug, title, volume, teams[], markets:[{ groupItemTitle, outcomePrices:"[Yes,No]" }] }`.
- **Baked `window.POLY`:** `{ asof, matches:[{ home, away, date, slug, moreSlug, homeGit, drawGit, awayGit, bttsQ, o25Q, vol, snap:{h,d,a,btts,o25}, model:{h,d,a,btts,o25} }], title:{ slug, sum, teams:[{team,git,snap,model}] } }`. *(JSON examples illustrative.)*

## 7. File path quick reference

| Purpose | Path |
|---|---|
| Fixtures (schedule + scores) | `data/wc2026_fixtures.csv` |
| Fitted MCMC trace | `models/trace.nc` |
| Model code | `src/footpred/model.py` |
| Prediction code | `src/footpred/predict.py` |
| Polymarket integration | `src/footpred/polymarket.py` |
| HTML report generator | `src/footpred/report.py` |
| Pipeline orchestrator | `run_pipeline.py` |
| Generated HTML (local) | `wc2026_predictions.html` |
| Public mirror | `public/index.html` |
| Deployed site | https://wc-2026-predictor-pied.vercel.app/ |

## Summary

Model predictions live in the committed `trace.nc` and are computed on demand via `predict()`. Polymarket data is fetched live from the **keyless Gamma API (series 11433)**. The HTML bakes model probs + resolved market identifiers at build time, then fetches live prices client-side and computes edges in the browser. For current numbers: **`python run_pipeline.py odds`** (or `render`), or the live site's Model-vs-Market tab. There is no cached predictions file — everything derives from `trace.nc` + the live Gamma API.

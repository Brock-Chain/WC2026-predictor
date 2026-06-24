# Football Match Outcome Predictor

A Bayesian hierarchical Poisson model (Dixon–Coles lineage) that predicts
men's international football match outcomes — not a single scoreline, but a
**full probability distribution**: P(home win / draw / away win), most-likely
scorelines, expected goals, and over/under — fit via **MCMC** (PyMC).

Trained on the CC0 [`martj42/international_results`](https://github.com/martj42/international_results)
dataset (~49k matches, 1872→2024), filtered to **2018→now**.

> **Why MCMC over a point estimate?** The posterior propagates parameter
> uncertainty into every prediction, so the scoreline grid reflects genuine
> confidence — exactly the distribution behind the inspiration reel.

## The model

Each team has latent **attack** and **defense** strengths (hierarchical, shrunk
toward a shared mean). Goals are Poisson; a single global **home-advantage**
term applies only at non-neutral venues (gated by the dataset's `neutral` flag):

```
log λ_home = intercept + home_adv·(1 − neutral) + atk[home] − def[away]
log λ_away = intercept                          + atk[away] − def[home]
home_score ~ Poisson(λ_home),  away_score ~ Poisson(λ_away)
```

Guiding principle: **start simple (vanilla double-Poisson); let the backtest
justify every added complication** (Dixon–Coles low-score correction,
time-decay weighting, time-varying strengths).

## Layout

```
src/footpred/
  data.py        download · clean · filter (2018+) · team normalization · encoding
  model.py       PyMC double-Poisson model + MCMC fit + ArviZ diagnostics
  predict.py     posterior → scoreline grid → P(W/D/L), xG, over/under
  backtest.py    temporal (no-leakage) backtest · RPS / log-loss / Brier · calibration
  baselines.py   Elo + naive baselines to benchmark against
  fixtures.py    WC2026 fixture loader
  simulate.py    Monte-Carlo group advancement + full-tournament title odds
  polymarket.py  build-time Polymarket odds resolver (optional, fail-soft)
  report.py      standalone HTML deliverable — All / Upcoming / Results /
                 Bracket / Model-vs-Market / Method tabs
notebooks/       01 explore/clean · 02 fit · 03 backtest
tests/           data-cleaning + metric correctness
run_pipeline.py  CLI: data | fit | predict | report | odds | all | update | render
```

## Quickstart

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows;  source .venv/bin/activate on *nix
pip install -e ".[dev]"

python run_pipeline.py data                 # download + clean → data/processed/
python run_pipeline.py fit                  # fit MCMC, save models/trace.nc
python run_pipeline.py predict "Brazil" "Haiti"
python run_pipeline.py report               # → wc2026_predictions.html
python run_pipeline.py odds                 # resolve live Polymarket markets
python run_pipeline.py render               # re-download data + re-render, NO refit
```

Run the tests with `pytest`.

> **Sampler note:** fitting uses [`nutpie`](https://github.com/pymc-devs/nutpie)
> with the **numba** backend, which JIT-compiles the model via LLVM and needs
> **no C/C++ compiler** (handy on Windows without MSVC/MinGW). It falls back to
> PyMC's default sampler automatically if nutpie is unavailable.

## Validation

`footpred.backtest` does an **expanding-window temporal backtest** (train on
≤T, score T+1; no leakage) reporting **RPS** (primary, ordered 1X2),
**log-loss**, **Brier**, and a calibration table — benchmarked against **Elo**
and a naive baseline. See `notebooks/03_backtest.ipynb`.

## Results

**Temporal backtest** (expanding window, folds at 2024/2025/2026, ~2,570 scored
matches, no leakage). Lower is better on all three:

| Model | RPS | log-loss | Brier |
|---|---|---|---|
| **Bayesian double-Poisson (MCMC)** | **0.166** | **0.860** | **0.506** |
| Elo (home-adv) | 0.182 | 0.937 | 0.547 |
| Naive (home-win prior) | 0.228 | 1.057 | 0.637 |

The Bayesian model beats Elo on every metric and is **well-calibrated** —
predicted home-win probability tracks the empirical rate closely across all
deciles. On the **WC2026 group stage** it called **24/39 (62%)** of played
matches correctly (1X2).

Fit diagnostics (full run, 1000 draws × 4 chains): **0 divergences**;
`home_adv`, `sd_att`, `sd_def` all R-hat ≈ 1.00. The global `intercept` mixes
slowly (R-hat ≈ 1.10) due to the usual weak identifiability against the
zero-centered team strengths — it doesn't affect predictions.

## Phases

| Phase | Deliverable |
|---|---|
| 0 | Repo scaffold, deps, git |
| 1 | Data pipeline — download, clean, filter to 2018+, normalize teams |
| 2 | Bayesian double-Poisson model, MCMC fit, convergence checks |
| 3 | `predict(team_a, team_b, neutral)` → full distribution |
| 4 | Temporal backtest + Elo baseline + metrics/calibration |
| 6 | **WC2026 HTML deliverable** — predictions for every match, played + upcoming |
| 7 | **Bracket** tab, chronological **Results**, **Model vs Market**, hosting |

## Model vs Market (Polymarket)

A "where do we disagree with a sharp market" lens — **not** a betting tool. The
build resolves each upcoming fixture to its Polymarket event (via the keyless
[Gamma API](https://gamma-api.polymarket.com)) and bakes our model probabilities
+ the resolved market identifiers into the page. The page's JS then fetches
**live** prices straight from Polymarket in your browser (CORS-open, keyless),
de-vigs them, and shows the per-match 1X2 / BTTS / Over-2.5 and title-odds
divergences — with a **Refresh** button and a ~10-minute auto-update.

> The model is goals-only and at its information ceiling; the WC market is liquid
> and prices things we can't see (lineups, injuries, money flow). So a divergence
> almost always means *the market knows something we don't* — a hypothesis about
> our blind spots, not a +EV bet. The tab says so, prominently.

The resolver lives **outside** the model core and is fully fail-soft: if
Polymarket is unreachable the tab simply degrades, and the model pipeline is
never affected.

## Hosting & auto-refresh

The page is a single static file, hosted on **Vercel** (serving `public/`), with
two independent refresh loops so it stays current with **no local runs**:

- **Odds** refresh *client-side* — the browser pulls live Polymarket prices on a
  ~10-min timer + the Refresh button. No redeploy needed.
- **Results / forecast** refresh via a **GitHub Actions** cron
  (`.github/workflows/refresh.yml`, every 2h + manual): it pulls **live results
  from Polymarket** (settled scores in real time — martj42 is only the
  historical/training feed and lags live games), regenerates the page, and
  pushes — Vercel's Git integration auto-deploys. It **re-renders only**
  (`run_pipeline.py render`), reusing the committed `models/trace.nc`, with no
  martj42 download and no PyMC, so it runs in ~1-2 min. (GitHub's scheduler can
  lag 15-60 min, so a result appears within roughly that window of full-time.)

Refitting the model (`run_pipeline.py update`) stays an occasional **local** step;
commit the refreshed `trace.nc` when the model changes.

**One-time setup:** create a Git remote, push, then in Vercel "Add New Project" →
import the repo → Framework **Other**, Output Directory **`public`**, Build
Command empty (already encoded in `vercel.json`). Add a GitHub repo secret only
if you switch the workflow to deploy via the Vercel CLI; the default uses the
push-based Git integration and needs no secrets.

## Notes

- Source data is **CC0** — free to use and redistribute.
- The Instagram reel that seeded this is the *inspiration/target output*, not
  the method source; the method is reconstructed standard football analytics.
- Decisions left to the backtest: friendlies in/out, Dixon–Coles vs vanilla,
  static vs time-varying strengths, hard 2018 cut vs time-decay weighting.

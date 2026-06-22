---
title: Football Match Outcome Predictor
date: 2026-06-21
type: idea
status: draft
category: Technology
tags: [data-science, machine-learning, bayesian, poisson, mcmc, football, soccer, sports-analytics, prediction, python, pymc, data-cleaning, backtesting, portfolio]
priority: medium
sessions:
  - "[[Sessions/2026-06-21-football-match-predictor]]"
---

# Football Match Outcome Predictor

**Captured**: 2026-06-21
**Category**: Technology
**Status**: Draft
**Sessions**: [[Sessions/2026-06-21-football-match-predictor|Initial ideation & method scoping →]]
**Dual goal**: Learn Bayesian modeling + MCMC **AND** produce predictions accurate enough to trust
**Ambition**: Replicate the reel's core model **+** wrap it in a real pipeline with backtesting

## The Idea

Build a model that predicts the likely outcome of a men's international football match — not just a single scoreline, but a **full probability distribution**: P(home win / draw / away win), most-likely scorelines, and over/under. Train it on the public-domain `martj42/international_results` dataset (~49k matches, 1872→2024), cleaned and filtered to **recent, relevant** matches (2018→now).

Seeded by an Instagram reel (@rbkespinosa) that predicted **Brazil vs Haiti (World Cup 2026)** using **MCMC**. The reel shows the *result*, not the *method* — so this project is **reverse-engineering the standard technique behind it**, not copying a published recipe.

> **Two halves, both explicitly in scope:**
> 1. **Data pipeline** — import → clean → filter to recent matches.
> 2. **Model** — Bayesian hierarchical Poisson fit via MCMC → predictions with uncertainty, then **backtested** for real accuracy.

## Why It Matters

- **Learns a genuinely useful method.** Bayesian hierarchical modeling + MCMC (PyMC/Stan) is a transferable, portfolio-grade skill — far more than a black-box classifier.
- **The output is a distribution, not a guess.** That's the whole appeal of the reel: you get calibrated uncertainty (P(win), scoreline grid), not a flat "2–1."
- **Free and clean source data.** CC0 license, well-maintained, four linked CSVs. No scraping, no licensing friction.
- **Demand is proven.** The reel's comments are full of people begging for a "guía" — replicating it well is both a learning project and a shareable artifact.

---

## Source Material

### Dataset — [`martj42/international_results`](https://github.com/martj42/international_results)

License: **CC0-1.0** (public domain). Four linked CSVs:

| File | What it gives | Key columns |
|---|---|---|
| `results.csv` | Core — **49,398** men's internationals, **1872→2024** | `date`, `home_team`, `away_team`, `home_score`, `away_score`, `tournament`, `city`, `country`, `neutral` |
| `shootouts.csv` | Penalty-shootout winners (scores in `results` **exclude** shootouts) | `date`, teams, `winner`, `first_shooter` |
| `goalscorers.csv` | Goal-level detail | `scorer`, `team`, `own_goal`, `penalty` |
| `former_names.csv` | Historical → current team name mapping |

**Excludes**: Olympics, B-teams, U-23, league select teams.

#### Data quirks that drive the cleaning step
- **Team names are current** (historical "Ireland" → "Northern Ireland") — so cross-team continuity already handled, but verify against `former_names.csv`.
- **`country` reflects the name at match time** (1950s Ghana = "Gold Coast") — don't treat `country` as a stable key.
- **`neutral` flag is load-bearing** — it gates home advantage. A "home" team at a neutral venue gets no home boost. Must be respected in the model, not dropped.
- Scores are **full-time, pre-shootout** — join `shootouts.csv` only if modeling knockout progression; for goals-based modeling, use `results` scores as-is.

### Inspiration — Instagram reel (@rbkespinosa)

- **Subject**: Brazil vs Haiti, World Cup 2026 — a predicted scoreline distribution.
- **Method (per commenter clarification)**: **MCMC** — "un método que sirve para estimar distribuciones de probabilidad... calcular numéricamente ciertas probabilidades."
- **Tags**: #machinelearning #cienciadedatos #mundial2026
- **Key point**: the reel demonstrates the *output*, withholds the *how*. We reconstruct the method from first principles (standard football-analytics technique), we are **not** following the reel's own steps.

---

## The Method (Reconstructed)

MCMC + scoreline prediction ≈ a **Bayesian hierarchical Poisson model**, the Dixon–Coles lineage. The standard recipe:

1. **Latent strengths per team** — each team gets an **attack** and a **defense** parameter (hierarchical: shrunk toward a league-wide mean).
2. **Goals ~ Poisson** — expected goals for team A vs B = `exp(intercept + home_adv·home + attack_A − defense_B)`. Model home and away goals separately.
3. **Home advantage** — a single global term, **gated by the `neutral` flag** (zero boost at neutral venues).
4. **(Optional) Dixon–Coles correction** — adjusts the independence assumption for low-scoring correlated outcomes (0–0, 1–0, 0–1, 1–1), which vanilla double-Poisson gets slightly wrong.
5. **Fit via MCMC** (PyMC or Stan / `cmdstanpy`) — sample the posterior over all attack/defense/home params.
6. **Predict** — for a fixture, simulate from the posterior → a **scoreline probability grid** → collapse to P(win/draw/loss), expected goals, over/under 2.5, etc.

**Why MCMC over a point estimate:** the posterior propagates parameter uncertainty into the prediction, so the scoreline grid reflects genuine confidence — exactly the distribution the reel sells.

### Likely stack (decide pre-build)
- **Python** + pandas (cleaning) · **PyMC** (model + MCMC; ArviZ for diagnostics) — Stan/`cmdstanpy` as the alternative.
- Notebook-first for exploration; optionally a small CLI/function `predict(team_a, team_b, neutral=False)` for the reusable-predictor layer.

---

## Locked Decisions (This Session)

| Decision | Outcome |
|---|---|
| **Recency filter** | **2018 → now** (~two World Cup cycles; most reflective of current squads/form) |
| **Ambition** | **Replicate the reel's model** *and* **build the full pipeline + backtest** (a mix, not one or the other) |
| **Intent** | **Learning/portfolio** *and* **predictions you'd actually trust** (dual goal) |
| **Model family** | Bayesian hierarchical Poisson (Dixon–Coles lineage) via MCMC |
| **Home advantage** | Modeled, gated by `neutral` flag |

## Scope Sketch

**v1 — Replicate + validate the core**
- Clean `results.csv`, filter to 2018→now, normalize teams (cross-check `former_names.csv`), respect `neutral`.
- Fit double-Poisson via MCMC in PyMC; check convergence (R-hat, trace plots via ArviZ).
- Reproduce a reel-style single-fixture prediction (scoreline grid + P(W/D/L)).

**v1.5 — Reusable predictor**
- Wrap into `predict(team_a, team_b, neutral)` returning the full distribution for any fixture.

**v2 — Make it trustworthy (backtest)**
- Held-out **temporal backtest** (train on ≤T, predict T+1 window; no leakage).
- Metrics: **log-loss / Brier** on W/D/L, **RPS** (ranked probability score — the standard for ordered 1X2 outcomes), calibration plots.
- Compare against baselines: bookmaker-implied odds (if available), **Elo**, naive home-team-wins.
- Consider Dixon–Coles low-score correction and **time-decay weighting** if accuracy demands it.

---

## Open Questions (Decide During Build)

### Data / filtering
- [ ] Is a hard 2018 cut right, or add **exponential time-decay weighting** within that window (Dixon–Coles style)? Recency answer was "since 2018" — revisit if rare matchups are starved of data.
- [ ] Include only competitive matches, or friendlies too? Friendlies are noisier (rotated squads) but add volume.
- [ ] Tournament weighting — should a World Cup match inform strength more than a friendly?

### Modeling
- [ ] Vanilla double-Poisson vs **Dixon–Coles correction** vs bivariate Poisson — start simple, add if backtest shows miscalibration on low scores.
- [ ] Static team strengths vs **time-varying** (strengths drift across the window). Time-varying is more correct, more complex.
- [ ] How to handle **new/rarely-seen teams** with little recent data (hierarchical shrinkage helps but watch the tail).
- [ ] PyMC vs Stan — PyMC likely (pure-Python, ArviZ diagnostics).

### Validation
- [ ] Backtest window design (rolling vs expanding) and the exact metric set (RPS + log-loss + calibration).
- [ ] Source of bookmaker odds for a benchmark, or skip and benchmark against Elo only.

### Reach (later)
- [ ] World Cup 2026 focus — predict actual upcoming fixtures (the reel's use case).
- [ ] A shareable artifact (own version of the reel) once backtest accuracy is credible.

---

## Next Steps

- [x] Understand both source materials (dataset + reel) ✓ *2026-06-21*
- [x] Lock recency filter, ambition, intent ✓ *2026-06-21*
- [x] Identify the method behind the reel (Bayesian Poisson + MCMC) ✓ *2026-06-21*
- [ ] Pick stack (PyMC likely) — pre-build
- [ ] **Spin up separate repo** for the build
- [ ] Use this idea note as the spec/source for that build
- [ ] Phase the build: clean+filter → fit MCMC → reusable predictor → backtest

## Related Ideas

- *(none yet logged)*

## Notes

- This idea lives in **Stuff** (ideation only); the build happens in a **separate repository** using this note as spec.
- The reel is the **inspiration/target output**, not the method source — the method is reconstructed standard football analytics (Dixon–Coles / Bayesian Poisson).
- Source data is **CC0** — free to use, redistribute, and build on.
- Guiding principle: **start simple (double-Poisson), let the backtest justify every added complication** (Dixon–Coles, time-decay, time-varying strengths).

---
*Last updated: 2026-06-21 — after session [[Sessions/2026-06-21-football-match-predictor|2026-06-21]]*

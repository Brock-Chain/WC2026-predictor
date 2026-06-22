---
date: 2026-06-21
type: session
related_idea: "[[Ideas/Technology/Football Match Outcome Predictor]]"
tags: [data-science, machine-learning, bayesian, poisson, mcmc, football, sports-analytics, prediction, ideation, method-scoping]
participants: [user, claude]
---

# Session — Football Match Outcome Predictor · Initial Ideation & Method Scoping

**Date**: 2026-06-21
**Idea**: [[Ideas/Technology/Football Match Outcome Predictor]]
**Goal**: Understand two source materials (a football dataset + an Instagram reel), identify the modeling method behind the reel, and lock scope for a predictor project.

## How We Started

User brought two links and asked me to study both for context:
1. **GitHub** — `martj42/international_results`, ~50k international football match results. User wants to import, clean, and filter to recent matches.
2. **Instagram reel** (@rbkespinosa) — a football-match-outcome prediction the user wants to replicate.

## What I Found

### Dataset
- **CC0 (public domain)**, four linked CSVs — not one. `results.csv` (49,398 matches, **1872→2024**), `shootouts.csv`, `goalscorers.csv`, `former_names.csv`.
- Excludes Olympics / B-teams / U-23.
- **Three quirks that shape cleaning**: team names are already *current* (historical Ireland → Northern Ireland); `country` reflects the name *at match time* (Gold Coast ≠ Ghana); the **`neutral` flag is load-bearing** for home advantage. Scores are full-time, pre-shootout.

### The reel
- Predicts **Brazil vs Haiti (World Cup 2026)**. Commenter confirmed the method is **MCMC** for estimating probability distributions. Tagged #machinelearning #cienciadedatos.
- **Crucially, the reel shows the output, not the steps.** Comments are full of requests for a "guía." So this is **reverse-engineering the standard method**, not copying the reel.

## Key Insight

> **MCMC + scoreline prediction = a Bayesian hierarchical Poisson model (the Dixon–Coles lineage).** Each team gets latent attack/defense strengths, goals are Poisson, a global home-advantage term gated by `neutral`, fit via MCMC (PyMC/Stan). The payoff vs a point estimate: the posterior yields a **full scoreline probability grid + P(W/D/L)** — the very distribution the reel sells.

## Decisions Locked This Session

| Question | Decision |
|---|---|
| **Recency filter** | **2018 → now** (~two World Cup cycles; current squads/form) |
| **Ambition** | **Mix**: replicate the reel's core model **+** build the full pipeline with **backtesting** |
| **Intent** | **Dual**: learning/portfolio (Bayesian + MCMC) **and** predictions accurate enough to trust |
| **Method** | Bayesian hierarchical Poisson via MCMC; home advantage gated by `neutral` |
| **Likely stack** | Python + pandas + **PyMC** (ArviZ diagnostics); Stan as alternative |

## Scope Agreed

- **v1** — clean+filter to 2018→now, fit double-Poisson via MCMC, reproduce a reel-style single prediction.
- **v1.5** — wrap into a reusable `predict(team_a, team_b, neutral)` returning the full distribution.
- **v2** — **temporal backtest** (no leakage), metrics **RPS / log-loss / Brier + calibration**, benchmark vs Elo (and bookmaker odds if available). Add Dixon–Coles correction / time-decay only if the backtest justifies it.

## Guiding Principle

**Start simple (vanilla double-Poisson); let the backtest justify every added complication** (Dixon–Coles low-score correction, time-decay weighting, time-varying strengths).

## Process Note

This was **ideation + method scoping only — no code, no model fit, no actual data download**. The riskiest modeling choices (Dixon–Coles vs vanilla, static vs time-varying strengths, friendlies in/out) were captured as **open questions deferred to the build repo**, to be settled empirically by the backtest rather than argued here.

## Still Open

- Hard 2018 cut vs time-decay weighting within the window.
- Friendlies in or out; tournament weighting.
- Model variant (double-Poisson / Dixon–Coles / bivariate) and static vs time-varying strengths.
- Backtest design + benchmark odds source.
- Eventual World Cup 2026 focus and a shareable reel-style artifact.

## Outcome

Two raw links → a scoped, method-grounded idea note ready to seed a separate build repo. The reel's "secret" (MCMC) is demystified as standard Bayesian-Poisson football analytics; the project's two halves (data pipeline + backtested model) and its dual learning/accuracy intent are locked.

## Next Session Hooks

- Pick the stack (PyMC vs Stan) and spin up the build repo.
- First build steps: download CSVs → clean+filter to 2018→now (respect `neutral`, cross-check `former_names.csv`) → fit double-Poisson MCMC → check convergence.

---
*Refines: [[Ideas/Technology/Football Match Outcome Predictor]]*

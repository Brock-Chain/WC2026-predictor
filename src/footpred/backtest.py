"""Temporal backtest + proper scoring metrics.

No leakage: at each fold we train only on matches strictly before the fold's
start, then score predictions on the fold's matches. We use an **expanding
window** (train on everything up to the cutoff, roll the cutoff forward).

Metrics for ordered 1X2 (home/draw/away) outcomes:
- **RPS** (Ranked Probability Score) — the standard for ordered football
  outcomes; penalizes predictions that are "far" in rank order.
- **log-loss** — multiclass cross-entropy.
- **Brier** — multiclass squared error.
Plus a calibration table.

Because the Bayesian model is expensive to fit per fold, the backtest is
parameterized by a ``predict_proba_factory(train_df) -> predict_proba_fn`` so
both Elo (cheap, online) and the PyMC model (refit per fold) share one loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

# Outcome encoding: 0=home win, 1=draw, 2=away win.
ProbaFn = Callable[[str, str, bool], tuple[float, float, float]]
Factory = Callable[[pd.DataFrame], ProbaFn]


def outcome(hg: int, ag: int) -> int:
    return 0 if hg > ag else (1 if hg == ag else 2)


def rps(probs: np.ndarray, actual: int) -> float:
    """Ranked Probability Score for one 3-class ordered prediction."""
    cum_p = np.cumsum(probs)
    cum_a = np.cumsum(np.eye(3)[actual])
    return float(np.sum((cum_p - cum_a) ** 2) / (len(probs) - 1))


def log_loss_one(probs: np.ndarray, actual: int, eps: float = 1e-12) -> float:
    return float(-np.log(max(probs[actual], eps)))


def brier_one(probs: np.ndarray, actual: int) -> float:
    return float(np.sum((probs - np.eye(3)[actual]) ** 2))


@dataclass
class BacktestResult:
    per_match: pd.DataFrame   # date, teams, probs, actual, rps, logloss, brier
    rps: float
    log_loss: float
    brier: float
    n: int

    def summary(self) -> dict:
        return {
            "n_matches": self.n,
            "RPS": round(self.rps, 4),
            "log_loss": round(self.log_loss, 4),
            "Brier": round(self.brier, 4),
        }


def temporal_backtest(
    df: pd.DataFrame,
    factory: Factory,
    fold_starts: list[str],
    min_train: int = 500,
) -> BacktestResult:
    """Expanding-window temporal backtest.

    ``fold_starts`` are the cutoff dates; each fold scores matches in
    [fold_starts[i], fold_starts[i+1]) (the last fold runs to the end), trained
    on everything strictly before fold_starts[i].
    """
    df = df.sort_values("date").reset_index(drop=True)
    bounds = [pd.Timestamp(d) for d in fold_starts] + [
        df["date"].max() + pd.Timedelta(days=1)
    ]
    rows = []
    for i in range(len(fold_starts)):
        lo, hi = bounds[i], bounds[i + 1]
        train = df[df["date"] < lo]
        test = df[(df["date"] >= lo) & (df["date"] < hi)]
        if len(train) < min_train or test.empty:
            continue
        proba_fn = factory(train)
        for r in test.itertuples():
            try:
                p = np.array(proba_fn(r.home_team, r.away_team, bool(r.neutral)))
            except KeyError:
                continue  # unseen team in this fold — skip, don't fabricate
            p = p / p.sum()
            act = outcome(int(r.home_score), int(r.away_score))
            rows.append({
                "date": r.date,
                "home_team": r.home_team,
                "away_team": r.away_team,
                "p_home": p[0], "p_draw": p[1], "p_away": p[2],
                "actual": act,
                "rps": rps(p, act),
                "log_loss": log_loss_one(p, act),
                "brier": brier_one(p, act),
            })
    per_match = pd.DataFrame(rows)
    if per_match.empty:
        raise RuntimeError("Backtest produced no scored matches — check folds.")
    return BacktestResult(
        per_match=per_match,
        rps=per_match["rps"].mean(),
        log_loss=per_match["log_loss"].mean(),
        brier=per_match["brier"].mean(),
        n=len(per_match),
    )


def calibration_table(per_match: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    """Reliability table for the predicted home-win probability."""
    p = per_match["p_home"].to_numpy()
    hit = (per_match["actual"] == 0).to_numpy().astype(float)
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    out = []
    for b in range(bins):
        m = idx == b
        if m.sum() == 0:
            continue
        out.append({
            "bin": f"{edges[b]:.1f}-{edges[b+1]:.1f}",
            "n": int(m.sum()),
            "mean_pred": float(p[m].mean()),
            "empirical": float(hit[m].mean()),
        })
    return pd.DataFrame(out)


# --- factories -------------------------------------------------------------

def elo_factory(**elo_kwargs) -> Factory:
    from .baselines import Elo

    def _make(train: pd.DataFrame) -> ProbaFn:
        model = Elo(**elo_kwargs).fit(train)
        return model.predict_proba

    return _make


def bayes_factory(
    draws: int = 500,
    tune: int = 500,
    chains: int = 2,
    half_life_years: float | None = None,
    importance: bool = False,
) -> Factory:
    """Refit the PyMC model on each fold's training data. Expensive — use few
    folds. Returns a predict_proba over (home, away, neutral).

    ``half_life_years`` / ``importance`` enable likelihood weighting (passed
    through to :func:`footpred.model.fit`). The time-decay clock is referenced
    per fold to the latest training match, so there is no leakage.
    """
    from . import model as M
    from .predict import predict as _predict

    def _make(train: pd.DataFrame) -> ProbaFn:
        idata = M.fit(
            train, draws=draws, tune=tune, chains=chains,
            half_life_years=half_life_years, importance=importance,
        )
        teams = list(idata.attrs["teams"])

        def _proba(home: str, away: str, neutral: bool = False):
            pred = _predict(idata, home, away, neutral, teams=teams)
            return (pred.p_home_win, pred.p_draw, pred.p_away_win)

        return _proba

    return _make

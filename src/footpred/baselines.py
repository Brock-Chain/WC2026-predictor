"""Cheap, honest baselines to benchmark the Bayesian model against.

- :func:`naive_home` — always predict the home team wins (or fixed climo).
- :class:`Elo` — a standard football Elo with home advantage, producing
  P(win/draw/loss). This is the free, no-odds-needed benchmark the spec calls
  for (bookmaker odds aren't in the CC0 dataset).

Both expose the same ``predict_proba(home, away, neutral) -> (pH, pD, pA)``
interface used by the backtest.
"""

from __future__ import annotations

import math
from collections import defaultdict

import pandas as pd


def naive_home(climo: tuple[float, float, float] | None = None):
    """Return a predictor that ignores the teams.

    With ``climo=None`` it predicts a flat home-win certainty-ish prior
    (0.5/0.25/0.25). Pass empirical (pH, pD, pA) climatology for a fairer
    baseline."""
    p = climo if climo is not None else (0.50, 0.25, 0.25)

    def _predict(home: str, away: str, neutral: bool = False):
        return p

    return _predict


class Elo:
    """Standard Elo rating with home advantage and a draw model.

    Win/draw/loss probabilities use the common logistic expected-score with a
    draw band derived from rating closeness. Ratings update online; call
    :meth:`fit` on a chronologically ordered frame, then ``predict_proba``.
    """

    def __init__(
        self,
        k: float = 30.0,
        home_adv: float = 65.0,
        base: float = 1500.0,
        draw_width: float = 0.30,
    ):
        self.k = k
        self.home_adv = home_adv
        self.base = base
        self.draw_width = draw_width
        self.ratings: dict[str, float] = defaultdict(lambda: base)

    def _expected(self, r_home: float, r_away: float, neutral: bool) -> float:
        ha = 0.0 if neutral else self.home_adv
        return 1.0 / (1.0 + 10 ** (-(r_home + ha - r_away) / 400.0))

    def predict_proba(self, home: str, away: str, neutral: bool = False):
        r_h = self.ratings[home]
        r_a = self.ratings[away]
        e_home = self._expected(r_h, r_a, neutral)  # expected score in [0,1]
        # Map expected score -> (pH, pD, pA). Draw prob peaks when even.
        p_draw = self.draw_width * (1.0 - abs(2 * e_home - 1.0))
        p_draw = max(0.05, min(0.40, p_draw))
        p_home = e_home * (1.0 - p_draw)
        p_away = (1.0 - e_home) * (1.0 - p_draw)
        s = p_home + p_draw + p_away
        return p_home / s, p_draw / s, p_away / s

    def update(self, home: str, away: str, hg: int, ag: int, neutral: bool):
        r_h = self.ratings[home]
        r_a = self.ratings[away]
        e_home = self._expected(r_h, r_a, neutral)
        s_home = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
        # Goal-difference multiplier (mild) — standard in football Elo.
        gd = abs(hg - ag)
        mult = math.log1p(gd) + 1.0
        delta = self.k * mult * (s_home - e_home)
        self.ratings[home] = r_h + delta
        self.ratings[away] = r_a - delta

    def fit(self, df: pd.DataFrame) -> "Elo":
        for row in df.sort_values("date").itertuples():
            self.update(
                row.home_team, row.away_team,
                int(row.home_score), int(row.away_score), bool(row.neutral),
            )
        return self

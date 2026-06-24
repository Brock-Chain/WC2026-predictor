"""Turn a fitted posterior into match predictions.

The headline object is a :class:`Prediction`: a full scoreline probability
grid for a fixture, plus the collapsed summaries the reel sells — P(home win /
draw / away win), expected goals, most-likely scorelines, over/under 2.5.

We integrate over the posterior (not a point estimate) so the prediction
reflects genuine parameter uncertainty. For each posterior draw we get a pair
of Poisson rates (lambda_home, lambda_away); we average the per-draw scoreline
PMFs to get the posterior-predictive grid.
"""

from __future__ import annotations

from dataclasses import dataclass

import arviz as az
import numpy as np
from scipy.stats import poisson


@dataclass
class Prediction:
    home_team: str
    away_team: str
    neutral: bool
    grid: np.ndarray              # [max_goals+1, max_goals+1], P(i home, j away)
    max_goals: int

    # --- per-draw posterior 1X2 (None unless predict(..., posterior_spread=True)) ---
    # Each is shape [S]: that draw's P(home win)/P(draw)/P(away win), plus the
    # per-draw expected total goals. The mean over draws equals the point
    # summaries below; the spread is the posterior uncertainty the MCMC buys us.
    draw_p_home: np.ndarray | None = None
    draw_p_draw: np.ndarray | None = None
    draw_p_away: np.ndarray | None = None
    draw_exp_total: np.ndarray | None = None

    # --- collapsed summaries ---
    @property
    def p_home_win(self) -> float:
        return float(np.tril(self.grid, -1).sum())  # home > away

    @property
    def p_draw(self) -> float:
        return float(np.trace(self.grid))

    @property
    def p_away_win(self) -> float:
        return float(np.triu(self.grid, 1).sum())  # away > home

    @property
    def exp_home_goals(self) -> float:
        idx = np.arange(self.max_goals + 1)
        return float((self.grid.sum(axis=1) * idx).sum())

    @property
    def exp_away_goals(self) -> float:
        idx = np.arange(self.max_goals + 1)
        return float((self.grid.sum(axis=0) * idx).sum())

    @property
    def p_over_2_5(self) -> float:
        i = np.arange(self.max_goals + 1)
        total = i[:, None] + i[None, :]
        return float(self.grid[total >= 3].sum())

    def has_spread(self) -> bool:
        return self.draw_p_home is not None

    def ci_1x2(self, outcome: str, lo: float = 5.0, hi: float = 95.0):
        """(lo, hi) credible-interval bounds for one 1X2 outcome's probability
        across the posterior draws. ``outcome`` in {"home","draw","away"}.
        Returns None if per-draw spread wasn't computed."""
        arr = {"home": self.draw_p_home, "draw": self.draw_p_draw,
               "away": self.draw_p_away}.get(outcome)
        if arr is None:
            return None
        return (float(np.percentile(arr, lo)), float(np.percentile(arr, hi)))

    def ci_exp_total(self, lo: float = 5.0, hi: float = 95.0):
        if self.draw_exp_total is None:
            return None
        return (float(np.percentile(self.draw_exp_total, lo)),
                float(np.percentile(self.draw_exp_total, hi)))

    def top_scorelines(self, n: int = 5) -> list[tuple[int, int, float]]:
        flat = [
            (i, j, float(self.grid[i, j]))
            for i in range(self.max_goals + 1)
            for j in range(self.max_goals + 1)
        ]
        flat.sort(key=lambda x: x[2], reverse=True)
        return flat[:n]

    def as_dict(self) -> dict:
        i, j, p = self.top_scorelines(1)[0]
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "neutral": self.neutral,
            "p_home_win": self.p_home_win,
            "p_draw": self.p_draw,
            "p_away_win": self.p_away_win,
            "exp_home_goals": self.exp_home_goals,
            "exp_away_goals": self.exp_away_goals,
            "p_over_2_5": self.p_over_2_5,
            "most_likely_scoreline": (i, j),
            "most_likely_scoreline_prob": p,
        }


def _flatten_posterior(idata: az.InferenceData, var: str) -> np.ndarray:
    """Return posterior samples for ``var`` flattened over (chain, draw),
    shape [n_samples, ...]."""
    arr = idata.posterior[var]
    return arr.stack(sample=("chain", "draw")).transpose("sample", ...).values


def predict(
    idata: az.InferenceData,
    home_team: str,
    away_team: str,
    neutral: bool = False,
    max_goals: int = 10,
    teams: list[str] | None = None,
    posterior_spread: bool = False,
) -> Prediction:
    """Predict a single fixture from the posterior.

    ``teams`` defaults to the team list stashed on the InferenceData by
    :func:`footpred.model.fit`.
    """
    if teams is None:
        teams = list(idata.attrs.get("teams", idata.posterior["team"].values))
    team_to_id = {t: k for k, t in enumerate(teams)}
    for t in (home_team, away_team):
        if t not in team_to_id:
            raise KeyError(
                f"Unknown team {t!r}. Not seen in the training window "
                f"(insufficient recent data)."
            )
    h, a = team_to_id[home_team], team_to_id[away_team]

    intercept = _flatten_posterior(idata, "intercept")          # [S]
    home_adv = _flatten_posterior(idata, "home_adv")            # [S]
    atk = _flatten_posterior(idata, "atk")                      # [S, T]
    deff = _flatten_posterior(idata, "def")                     # [S, T]

    home_active = 0.0 if neutral else 1.0
    log_lh = intercept + home_adv * home_active + atk[:, h] - deff[:, a]
    log_la = intercept + atk[:, a] - deff[:, h]
    lam_h = np.exp(log_lh)   # [S]
    lam_a = np.exp(log_la)   # [S]

    # Per-draw Poisson PMFs over 0..max_goals, then average over draws.
    k = np.arange(max_goals + 1)
    pmf_h = poisson.pmf(k[None, :], lam_h[:, None])   # [S, G+1]
    pmf_a = poisson.pmf(k[None, :], lam_a[:, None])   # [S, G+1]

    # per-draw 1X2 + expected total, populated only when posterior_spread=True
    dph = dpd = dpa = dtot = None

    if "rho" in idata.posterior:
        # Dixon-Coles: per-draw grid with the tau correction on the four
        # low-score cells, renormalized per draw, then averaged.
        rho = _flatten_posterior(idata, "rho")             # [S]
        g = pmf_h[:, :, None] * pmf_a[:, None, :]           # [S, G+1, G+1]
        g[:, 0, 0] *= (1.0 - lam_h * lam_a * rho)
        g[:, 0, 1] *= (1.0 + lam_h * rho)
        g[:, 1, 0] *= (1.0 + lam_a * rho)
        g[:, 1, 1] *= (1.0 - rho)
        g = np.clip(g, 0.0, None)
        g /= g.sum(axis=(1, 2), keepdims=True)              # per-draw normalized
        grid = g.mean(axis=0)
        if posterior_spread:
            ii = np.arange(grid.shape[0])
            tri_lower = (ii[:, None] > ii[None, :]).ravel()   # home > away
            tri_upper = (ii[:, None] < ii[None, :]).ravel()   # away > home
            diag = (ii[:, None] == ii[None, :]).ravel()
            gf = g.reshape(g.shape[0], -1)                    # [S, (G+1)^2]
            dph = gf[:, tri_lower].sum(axis=1)
            dpa = gf[:, tri_upper].sum(axis=1)
            dpd = gf[:, diag].sum(axis=1)
    else:
        # Independent double-Poisson: average the per-draw outer products.
        grid = np.einsum("si,sj->ij", pmf_h, pmf_a) / pmf_h.shape[0]
        if posterior_spread:
            # Per-draw 1X2 WITHOUT materializing [S,G+1,G+1] — vector reductions.
            # Normalize each draw on the truncated 0..G square (matches the mean
            # grid's renormalization below) so the three sum to 1 per draw and
            # mean_s P_x[s] == the collapsed point summary.
            cdf_h = np.cumsum(pmf_h, axis=1)                  # [S, G+1]
            tot_h = cdf_h[:, -1]                              # mass on 0..G
            tot_a = np.cumsum(pmf_a, axis=1)[:, -1]
            Z = tot_h * tot_a                                 # [S] truncated mass
            dpd = (pmf_h * pmf_a).sum(axis=1) / Z
            dph = (pmf_a * (tot_h[:, None] - cdf_h)).sum(axis=1) / Z
            dpa = 1.0 - dph - dpd
    grid = grid / grid.sum()  # renormalize (truncation at max_goals)

    if posterior_spread:
        dtot = lam_h + lam_a   # per-draw expected total goals [S]

    return Prediction(
        home_team=home_team,
        away_team=away_team,
        neutral=neutral,
        grid=grid,
        max_goals=max_goals,
        draw_p_home=dph,
        draw_p_draw=dpd,
        draw_p_away=dpa,
        draw_exp_total=dtot,
    )

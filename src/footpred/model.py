"""The Bayesian hierarchical double-Poisson model (Dixon-Coles lineage),
fit via MCMC in PyMC.

Generative story
----------------
Each team ``t`` has a latent **attack** strength ``atk[t]`` and **defense**
strength ``def[t]``, both hierarchical (Normal, shrunk toward 0 with a shared
learned scale — this regularizes rarely-seen teams toward the mean). A single
global **home advantage** term applies only at non-neutral venues.

For a match (home ``h`` vs away ``a``)::

    log lambda_home = intercept + home_adv * (1 - neutral) + atk[h] - def[a]
    log lambda_away = intercept                            + atk[a] - def[h]
    home_score ~ Poisson(lambda_home)
    away_score ~ Poisson(lambda_away)

We start with vanilla double-Poisson (no Dixon-Coles low-score correction).
The guiding principle: add complexity only when the backtest justifies it.

Identifiability: attack/defense are only defined up to a constant. The
hierarchical zero-centered priors + the global ``intercept`` pin them down
adequately for prediction; we do not impose a hard sum-to-zero constraint.
"""

from __future__ import annotations

from pathlib import Path

import arviz as az
import numpy as np
import pandas as pd
import pymc as pm

from .data import TeamIndex, encode_matches, match_weights


def build_model(
    df: pd.DataFrame,
    index: TeamIndex,
    weights: "np.ndarray | None" = None,
) -> pm.Model:
    """Construct the PyMC model from an encoded match frame.

    ``df`` must contain ``home_id``, ``away_id``, ``home_score``,
    ``away_score``, ``neutral``.

    If ``weights`` is given (per-match, aligned to ``df`` rows), the Poisson
    log-likelihood of each match is scaled by its weight via ``pm.Potential``
    (a weighted likelihood). With ``weights=None`` the model is the plain
    unweighted double-Poisson.
    """
    home_id = df["home_id"].to_numpy()
    away_id = df["away_id"].to_numpy()
    home_goals = df["home_score"].to_numpy()
    away_goals = df["away_score"].to_numpy()
    # not-neutral -> 1.0 enables home advantage; neutral -> 0.0 disables it.
    home_active = (~df["neutral"].to_numpy()).astype(float)

    coords = {
        "team": index.teams,
        "match": np.arange(len(df)),
    }

    with pm.Model(coords=coords) as model:
        home_id_ = pm.Data("home_id", home_id, dims="match")
        away_id_ = pm.Data("away_id", away_id, dims="match")
        home_active_ = pm.Data("home_active", home_active, dims="match")

        # Global terms.
        intercept = pm.Normal("intercept", mu=0.0, sigma=1.0)
        home_adv = pm.Normal("home_adv", mu=0.0, sigma=1.0)

        # Hierarchical scales for team strengths.
        sd_att = pm.HalfNormal("sd_att", sigma=1.0)
        sd_def = pm.HalfNormal("sd_def", sigma=1.0)

        # Per-team latent strengths (zero-centered, shrunk by the scales).
        atk = pm.Normal("atk", mu=0.0, sigma=sd_att, dims="team")
        deff = pm.Normal("def", mu=0.0, sigma=sd_def, dims="team")

        log_lambda_home = (
            intercept
            + home_adv * home_active_
            + atk[home_id_]
            - deff[away_id_]
        )
        log_lambda_away = (
            intercept
            + atk[away_id_]
            - deff[home_id_]
        )

        if weights is None:
            pm.Poisson(
                "home_goals",
                mu=pm.math.exp(log_lambda_home),
                observed=home_goals,
                dims="match",
            )
            pm.Poisson(
                "away_goals",
                mu=pm.math.exp(log_lambda_away),
                observed=away_goals,
                dims="match",
            )
        else:
            # Weighted likelihood: scale each match's Poisson logp by its weight.
            w_ = pm.Data("weights", np.asarray(weights, dtype=float), dims="match")
            home_dist = pm.Poisson.dist(mu=pm.math.exp(log_lambda_home))
            away_dist = pm.Poisson.dist(mu=pm.math.exp(log_lambda_away))
            pm.Potential("home_goals_w", (w_ * pm.logp(home_dist, home_goals)).sum())
            pm.Potential("away_goals_w", (w_ * pm.logp(away_dist, away_goals)).sum())

    return model


def fit(
    df: pd.DataFrame,
    index: TeamIndex | None = None,
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.9,
    random_seed: int = 42,
    nuts_sampler: str = "nutpie",
    half_life_years: float | None = None,
    importance: bool = False,
) -> az.InferenceData:
    """Encode, build, and sample the model. Returns an ArviZ InferenceData
    with the posterior.

    ``nuts_sampler="nutpie"`` JIT-compiles the model via numba (LLVM) — fast
    and needs no C/C++ compiler. Falls back to PyMC's default sampler if
    nutpie is unavailable.

    ``half_life_years`` / ``importance`` switch on per-match likelihood
    weighting (time-decay and/or tournament-importance). Both off (the default)
    reproduces the plain unweighted double-Poisson. The time-decay clock is
    referenced to the latest match in ``df`` (leakage-free at train time).
    """
    df_enc, index = encode_matches(df, index)
    weights = None
    if half_life_years is not None or importance:
        weights = match_weights(
            df_enc, half_life_years=half_life_years, importance=importance
        )
    model = build_model(df_enc, index, weights=weights)
    sample_kwargs = dict(
        draws=draws,
        tune=tune,
        chains=chains,
        target_accept=target_accept,
        random_seed=random_seed,
        progressbar=True,
    )
    with model:
        try:
            idata = pm.sample(nuts_sampler=nuts_sampler, **sample_kwargs)
        except Exception as exc:  # pragma: no cover - environment dependent
            print(f"[warn] {nuts_sampler} sampler failed ({exc}); "
                  f"falling back to default PyMC sampler.")
            idata = pm.sample(**sample_kwargs)
    # Stash the team list so downstream code is self-contained.
    idata.attrs["teams"] = list(index.teams)
    return idata


def convergence_summary(idata: az.InferenceData) -> pd.DataFrame:
    """Return an ArviZ summary (r_hat, ess) for the global + scale params.
    Per-team params are many; we summarize the headline scalars."""
    return az.summary(
        idata,
        var_names=["intercept", "home_adv", "sd_att", "sd_def"],
        round_to=4,
    )


def n_divergences(idata: az.InferenceData) -> int:
    if "sample_stats" in idata and "diverging" in idata.sample_stats:
        return int(idata.sample_stats["diverging"].sum())
    return 0


# --- persistence -----------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"


def save_trace(idata: az.InferenceData, name: str = "trace.nc") -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / name
    idata.to_netcdf(path)
    return path


def load_trace(name: str = "trace.nc") -> az.InferenceData:
    path = MODELS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found — fit the model first.")
    return az.from_netcdf(path)

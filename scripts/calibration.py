"""Compute the model's reliability (calibration) curve ONCE and cache it.

The temporal backtest is slow (it refits PyMC per fold) and only persists scalar
scores — not the per-match probabilities a reliability plot needs. So we take
the cheap honest path used for every other baked artifact: load the SHIPPED
full-data trace (``models/trace.nc``) and run the closed-form ``predict`` over
the training matches (no MCMC — seconds), then bin predicted probability against
the realized outcome and write ``reports/calibration.json``. ``report.py`` bakes
that file the same way it bakes ``reports/model_variants.json``.

We pool ALL THREE outcome probabilities (home / draw / away) against their 0/1
indicators, so each bin answers "when the model says p, how often does it
happen?" across the full probability range. This is an IN-SAMPLE check (fit on
all matches, evaluated on those same matches) — the Method card says so. The
backtest RPS stays the headline out-of-sample skill number; this is the
complementary "are the probabilities trustworthy" diagnostic.

Run:  python scripts/calibration.py   ->  writes reports/calibration.json
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np  # noqa: E402

from footpred import data, model  # noqa: E402
from footpred.backtest import outcome  # noqa: E402
from footpred.predict import predict  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BINS = 10


def reliability(df, idata, teams) -> dict:
    edges = np.linspace(0.0, 1.0, BINS + 1)
    preds: list[float] = []
    hits: list[float] = []
    skipped = 0
    for r in df.itertuples():
        try:
            p = predict(idata, r.home_team, r.away_team,
                        bool(r.neutral), teams=teams)
        except KeyError:
            skipped += 1   # unseen team — don't fabricate
            continue
        act = outcome(int(r.home_score), int(r.away_score))  # 0=H,1=D,2=A
        for cls, pr in enumerate((p.p_home_win, p.p_draw, p.p_away_win)):
            preds.append(float(pr))
            hits.append(1.0 if act == cls else 0.0)

    preds_a = np.asarray(preds)
    hits_a = np.asarray(hits)
    idx = np.clip(np.digitize(preds_a, edges) - 1, 0, BINS - 1)

    bins = []
    for b in range(BINS):
        m = idx == b
        if not m.any():
            continue
        bins.append({
            "lo": round(float(edges[b]), 3),
            "hi": round(float(edges[b + 1]), 3),
            "n": int(m.sum()),
            "mean_pred": round(float(preds_a[m].mean()), 4),
            "empirical": round(float(hits_a[m].mean()), 4),
        })

    # Expected Calibration Error: n-weighted mean |empirical - mean_pred|.
    total = sum(d["n"] for d in bins) or 1
    ece = sum(d["n"] * abs(d["empirical"] - d["mean_pred"]) for d in bins) / total

    return {
        "bins": bins,
        "n_predictions": int(hits_a.size),     # 3 per match
        "n_matches": int(df.shape[0] - skipped),
        "ece": round(float(ece), 4),
        "source": "in-sample",   # full-data trace evaluated on training matches
        "classes": "home/draw/away pooled",
    }


def main() -> None:
    df = data.load_processed()
    idata = model.load_trace()                     # models/trace.nc (shipped)
    teams = list(idata.attrs["teams"])
    out = reliability(df, idata, teams)
    path = ROOT / "reports" / "calibration.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"[calibration] {out['n_matches']} matches, "
          f"{out['n_predictions']} predictions, ECE={out['ece']:.4f} "
          f"-> {path}")


if __name__ == "__main__":
    main()

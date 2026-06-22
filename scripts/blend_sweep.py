"""Does blending Bayes + Elo beat Bayes alone? (non-invasive experiment)

Linear opinion pool: p_blend = w * p_bayes + (1 - w) * p_elo, with w swept on
the same temporal folds as the model comparison. This does NOT change the
production model — it fits Bayes and Elo once per fold, caches each model's
1X2 probabilities on the test matches, then scores every w cheaply over the
cache (so the Bayes MCMC is paid once per fold, not once per weight).

w = 1.0 is pure Bayes (our current model); w = 0.0 is pure Elo.

Writes reports/blend_sweep.txt.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from footpred import backtest as B          # noqa: E402
from footpred import data                   # noqa: E402
from footpred import model as M             # noqa: E402
from footpred.baselines import Elo          # noqa: E402
from footpred.predict import predict as _predict  # noqa: E402

FOLDS = ["2023-01-01", "2024-01-01"]
DRAWS, TUNE, CHAINS = 500, 500, 2
OUT = ROOT / "reports" / "blend_sweep.txt"


def collect_probs() -> list[tuple[np.ndarray, np.ndarray, int]]:
    df = data.load_processed().sort_values("date").reset_index(drop=True)
    bounds = [pd.Timestamp(d) for d in FOLDS] + [
        df["date"].max() + pd.Timedelta(days=1)
    ]
    records = []
    for i in range(len(FOLDS)):
        lo, hi = bounds[i], bounds[i + 1]
        train = df[df["date"] < lo]
        test = df[(df["date"] >= lo) & (df["date"] < hi)]
        if len(train) < 500 or test.empty:
            continue
        t0 = time.time()
        idata = M.fit(train, draws=DRAWS, tune=TUNE, chains=CHAINS)
        teams = list(idata.attrs["teams"])
        known = set(teams)
        elo = Elo().fit(train)
        for r in test.itertuples():
            if r.home_team not in known or r.away_team not in known:
                continue
            pred = _predict(idata, r.home_team, r.away_team,
                            bool(r.neutral), teams=teams)
            pb = np.array([pred.p_home_win, pred.p_draw, pred.p_away_win])
            pe = np.array(elo.predict_proba(r.home_team, r.away_team,
                                            bool(r.neutral)))
            act = B.outcome(int(r.home_score), int(r.away_score))
            records.append((pb, pe, act))
        print(f"[fold {lo.date()}] {len(test)} test rows, "
              f"fit {time.time()-t0:.0f}s", flush=True)
    return records


def score(records, w: float) -> tuple[float, float, float]:
    rps = ll = br = 0.0
    for pb, pe, act in records:
        p = w * pb + (1 - w) * pe
        p = p / p.sum()
        rps += B.rps(p, act)
        ll += B.log_loss_one(p, act)
        br += B.brier_one(p, act)
    n = len(records)
    return rps / n, ll / n, br / n


def main() -> int:
    rec = collect_probs()
    print(f"[collected] {len(rec)} scored matches\n", flush=True)

    grid = np.round(np.linspace(0.0, 1.0, 21), 2)
    rows = [(w, *score(rec, w)) for w in grid]
    best = min(rows, key=lambda r: r[1])
    pure_bayes = next(r for r in rows if r[0] == 1.0)

    lines = [
        "Bayes + Elo blend sweep  (p = w*Bayes + (1-w)*Elo)",
        f"folds={FOLDS}  n={len(rec)}  draws={DRAWS} tune={TUNE} chains={CHAINS}",
        "",
        f"{'w':>5} {'RPS':>8} {'logloss':>9} {'Brier':>8} {'vs pure Bayes':>15}",
        "-" * 50,
    ]
    for w, r, l, b in rows:
        d = ""
        if w != 1.0:
            d = f"{(r - pure_bayes[1]) / pure_bayes[1] * 100:+.2f}%"
        star = "  <- best" if (w, r, l, b) == best else ""
        lines.append(f"{w:>5.2f} {r:>8.4f} {l:>9.4f} {b:>8.4f} {d:>15}{star}")
    lines += [
        "",
        f"pure Bayes (w=1.0): RPS {pure_bayes[1]:.4f}",
        f"pure Elo   (w=0.0): RPS {rows[0][1]:.4f}",
        f"best blend (w={best[0]:.2f}): RPS {best[1]:.4f}  "
        f"({(best[1]-pure_bayes[1])/pure_bayes[1]*100:+.2f}% vs pure Bayes)",
    ]
    OUT.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\n[done] -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

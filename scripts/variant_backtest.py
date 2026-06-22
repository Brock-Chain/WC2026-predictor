"""Head-to-head temporal backtest of the model variants.

Compares the plain double-Poisson against the Dixon-Coles low-score correction,
the confederation hierarchy, and both together — on identical expanding-window
folds. Reports RPS / log-loss / Brier, plus a DRAW diagnostic (predicted vs
actual draw rate): the ML-classifier literature consistently underpredicts
draws, so we check whether our generative model — and DC specifically — gets
the draw region right.

Run:  python scripts/variant_backtest.py
Writes reports/model_variants.txt and .json.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np  # noqa: E402

from footpred import backtest, data  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FOLDS = ["2024-01-01", "2025-01-01", "2026-01-01"]
DRAWS, TUNE, CHAINS = 500, 500, 2

VARIANTS = {
    "baseline": dict(),
    "dixon_coles": dict(dixon_coles=True),
    "confederation": dict(confederation_layer=True),
    "dc+confed": dict(dixon_coles=True, confederation_layer=True),
}


def run():
    df = data.load_processed()
    rows = {}
    for name, kw in VARIANTS.items():
        print(f"[run] {name} ...", flush=True)
        res = backtest.temporal_backtest(
            df,
            backtest.bayes_factory(draws=DRAWS, tune=TUNE, chains=CHAINS, **kw),
            FOLDS,
        )
        pm = res.per_match
        pred_cols = pm[["p_home", "p_draw", "p_away"]].to_numpy()
        acc = float((pred_cols.argmax(1) == pm["actual"].to_numpy()).mean())
        rows[name] = {
            **res.summary(),
            "accuracy": round(acc, 4),
            "draw_pred_rate": round(float(pm["p_draw"].mean()), 4),
            "draw_actual_rate": round(float((pm["actual"] == 1).mean()), 4),
        }
        print(f"[done] {name}: {rows[name]}", flush=True)

    # Also include the Elo baseline for context.
    elo = backtest.temporal_backtest(df, backtest.elo_factory(), FOLDS)
    epm = elo.per_match
    rows["elo"] = {
        **elo.summary(),
        "accuracy": round(float((
            epm[["p_home", "p_draw", "p_away"]].to_numpy().argmax(1)
            == epm["actual"].to_numpy()).mean()), 4),
        "draw_pred_rate": round(float(epm["p_draw"].mean()), 4),
        "draw_actual_rate": round(float((epm["actual"] == 1).mean()), 4),
    }

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "model_variants.json").write_text(json.dumps(rows, indent=2))

    # Pretty table.
    hdr = f"{'variant':14s} {'RPS':>7s} {'logloss':>8s} {'Brier':>7s} {'acc':>6s} {'drawP':>6s} {'drawA':>6s}"
    lines = [hdr, "-" * len(hdr)]
    for name, r in rows.items():
        lines.append(
            f"{name:14s} {r['RPS']:7.4f} {r['log_loss']:8.4f} {r['Brier']:7.4f} "
            f"{r['accuracy']*100:5.1f}% {r['draw_pred_rate']*100:5.1f}% {r['draw_actual_rate']*100:5.1f}%"
        )
    table = "\n".join(lines)
    (reports / "model_variants.txt").write_text(table + "\n")
    print("\n" + table)


if __name__ == "__main__":
    run()

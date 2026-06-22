"""Finalize the model work in one sequential pass (heavy; run in background):

1. Re-backtest the two Dixon-Coles variants with the FIXED rho bound and merge
   the corrected numbers into reports/model_variants.json (baseline /
   confederation / elo are unaffected by the DC fix, so they're kept as-is).
2. Refit the SHIPPED full-data trace with the confederation layer on (the
   marginal-but-consistent backtest winner) and save it to models/trace.nc.

Run:  python scripts/finalize_model.py
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np  # noqa: E402

from footpred import backtest, data, model  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FOLDS = ["2024-01-01", "2025-01-01", "2026-01-01"]
DRAWS, TUNE, CHAINS = 500, 500, 2


def _row(res):
    pm = res.per_match
    acc = float((pm[["p_home", "p_draw", "p_away"]].to_numpy().argmax(1)
                 == pm["actual"].to_numpy()).mean())
    return {
        **res.summary(),
        "accuracy": round(acc, 4),
        "draw_pred_rate": round(float(pm["p_draw"].mean()), 4),
        "draw_actual_rate": round(float((pm["actual"] == 1).mean()), 4),
    }


def rebacktest_dc():
    df = data.load_processed()
    jpath = ROOT / "reports" / "model_variants.json"
    rows = json.loads(jpath.read_text()) if jpath.exists() else {}
    for name, kw in [("dixon_coles", dict(dixon_coles=True)),
                     ("dc+confed", dict(dixon_coles=True, confederation_layer=True))]:
        print(f"[backtest] {name} (fixed DC) ...", flush=True)
        res = backtest.temporal_backtest(
            df, backtest.bayes_factory(draws=DRAWS, tune=TUNE, chains=CHAINS, **kw), FOLDS)
        rows[name] = _row(res)
        print(f"[backtest] {name}: {rows[name]}", flush=True)
    jpath.write_text(json.dumps(rows, indent=2))

    order = ["baseline", "confederation", "dixon_coles", "dc+confed", "elo"]
    hdr = f"{'variant':14s} {'RPS':>7s} {'logloss':>8s} {'Brier':>7s} {'acc':>6s} {'drawP':>6s}"
    lines = [hdr, "-" * len(hdr)]
    for k in order:
        if k in rows:
            r = rows[k]
            lines.append(f"{k:14s} {r['RPS']:7.4f} {r['log_loss']:8.4f} "
                         f"{r['Brier']:7.4f} {r['accuracy']*100:5.1f}% {r['draw_pred_rate']*100:5.1f}%")
    (ROOT / "reports" / "model_variants.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def refit_shipped():
    print("\n[fit] refitting shipped trace with confederation layer ...", flush=True)
    df = data.load_processed()
    idata = model.fit(df, draws=1000, tune=1000, chains=4, confederation_layer=True)
    print(model.convergence_summary(idata))
    print("divergences:", model.n_divergences(idata))
    path = model.save_trace(idata)
    print(f"[fit] shipped trace saved -> {path}")


if __name__ == "__main__":
    rebacktest_dc()
    refit_shipped()
    print("\n[finalize] done.")

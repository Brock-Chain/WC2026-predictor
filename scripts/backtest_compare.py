"""Compare model variants on the temporal backtest (RPS / log-loss / Brier).

Reproduces the notebook's expanding-window folds and pits the plain
double-Poisson against likelihood-weighting variants (time-decay,
tournament-importance, and their combination). Elo is the cheap reference.

Writes results incrementally to ``reports/backtest_results.json`` and a
human-readable ``reports/backtest_results.txt`` so progress is visible while
the (slow, per-fold-refit) Bayesian variants run.

Run:  .venv\\Scripts\\python.exe scripts\\backtest_compare.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from footpred import backtest, data  # noqa: E402

FOLDS = ["2023-01-01", "2024-01-01"]          # same as notebooks/03_backtest
DRAWS, TUNE, CHAINS = 500, 500, 2             # same as the recorded baseline

OUT_DIR = ROOT / "reports"
OUT_DIR.mkdir(exist_ok=True)
JSON_PATH = OUT_DIR / "backtest_results.json"
TXT_PATH = OUT_DIR / "backtest_results.txt"


def bayes(**kw):
    return backtest.bayes_factory(draws=DRAWS, tune=TUNE, chains=CHAINS, **kw)


# (label, factory) — order matters; cheapest first so partial output is useful.
VARIANTS = [
    ("Elo (reference)", backtest.elo_factory()),
    ("Bayes baseline (unweighted)", bayes()),
    ("Bayes + time-decay hl=2y", bayes(half_life_years=2.0)),
    ("Bayes + time-decay hl=4y", bayes(half_life_years=4.0)),
    ("Bayes + importance", bayes(importance=True)),
    ("Bayes + importance + td hl=2y", bayes(importance=True, half_life_years=2.0)),
]


def main() -> int:
    df = data.load_processed()
    print(f"[data] {len(df):,} matches, "
          f"{df['date'].min().date()} -> {df['date'].max().date()}")
    print(f"[folds] {FOLDS} (score 2023-01-01 -> end)\n")

    results = []
    for label, factory in VARIANTS:
        t0 = time.time()
        print(f"[run] {label} ...", flush=True)
        res = backtest.temporal_backtest(df, factory, FOLDS)
        dt = time.time() - t0
        row = {"variant": label, **res.summary(), "secs": round(dt, 1)}
        results.append(row)
        print(f"      RPS={row['RPS']}  logloss={row['log_loss']}  "
              f"Brier={row['Brier']}  n={row['n_matches']}  ({dt:.0f}s)\n",
              flush=True)

        # Incremental write so partial progress is readable.
        JSON_PATH.write_text(json.dumps(results, indent=2))
        _write_txt(results)

    print(f"[done] -> {JSON_PATH}")
    return 0


def _write_txt(results: list[dict]) -> None:
    base = next((r["RPS"] for r in results
                 if r["variant"].startswith("Bayes baseline")), None)
    lines = [
        "Temporal backtest — model-variant comparison",
        f"folds={FOLDS}  draws={DRAWS} tune={TUNE} chains={CHAINS}",
        "",
        f"{'variant':<34} {'RPS':>7} {'logloss':>8} {'Brier':>7} "
        f"{'dRPS%':>7} {'n':>5} {'secs':>6}",
        "-" * 80,
    ]
    for r in results:
        d = ""
        if base and r["variant"].startswith("Bayes") and r["RPS"] != base:
            d = f"{(r['RPS'] - base) / base * 100:+.1f}"
        lines.append(
            f"{r['variant']:<34} {r['RPS']:>7} {r['log_loss']:>8} "
            f"{r['Brier']:>7} {d:>7} {r['n_matches']:>5} {r['secs']:>6}"
        )
    lines.append("")
    lines.append("dRPS% = change vs Bayes baseline (negative = better).")
    TXT_PATH.write_text("\n".join(lines))


if __name__ == "__main__":
    raise SystemExit(main())

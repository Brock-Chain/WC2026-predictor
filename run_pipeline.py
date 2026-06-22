"""End-to-end pipeline runner.

Usage:
    python run_pipeline.py data        # download + clean + save processed data
    python run_pipeline.py fit         # fit the MCMC model, save trace
    python run_pipeline.py predict "Brazil" "Haiti"   # single-fixture demo
    python run_pipeline.py report      # render WC2026 HTML deliverable
    python run_pipeline.py all         # data -> fit -> report

Backtesting is driven from notebooks/03_backtest.ipynb (it refits per fold and
is slow); see footpred.backtest for the API.
"""

from __future__ import annotations

import sys

from footpred import data, model, predict, report
from footpred.fixtures import check_team_names, load_fixtures


def cmd_data():
    df = data.build_dataset()
    idx = data.TeamIndex.from_matches(df)
    print(f"[ok] {len(df):,} matches, {idx.n_teams} teams, "
          f"{df['date'].min().date()} -> {df['date'].max().date()}")


def cmd_fit():
    df = data.load_processed()
    idata = model.fit(df)
    print(model.convergence_summary(idata))
    print(f"divergences: {model.n_divergences(idata)}")
    path = model.save_trace(idata)
    print(f"[ok] trace saved -> {path}")


def cmd_predict(home: str, away: str):
    idata = model.load_trace()
    pred = predict.predict(idata, home, away, neutral=True)
    d = pred.as_dict()
    print(f"{home} vs {away} (neutral):")
    print(f"  P(home/draw/away) = {d['p_home_win']:.1%} / "
          f"{d['p_draw']:.1%} / {d['p_away_win']:.1%}")
    print(f"  xG = {d['exp_home_goals']:.2f} – {d['exp_away_goals']:.2f}")
    print(f"  most likely: {d['most_likely_scoreline']} "
          f"({d['most_likely_scoreline_prob']:.1%})")
    print("  top scorelines:", pred.top_scorelines(5))


def cmd_report():
    idata = model.load_trace()
    teams = list(idata.attrs["teams"])
    fx = load_fixtures()
    missing = check_team_names(fx, teams)
    if missing:
        print(f"[warn] {len(missing)} fixture teams unseen in training window: "
              f"{sorted(missing)}")
    from datetime import date
    out = report.render_report(idata, fx, teams,
                               generated_on=date.today().strftime("%b %d, %Y"))
    print(f"[ok] report -> {out}")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "data":
        cmd_data()
    elif cmd == "fit":
        cmd_fit()
    elif cmd == "predict":
        cmd_predict(argv[1], argv[2])
    elif cmd == "report":
        cmd_report()
    elif cmd == "all":
        cmd_data(); cmd_fit(); cmd_report()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

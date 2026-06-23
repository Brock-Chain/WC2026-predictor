"""End-to-end pipeline runner.

Usage:
    python run_pipeline.py data        # download + clean + save processed data
    python run_pipeline.py fit         # fit the MCMC model, save trace
    python run_pipeline.py predict "Brazil" "Haiti"   # single-fixture demo
    python run_pipeline.py report      # render WC2026 HTML deliverable
    python run_pipeline.py odds        # resolve + print live Polymarket markets
    python run_pipeline.py all         # data -> fit -> report (no odds; core build)
    python run_pipeline.py update      # re-download live data -> refit -> report
                                       # (keeps the page fresh during the tournament)
    python run_pipeline.py render      # re-download data -> report (NO refit);
                                       # the cheap verb for a frequent hosting cron

Backtesting is driven from notebooks/03_backtest.ipynb (it refits per fold and
is slow); see footpred.backtest for the API.
"""

from __future__ import annotations

import sys

import pandas as pd

from footpred import data, model, predict, report
from footpred.fixtures import check_team_names, load_fixtures, sync_played_results


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


def _upcoming_fixtures(fx) -> list[tuple]:
    """(home, away, YYYY-MM-DD) for every unplayed fixture."""
    up = fx[~fx["played"]]
    return [(r.home_team, r.away_team,
             r.date.strftime("%Y-%m-%d") if pd.notna(r.date) else "")
            for r in up.itertuples()]


def _resolve_odds(fx, teams, verbose: bool = True):
    """Best-effort Polymarket resolution for the Model-vs-Market tab.

    Lives entirely outside the model pipeline and never raises: any network or
    parse failure just returns ``None`` and the tab degrades gracefully.
    """
    try:
        from footpred import polymarket
        matches, title = polymarket.resolve_odds(_upcoming_fixtures(fx), teams)
        if verbose:
            print(f"[odds] resolved {len(matches)} live match market(s)"
                  f" + {len(title.get('teams', {}))} title team(s)")
        if not matches and not title.get("teams"):
            return None
        return (matches, title)
    except Exception as e:  # noqa: BLE001 — must never break the build
        if verbose:
            print(f"[odds] skipped (Polymarket unavailable: {e})")
        return None


def _load_fixtures_synced(teams):
    """Load fixtures and fill played scores from the authoritative live dataset
    (corrects any hand-entered scores in the schedule file)."""
    fx = load_fixtures()
    try:
        matches = data.load_processed()
        fx, n_filled, corrections = sync_played_results(fx, matches)
        if n_filled:
            print(f"[sync] filled {n_filled} played result(s) from live data")
        for teams_s, old, new in corrections:
            print(f"[sync] corrected {teams_s}: {old} -> {new}")
    except FileNotFoundError:
        print("[warn] no processed data; using scores as stored in fixtures CSV")
    missing = check_team_names(fx, teams)
    if missing:
        print(f"[warn] {len(missing)} fixture teams unseen in training window: "
              f"{sorted(missing)}")
    return fx


def cmd_report(with_odds: bool = True):
    idata = model.load_trace()
    teams = list(idata.attrs["teams"])
    fx = _load_fixtures_synced(teams)
    odds_meta = _resolve_odds(fx, teams) if with_odds else None
    from datetime import date
    out = report.render_report(idata, fx, teams,
                               generated_on=date.today().strftime("%b %d, %Y"),
                               odds_meta=odds_meta)
    print(f"[ok] report -> {out}")


def cmd_odds():
    """Resolve + print the live Polymarket markets the report would compare
    against (a standalone check; the report does this automatically)."""
    idata = model.load_trace()
    teams = list(idata.attrs["teams"])
    fx = _load_fixtures_synced(teams)
    meta = _resolve_odds(fx, teams)
    if not meta:
        print("[odds] nothing resolved.")
        return
    matches, title = meta
    for (h, a, d), m in matches.items():
        s = m["snapshot"]
        print(f"  {d}  {h} v {a:<22} H/D/A={s['h']}/{s['d']}/{s['a']}"
              f"  vol=${m['volume']/1e6:.1f}M  more={'Y' if m['more_slug'] else '-'}")
    print(f"[odds] {len(matches)} matches, "
          f"{len(title.get('teams', {}))} title teams, "
          f"overround={title.get('sum', 0):.3f}")


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
    elif cmd == "odds":
        cmd_odds()
    elif cmd == "all":
        # Core model build only — never blocked by Polymarket availability.
        cmd_data(); cmd_fit(); cmd_report(with_odds=False)
    elif cmd == "update":
        # Refresh the live data, refit on the new results, regenerate the page
        # (best-effort live odds folded into the report step).
        data.build_dataset(force_download=True)
        cmd_fit(); cmd_report()
    elif cmd == "render":
        # Re-render only: fresh data sync + live odds, NO refit. Cheap enough to
        # run on a frequent hosting cron (uses the committed/cached trace).
        data.build_dataset(force_download=True)
        cmd_report()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

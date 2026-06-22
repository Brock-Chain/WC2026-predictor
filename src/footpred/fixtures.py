"""World Cup 2026 fixtures.

The historical dataset stops in 2024, so WC2026 fixtures live in their own file
(``data/raw/wc2026_fixtures.csv``). Schema (one row per match):

    stage,group,date,home_team,away_team,home_score,away_score

- ``stage``: "Group" | "Round of 32" | "Round of 16" | ... | "Final"
- ``group``: group letter for the group stage, else blank
- ``home_score`` / ``away_score``: integers for already-played matches,
  blank for upcoming fixtures (these get predictions only).

Team names MUST match the dataset's normalized names (see data.normalize_teams).
:func:`check_team_names` flags any fixture team the model has never seen.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_PATH = PROJECT_ROOT / "data" / "wc2026_fixtures.csv"


def load_fixtures(path: Path | None = None) -> pd.DataFrame:
    path = path or FIXTURES_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Populate it with the WC2026 schedule "
            f"(see fixtures.py docstring for the schema)."
        )
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ("home_score", "away_score"):
        df[col] = pd.to_numeric(df.get(col), errors="coerce")
    df["played"] = df["home_score"].notna() & df["away_score"].notna()
    df["group"] = df.get("group", "").fillna("")
    return df.sort_values("date").reset_index(drop=True)


def check_team_names(fixtures: pd.DataFrame, known_teams: list[str]) -> set[str]:
    """Return fixture team names absent from the training window — these can't
    be predicted (no recent data) and the caller must decide how to handle."""
    known = set(known_teams)
    used = set(fixtures["home_team"]) | set(fixtures["away_team"])
    return {t for t in used if t not in known}


# Tournament window for auto-syncing played results from the live dataset.
WC_START = "2026-06-01"
WC_TOURNAMENT = "World Cup"


def sync_played_results(
    fixtures: pd.DataFrame,
    matches: pd.DataFrame,
    window_start: str = WC_START,
    tournament_contains: str = WC_TOURNAMENT,
):
    """Fill/correct each fixture's score from the **authoritative live dataset**.

    The martj42 feed tags WC2026 games as "FIFA World Cup", so once a match is
    played its real score appears in ``matches``. We match each scheduled fixture
    to its result by *unordered team pair* within the tournament window, keep the
    fixture's own home/away orientation (swapping the score if the dataset stored
    the pair the other way round), and recompute ``played``.

    This removes hand-maintained scores as a source of error: the schedule file
    only needs the right pairings/dates; results come from the data.

    Returns ``(synced_fixtures, n_filled, corrections)`` where ``corrections`` is
    a list of (teams, old, new) for fixtures whose stored score disagreed.
    """
    m = matches[
        (matches["date"] >= pd.Timestamp(window_start))
        & matches["tournament"].str.contains(tournament_contains, case=False, na=False)
    ]
    lookup: dict[frozenset, tuple] = {}
    for r in m.itertuples():
        lookup[frozenset((r.home_team, r.away_team))] = (
            r.home_team, r.away_team, int(r.home_score), int(r.away_score)
        )

    fx = fixtures.copy()
    new_hs, new_as = [], []
    n_filled = 0
    corrections = []
    for r in fx.itertuples():
        key = frozenset((r.home_team, r.away_team))
        if key in lookup and r.home_team != r.away_team:
            dh, _da, dhs, das = lookup[key]
            hs, as_ = (dhs, das) if r.home_team == dh else (das, dhs)
            old = (r.home_score, r.away_score)
            if pd.isna(old[0]) or pd.isna(old[1]):
                n_filled += 1
            elif (int(old[0]), int(old[1])) != (hs, as_):
                corrections.append(
                    (f"{r.home_team} v {r.away_team}",
                     f"{int(old[0])}-{int(old[1])}", f"{hs}-{as_}")
                )
            new_hs.append(hs)
            new_as.append(as_)
        else:
            new_hs.append(r.home_score)
            new_as.append(r.away_score)

    fx["home_score"] = pd.to_numeric(pd.Series(new_hs, index=fx.index), errors="coerce")
    fx["away_score"] = pd.to_numeric(pd.Series(new_as, index=fx.index), errors="coerce")
    fx["played"] = fx["home_score"].notna() & fx["away_score"].notna()
    return fx, n_filled, corrections

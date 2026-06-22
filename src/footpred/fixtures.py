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

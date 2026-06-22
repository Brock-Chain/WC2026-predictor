"""Data pipeline: download, clean, filter, and normalize the
``martj42/international_results`` dataset (CC0).

Design notes (the three quirks that drive cleaning — see project spec):

1. Team names in the dataset are already *current* (e.g. historical "Ireland"
   rows are labelled "Northern Ireland"). We still cross-check against
   ``former_names.csv`` to be safe, but minimal remapping is expected.
2. ``country`` reflects the venue's name *at match time* (1950s Ghana =
   "Gold Coast"). It is NOT a stable key — we never use it for joins/indexing.
3. The ``neutral`` flag is load-bearing: it gates home advantage. We keep it
   intact and never drop it.

Scores are full-time, pre-shootout. For goals-based Poisson modelling we use
``results.csv`` scores as-is and ignore ``shootouts.csv`` (knockout-only).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

# --- locations -------------------------------------------------------------

RAW_BASE_URL = (
    "https://raw.githubusercontent.com/martj42/international_results/master/"
)
CSV_FILES = {
    "results": "results.csv",
    "shootouts": "shootouts.csv",
    "goalscorers": "goalscorers.csv",
    "former_names": "former_names.csv",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Default recency filter (locked decision: ~two World Cup cycles).
DEFAULT_START = "2018-01-01"


# --- download --------------------------------------------------------------

def download_raw(force: bool = False) -> dict[str, Path]:
    """Download the four CSVs into ``data/raw/``. Skips files already present
    unless ``force=True``. Returns a mapping name -> local path."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, fname in CSV_FILES.items():
        dest = RAW_DIR / fname
        if dest.exists() and not force:
            paths[name] = dest
            continue
        url = RAW_BASE_URL + fname
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        paths[name] = dest
    return paths


def _read_raw(name: str) -> pd.DataFrame:
    path = RAW_DIR / CSV_FILES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run download_raw() first."
        )
    return pd.read_csv(path)


# --- team normalization ----------------------------------------------------

def build_name_map() -> dict[str, str]:
    """Map historical/former team names -> current name using
    ``former_names.csv``. Columns: current, former, start_date, end_date.

    We build a *string-only* former->current map. (Date-bounded remapping is
    unnecessary here: the dataset already stores current names, so this is a
    safety net for stragglers.)"""
    fn = _read_raw("former_names")
    name_map: dict[str, str] = {}
    for _, row in fn.iterrows():
        former = str(row["former"]).strip()
        current = str(row["current"]).strip()
        if former and current and former != current:
            name_map[former] = current
    return name_map


def normalize_teams(df: pd.DataFrame, name_map: dict[str, str]) -> pd.DataFrame:
    df = df.copy()
    df["home_team"] = df["home_team"].str.strip().replace(name_map)
    df["away_team"] = df["away_team"].str.strip().replace(name_map)
    return df


# --- cleaning --------------------------------------------------------------

def clean_results(
    start: str = DEFAULT_START,
    end: str | None = None,
    competitive_only: bool = False,
) -> pd.DataFrame:
    """Load, clean, and filter ``results.csv``.

    Parameters
    ----------
    start, end : date strings (inclusive). ``end=None`` means "up to latest".
    competitive_only : if True, drop matches whose tournament is "Friendly".
        Default False (keep all matches — friendlies add volume; whether they
        help is a backtest question, not a cleaning one).

    Returns a tidy frame with parsed dates, integer scores, intact ``neutral``,
    normalized team names, and a categorical-friendly ``tournament``.
    """
    df = _read_raw("results")
    df = normalize_teams(df, build_name_map())

    # Parse + filter dates.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[df["date"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["date"] <= pd.Timestamp(end)]

    # Scores must be present and non-negative integers.
    df = df.dropna(subset=["home_score", "away_score"])
    df = df[(df["home_score"] >= 0) & (df["away_score"] >= 0)]
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    # neutral flag: load-bearing. Coerce to clean boolean, keep it.
    df["neutral"] = df["neutral"].astype(bool)

    if competitive_only:
        df = df[df["tournament"].str.lower() != "friendly"]

    # Drop self-matches / blank teams if any.
    df = df[df["home_team"].notna() & df["away_team"].notna()]
    df = df[df["home_team"] != df["away_team"]]

    df = df.sort_values("date").reset_index(drop=True)
    return df


# --- model-ready encoding --------------------------------------------------

@dataclass
class TeamIndex:
    """Bidirectional team <-> integer-id mapping for the model."""

    teams: list[str]
    to_id: dict[str, int]

    @classmethod
    def from_matches(cls, df: pd.DataFrame) -> "TeamIndex":
        teams = sorted(set(df["home_team"]) | set(df["away_team"]))
        return cls(teams=teams, to_id={t: i for i, t in enumerate(teams)})

    @property
    def n_teams(self) -> int:
        return len(self.teams)


def encode_matches(df: pd.DataFrame, index: TeamIndex | None = None):
    """Attach integer team ids used by the PyMC model. Returns
    ``(df_encoded, TeamIndex)``."""
    if index is None:
        index = TeamIndex.from_matches(df)
    df = df.copy()
    df["home_id"] = df["home_team"].map(index.to_id)
    df["away_id"] = df["away_team"].map(index.to_id)
    # Any team not in the index (e.g. encoding a holdout fixture) -> drop.
    df = df.dropna(subset=["home_id", "away_id"])
    df["home_id"] = df["home_id"].astype(int)
    df["away_id"] = df["away_id"].astype(int)
    return df, index


# --- persistence -----------------------------------------------------------

def save_processed(df: pd.DataFrame, name: str = "matches.parquet") -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / name
    df.to_parquet(path, index=False)
    return path


def load_processed(name: str = "matches.parquet") -> pd.DataFrame:
    path = PROCESSED_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found — run the pipeline first.")
    return pd.read_parquet(path)


def build_dataset(
    start: str = DEFAULT_START,
    end: str | None = None,
    competitive_only: bool = False,
    force_download: bool = False,
) -> pd.DataFrame:
    """End-to-end: download (if needed) -> clean -> save -> return."""
    download_raw(force=force_download)
    df = clean_results(start=start, end=end, competitive_only=competitive_only)
    save_processed(df)
    return df


if __name__ == "__main__":
    matches = build_dataset()
    idx = TeamIndex.from_matches(matches)
    print(f"Matches (>= {DEFAULT_START}): {len(matches):,}")
    print(f"Date range: {matches['date'].min().date()} -> "
          f"{matches['date'].max().date()}")
    print(f"Teams: {idx.n_teams}")
    print(f"Neutral-venue share: {matches['neutral'].mean():.1%}")
    print(matches[["date", "home_team", "away_team", "home_score",
                   "away_score", "tournament", "neutral"]].tail(8).to_string())

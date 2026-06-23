"""Build-time Polymarket odds resolver (optional, fail-soft, OUTSIDE the CC0 core).

The "Model vs Market" tab compares our model probabilities against Polymarket's
market-implied probabilities. To keep the deliverable a static page that still
shows *live* odds, we split the work:

* **Build time (this module):** resolve, for each *upcoming* fixture, the exact
  Polymarket event slug + the market identifiers (which `groupItemTitle` is the
  home/draw/away market; which `question` is the BTTS / Over-2.5 market). We also
  resolve the tournament-winner market team mapping. Matching is done here, once,
  in Python — where names can be normalized and aliased reliably — and the
  resolved identifiers are baked into the page. A build-time price *snapshot* is
  captured as an offline fallback.

* **Run time (the page's JS):** fetch live prices for those baked slugs straight
  from the keyless Gamma API (CORS is open), de-vig, and recompute edges. No
  matching logic ships to the browser.

Everything here is best-effort: any network/parse failure returns empty, the
caller treats the tab as simply unavailable, and the model pipeline is never
touched (this module is never imported by data/model/predict/simulate).

Data source: Polymarket Gamma API (https://gamma-api.polymarket.com), keyless.
Used for personal, non-commercial, educational comparison — not betting advice.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import requests

GAMMA = "https://gamma-api.polymarket.com"
SERIES_ID = 11433            # soccer-fifwc (2026 FIFA World Cup) series
WINNER_SLUG = "world-cup-winner"
TIMEOUT = 20

# The canonical per-match 1X2 event: ``fifwc-{home3}-{away3}-{YYYY-MM-DD}`` with
# NOTHING after the date. Variants (``-more-markets``, ``-second-half-result``,
# ``-double-chance`` …) share the same team-pair + date and would otherwise
# clobber the main event in the index, so we match the exact shape.
_MATCH_SLUG_RE = re.compile(r"^fifwc-[a-z]+-[a-z]+-\d{4}-\d{2}-\d{2}$")

# Normalized Polymarket spelling -> our canonical team name, for the handful
# that don't match after accent/case normalization. (Polymarket uses different
# spellings in per-match events vs the winner market, e.g. "DR Congo" / "Congo
# DR", "United States" / "USA" — both directions are covered here.)
_ALIAS = {
    "czechia": "Czech Republic",
    "usa": "United States",
    "turkiye": "Turkey",
    "congo dr": "DR Congo",
}


def _norm(s: str) -> str:
    """Lowercase, strip accents and punctuation — a stable join key for team
    names across our data and Polymarket's spellings."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower()
    return "".join(c for c in s if c.isalnum() or c == " ").strip()


def _to_our_name(poly_name: str, our_index: dict[str, str]) -> str | None:
    """Map a Polymarket team spelling to our canonical name (or None)."""
    n = _norm(poly_name)
    if n in _ALIAS:
        return _ALIAS[n]
    return our_index.get(n)


def _get(path: str, params: dict):
    try:
        r = requests.get(f"{GAMMA}{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _price0(market: dict) -> float | None:
    """The implied probability of a binary market's first outcome (Yes/Over)."""
    import json
    raw = market.get("outcomePrices")
    if not raw:
        return None
    try:
        vals = json.loads(raw) if isinstance(raw, str) else raw
        return float(vals[0])
    except Exception:
        return None


def fetch_open_events(max_pages: int = 6) -> list[dict]:
    """All open events in the World Cup series (paginated). Best-effort."""
    out: list[dict] = []
    for pg in range(max_pages):
        batch = _get("/events", {"series_id": SERIES_ID, "closed": "false",
                                 "limit": 100, "offset": pg * 100})
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
    return out


def _resolve_match(event: dict, by_slug: dict, our_index: dict) -> dict | None:
    """Resolve one per-match event into baked identifiers + a price snapshot."""
    teams = event.get("teams") or []
    if len(teams) != 2:
        return None
    title = event.get("title", "")          # e.g. "Switzerland vs. Canada"
    home_git = draw_git = away_git = None
    snap_h = snap_d = snap_a = None
    # Map our home/away to the two non-draw markets by groupItemTitle.
    for m in event.get("markets", []):
        git = m.get("groupItemTitle") or ""
        if "draw" in git.lower():
            draw_git, snap_d = git, _price0(m)
        else:
            snap = _price0(m)
            # tag later once we know which is home vs away
            if home_git is None:
                home_git, snap_h = git, snap
            else:
                away_git, snap_a = git, snap
    if not (home_git and away_git and draw_git):
        return None

    # More-markets bundle (BTTS / totals) — same base slug + suffix.
    more_slug = f"{event['slug']}-more-markets"
    more = by_slug.get(more_slug)
    btts_q = o25_q = None
    snap_btts = snap_o25 = None
    if more:
        btts_q = f"{title}: Both Teams to Score"
        o25_q = f"{title}: O/U 2.5"
        for m in more.get("markets", []):
            q = m.get("question") or ""
            if q == btts_q:
                snap_btts = _price0(m)
            elif q == o25_q:
                snap_o25 = _price0(m)
        if snap_btts is None:
            btts_q = None
        if snap_o25 is None:
            o25_q = None

    return {
        "slug": event["slug"],
        "more_slug": more_slug if (btts_q or o25_q) else None,
        "home_git": home_git, "draw_git": draw_git, "away_git": away_git,
        "btts_q": btts_q, "o25_q": o25_q,
        "volume": float(event.get("volume") or 0),
        "snapshot": {"h": snap_h, "d": snap_d, "a": snap_a,
                     "btts": snap_btts, "o25": snap_o25},
    }


def resolve_odds(fixtures: Iterable[tuple], our_teams: list[str]):
    """Resolve Polymarket identifiers for upcoming fixtures + the winner market.

    ``fixtures`` is an iterable of ``(home_team, away_team, date_str)`` for the
    *upcoming* matches we want to compare (``date_str`` = ``YYYY-MM-DD``).

    Returns ``(matches, title)`` where:
      * ``matches`` maps ``(home, away, date_str)`` -> resolved match dict
        (slug, market ids, volume, price snapshot), for matches found live;
      * ``title`` is ``{"slug", "sum", "teams": {our_name: {git, snap}}}`` for
        the tournament-winner market (``sum`` = overround denominator over all
        listed teams, for de-vigging the baked snapshot).
    Both are empty on any failure — the caller degrades gracefully.
    """
    our_index = {_norm(t): t for t in our_teams}
    events = fetch_open_events()
    if not events:
        return {}, {}
    by_slug = {e.get("slug", ""): e for e in events}

    # Index per-match events by unordered, normalized team pair + date.
    match_index: dict[tuple, dict] = {}
    for e in events:
        slug = e.get("slug", "")
        if not _MATCH_SLUG_RE.match(slug):
            continue
        teams = e.get("teams") or []
        if len(teams) != 2:
            continue
        names = [_to_our_name(t.get("name", ""), our_index) for t in teams]
        if None in names:
            continue
        date = (e.get("eventDate") or "")[:10]
        key = (frozenset(names), date)
        match_index[key] = e

    matches: dict[tuple, dict] = {}
    for home, away, date_str in fixtures:
        key = (frozenset((home, away)), date_str)
        e = match_index.get(key)
        if not e:
            continue
        resolved = _resolve_match(e, by_slug, our_index)
        if not resolved:
            continue
        # Tag home/away gits correctly (the two non-draw markets were read in
        # event order; map them to our home/away by name).
        gh = _to_our_name(resolved["home_git"], our_index)
        if gh == away:                      # event listed away-market first
            resolved["home_git"], resolved["away_git"] = (
                resolved["away_git"], resolved["home_git"])
            s = resolved["snapshot"]
            s["h"], s["a"] = s["a"], s["h"]
        matches[(home, away, date_str)] = resolved

    # Tournament-winner market.
    title: dict = {}
    win = _get("/events", {"slug": WINNER_SLUG})
    if win:
        ev = win[0]
        teams_map: dict[str, dict] = {}
        total = 0.0
        for m in ev.get("markets", []):
            p = _price0(m)
            if p is not None:
                total += p
            our = _to_our_name(m.get("groupItemTitle", ""), our_index)
            if our and p is not None:
                teams_map[our] = {"git": m.get("groupItemTitle"), "snap": p}
        title = {"slug": WINNER_SLUG, "sum": total or 1.0, "teams": teams_map}

    return matches, title

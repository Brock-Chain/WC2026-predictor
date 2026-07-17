"""Curated edge-board data: the best current bets (with backing data) and the
penalty-shootout scout, both surfaced on the site's "Best Bets" tab.

This is RESEARCH-DERIVED, hand-curated data — NOT computed from the trace. It
combines the model's numbers with external signals the goals-only model is blind
to (injuries, rotation, penalty-shootout profiles). Update it per knockout round.
Kept dependency-free (pure data) so a stale entry can never break the report build.

Governing rule (see the edge-finder skill): divergence is not value. Only bets
with a NAMED mechanism the market hasn't priced belong in BEST_BETS.
"""

from __future__ import annotations

# Round + date this board reflects (shown in the header).
AS_OF = "2026-07-17 · Final + 3rd place"

# --- Best bets: status is BET (actionable) / WATCH (conditional) -------------
# Two games left, both markets efficient. No named, unpriced edge → no open bets.
BEST_BETS: list[dict] = []

# Shown as the tab's main note whenever there are no open bets.
PASS_NOTE = (
    "No open bets — the tournament is down to two games and both markets are efficient. "
    "FINAL, Spain v Argentina: the model leans Argentina (52% to lift the cup, on the Dibu Martínez "
    "shootout edge + reigning-champ pedigree), but Polymarket favours SPAIN 59% — and that's the "
    "defensible number: Spain have been the tournament's best side (6+ clean sheets, beat France 2-0 "
    "in the semi), which a goals-only model under-weights. The model's Argentina lean is most likely "
    "its blind spot, not an edge → Pass (Argentina's shootout dominance keeps the trophy genuinely "
    "live in the ~29% of finals that reach penalties). 3RD PLACE, France v England: the model likes "
    "England (40% vs France's ~50% market), but it's a low-stakes bronze game → Pass. "
    "✓ Tournament track record: R16 calls England-to-advance (Mexico 2-3 England) and "
    "Belgium-to-advance (USA 1-4 Belgium) both WON; the QF/SF slates were correctly all-Pass."
)

# --- Penalty-shootout scout --------------------------------------------------
# style: 'pre-committer' (dives early off a scouted dossier), 'reactor' (waits &
# reads the shot), 'mixed' (prepared reads + deception), 'unknown' (no profile).
PENALTY_SCOUT = [
    {
        "home": "Spain", "away": "Argentina", "date": "Jul 19 · FINAL",
        "so_home": 30, "draw90": 29, "edge": "Argentina (huge)",
        "home_gk": ("Unai Simón", "reactor"), "away_gk": ("Emi Martínez", "mixed"),
        "home_takers": "Oyarzábal 87.5%, Rodri, Yamal",
        "away_takers": "Messi 84.6% (shootout), Lautaro, Álvarez, Dybala",
        "note": "The decisive sub-plot of the final. Dibu Martínez is the world's best shootout GK "
                "(Argentina 6-1 all-time, won the '22 title on penalties); Spain have the WORST WC "
                "shootout record of any nation (1W-4L). Polymarket favours Spain 59% to lift the cup "
                "(they've been the better side in open play), but in the ~29% of finals that reach "
                "penalties Argentina are heavy favourites — which is why the model (Argentina 52% "
                "incl. pens) and the reigning-champ narrative keep the trophy genuinely live.",
    },
    {
        "home": "France", "away": "England", "date": "Jul 18 · 3rd place",
        "so_home": 45, "draw90": 29, "edge": "England (slight)",
        "home_gk": ("Maignan", "reactor"), "away_gk": ("Pickford", "pre-committer"),
        "home_takers": "Mbappé, Olise, Dembélé",
        "away_takers": "Kane 88%, Saka, Rashford, Eze",
        "note": "England are 1W-3L but improving (Pickford's dossier + a deep taker pool); France are "
                "2W-3L with back-to-back final losses ('06, '22). Slight England edge if it goes the "
                "distance — but this is a low-stakes bronze game where motivation, not pens, decides it.",
    },
]

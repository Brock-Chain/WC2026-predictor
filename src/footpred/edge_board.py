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
AS_OF = "2026-07-07 · Quarter-finals"

# --- Best bets: status is BET (actionable) / WATCH (conditional) -------------
# QF slate read: NO open bets. Deep-knockout markets are razor-sharp — every
# model-vs-market divergence traces to a known model bias (under-rating
# favourites; over-rating reputation-favourite Belgium), and on each game a
# second independent estimator (Opta / Kalshi / the sharp sportsbook line) sits
# WITH the market against our model. Divergence ≠ value → Pass across the board.
BEST_BETS: list[dict] = []

# Shown as the tab's main note whenever there are no open bets.
PASS_NOTE = (
    "No open bets this round — the quarter-final slate (plus the two remaining R16 games) is "
    "razor-sharp, and on every game a second independent estimator sits with the market against "
    "our model. France v Morocco: model 43% vs market 61% France — the under-favourite bias, and "
    "Morocco are genuinely elite (Tchouaméni's absence is already in the price). Spain v Belgium: "
    "the sportsbook line is already ~75% Spain-to-advance, past our known Belgium-overrate (Belgium's "
    "4-1 vs USA came with De Bruyne benched vs a weak side). Norway v England: Kalshi 51/26/24 ≈ "
    "Polymarket, so our England lean is the outlier (Quansah suspended, Reece James a doubt explain "
    "the market's discount). Argentina v Egypt and Switzerland v Colombia are near-aligned. "
    "Divergence ≠ value → Pass.  ✓ Track record: last round's two calls — England to advance "
    "(Mexico 2-3 England) and Belgium to advance (USA 1-4 Belgium) — both WON."
)

# --- Penalty-shootout scout --------------------------------------------------
# style: 'pre-committer' (dives early off a scouted dossier), 'reactor' (waits &
# reads the shot), 'mixed' (prepared reads + deception), 'unknown' (no profile).
PENALTY_SCOUT = [
    {
        "home": "Argentina", "away": "Egypt", "date": "Jul 7 · R16",
        "so_home": 74, "draw90": 24, "edge": "Argentina (huge)",
        "home_gk": ("Emi Martínez", "mixed"), "away_gk": ("Shobeir", "unknown"),
        "home_takers": "Messi 84.6% (shootout), Lautaro, Álvarez, De Paul",
        "away_takers": "Salah (Panenka vs AUS), Marmoush — both missed the Jan-'26 AFCON shootout",
        "note": "Dibu Martínez is the world's best shootout GK (Argentina 6-1 all-time, won the '22 "
                "title on shootouts). Egypt won their R32 shootout vs Australia (Salah rehabbed with a "
                "Panenka), but Argentina's edge is enormous — though at ~80% to win in 90, pens are unlikely.",
    },
    {
        "home": "Switzerland", "away": "Colombia", "date": "Jul 7 · R16",
        "so_home": 50, "draw90": 27, "edge": "Even (no edge)",
        "home_gk": ("Kobel", "pre-committer"), "away_gk": ("Vargas", "mixed"),
        "home_takers": "Xhaka, Embolo, Ndoye",
        "away_takers": "James 83%, L. Díaz, Arias, Ríos",
        "note": "Both nations are 0-1 in WC shootouts (SUI lost to Ukraine '06, COL to England '18) — "
                "symmetric and inexperienced. No shootout edge either way.",
    },
    {
        "home": "France", "away": "Morocco", "date": "Jul 9 · QF",
        "so_home": 45, "draw90": 31, "edge": "Morocco (slight, if it gets there)",
        "home_gk": ("Maignan", "reactor"), "away_gk": ("Bono", "mixed"),
        "home_takers": "Mbappé, Olise, Dembélé",
        "away_takers": "Rahimi, Saibari (if fit), Hakimi",
        "note": "Bono is elite in shootouts (Morocco 2/2 recent WC — beat Spain '22, Netherlands '26); "
                "France are 2W-3L with back-to-back final losses ('06, '22). Slight Morocco edge if it "
                "reaches pens — but that's only ~25-30% of outcomes; France are ~61% to win in 90.",
    },
    {
        "home": "Spain", "away": "Belgium", "date": "Jul 10 · QF",
        "so_home": 48, "draw90": 26, "edge": "Wash (both keepers poor)",
        "home_gk": ("Unai Simón", "reactor"), "away_gk": ("Courtois", "pre-committer"),
        "home_takers": "Oyarzábal 87.5%, Rodri, Yamal",
        "away_takers": "De Bruyne, Tielemans (124' winner vs SEN), Lukaku",
        "note": "Spain have the WORST WC shootout record of any nation (1W-4L — incl. the 2022 loss to "
                "Morocco, not Belgium); Courtois saves few penalties historically (~17%) but is composed. "
                "A genuine wash — if anything Spain's record is the bigger red flag.",
    },
    {
        "home": "Norway", "away": "England", "date": "Jul 11 · QF",
        "so_home": 40, "draw90": 25, "edge": "England",
        "home_gk": ("Nyland", "mixed"), "away_gk": ("Pickford", "pre-committer"),
        "home_takers": "Haaland, Ødegaard, Sørloth",
        "away_takers": "Kane 88%, Saka, Rashford, Eze",
        "note": "England are 1W-3L but improving (Pickford's dossier + a deep taker pool); Norway have "
                "ZERO WC shootout experience (first-ever QF). England edge if it goes the distance.",
    },
]

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
AS_OF = "2026-07-04 · Round of 16"

# --- Best bets: status is BET (actionable) / WATCH (conditional) -------------
# R16 read: a very sharp slate. Opta + the sportsbooks agree with the market on
# six of eight games (our model's divergences are its known blind spots). The two
# actionable spots are the same shape — Polymarket underpricing the quality AWAY
# side's "to advance" because home money floods the host — and both are confirmed
# by a second independent estimate (Opta) sitting ABOVE the soft Polymarket line.
BEST_BETS = [
    {
        "status": "BET",
        "bet": "England to advance",
        "game": "Mexico v England",
        "date": "Jul 5 · Mexico City (Azteca)",
        "market": "~56%",
        "model": "66%",
        "edge": "+4 to +10pp",
        "conviction": "Medium-low",
        "size": "1 unit (small) — Polymarket to-advance market only",
        "mechanism": (
            "A triangulation edge, not a lone-model call. The sharper, more-liquid "
            "sportsbooks price England ~60% to advance and Opta's tournament ratio "
            "implies ~66% — BOTH above Polymarket's soft ~56%. The Azteca altitude "
            "(2,240m — a real factor our goals-only model under-weights) is ALREADY "
            "baked into those sharp numbers, and they are STILL above Polymarket. So "
            "the gap is Polymarket home/public bias on Mexico, not new information "
            "the sharps missed. Buy England-to-advance where it is cheap."
        ),
        "signals": [
            "England-advance: Polymarket ~56% < sportsbooks ~60% < Opta ~66% — Polymarket is the soft outlier",
            "Altitude is already in the sharp books' number, yet they still have England higher → the discount is home-public bias",
            "Mexico 0-2 all-time in WC shootouts (dreadful) vs England improving (Pickford dossier, deep taker pool) — a shootout tilts England",
            "Kane in record WC form (13 goals); Mexico's 0.56 xG-allowed came against far weaker attacks than this",
        ],
        "caveat": (
            "This is the TO-ADVANCE market, not England-to-win-90 — altitude makes a "
            "comfortable regulation win unlikely (pass on the 1X2). England are missing "
            "RB Reece James (hamstring) and Rice's fitness is a question; altitude is a "
            "genuine unknown, so our 66% may be a touch high — size small. Revisit at "
            "the ~6:00 PM ET Jul 5 teamsheet; if Rice is out/limited, downgrade to Pass."
        ),
    },
    {
        "status": "WATCH",
        "bet": "Belgium to advance",
        "game": "United States v Belgium",
        "date": "Jul 6 · Seattle",
        "market": "~52%",
        "model": "63%",
        "edge": "+5pp (fair ~57%)",
        "conviction": "Do not bet yet — minimum only",
        "size": "—",
        "mechanism": (
            "Same host-overbet shape as Mexico-England: Polymarket ~52% Belgium-advance "
            "is soft vs Opta's ~57-58% (76% of tickets are on the USA — home public bias). "
            "But TWO flags shrink the edge. (1) Our own 63% is inflated — the model's "
            "documented Belgium-reputation blind spot: Belgium beat Senegal 3-2 AET while "
            "being out-xG'd 1.84 to 3.18 (running hot, not playing well). (2) The USA crowd "
            "is a GENUINE partisan home edge here (Seattle), unlike Canada's phantom Houston "
            "game. Net fair ~57% vs market ~52% ≈ only +5pp."
        ),
        "signals": [
            "Polymarket ~52% < Opta ~57-58% Belgium-advance — soft home-team line",
            "BUT our 63% is ~5-6pp too high (Belgium out-xG'd 1.84–3.18 by Senegal; won on a 124' penalty)",
            "USA missing top scorer Balogun (red vs Bosnia, suspended) — helps Belgium, but likely already priced",
            "Courtois = elite shootout GK; USA minimal WC shootout experience — a tiebreaker for Belgium",
        ],
        "caveat": (
            "This is the SAME 'Belgium-to-advance, model-above-market' signal that nearly "
            "lost in the R32 (Belgium 0-2 down to Senegal). They are winning on Courtois and "
            "luck, not performance. Minimum stake at most, and only if Lukaku starts and the "
            "line stays ≥ current; pass if it tightens to Belgium -125. Never bet Belgium-to-win-90."
        ),
    },
]

# Passed the rest: on all six, Opta and/or the sportsbooks agree with the market —
# our model's divergences are its known biases, not named edges. Tab footnote.
PASS_NOTE = (
    "Everything else is a Pass — and Opta agrees with the market on all six. Canada v Morocco "
    "(phantom host edge: the game is in Houston with a Morocco-leaning crowd; Opta 52% Morocco), "
    "Paraguay v France (France near-full-strength; Opta 87% France), Brazil v Norway (Raphinha + "
    "Paquetá out, Haaland flying — Opta = market, our model is the outlier), Portugal v Spain "
    "(Spain's class; all models ~50%), Argentina v Egypt (Salah fit after all; Argentina fairly "
    "priced ~84% to advance), Switzerland v Colombia (Colombia's cross-continent travel + fewer "
    "rest days + James Rodríguez's uncertain role). No named unpriced edge → no bet."
)

# --- Penalty-shootout scout --------------------------------------------------
# style: 'pre-committer' (dives early off a scouted dossier), 'reactor' (waits &
# reads the shot), 'mixed' (prepared reads + deception), 'unknown' (no profile).
PENALTY_SCOUT = [
    {
        "home": "Canada", "away": "Morocco", "date": "Jul 4",
        "so_home": 33, "draw90": 30, "edge": "Morocco (clear)",
        "home_gk": ("Crépeau", "unknown"), "away_gk": ("Bono", "mixed"),
        "home_takers": "J. David 82%; Larin & Davies have missed big shootout pens",
        "away_takers": "Rahimi, Saibari (netted the decider vs NED); Hakimi & Díaz have missed",
        "note": "Bono is arguably the world's best shootout GK right now — Morocco are 2/2 in "
                "recent WC shootouts (beat Spain '22 and the Netherlands '26). Canada have no WC "
                "shootout history. The market already prices Morocco — no Canada bet.",
    },
    {
        "home": "Paraguay", "away": "France", "date": "Jul 4",
        "so_home": 55, "draw90": 25, "edge": "Paraguay (slight, if it gets there)",
        "home_gk": ("Gill", "unknown"), "away_gk": ("Maignan", "reactor"),
        "home_takers": "Canale (buried the winner vs GER), Enciso, Almirón — riding confidence",
        "away_takers": "Mbappé, Olise, Rabiot — France 2W-3L with documented shootout anxiety",
        "note": "Paraguay are 2/2 in WC shootouts (Japan '10, Germany '26) and Gill just saved two "
                "vs Germany; France are 2W-3L. But France are ~85% to win in 90 — a shootout is a long shot.",
    },
    {
        "home": "Brazil", "away": "Norway", "date": "Jul 5",
        "so_home": 60, "draw90": 23, "edge": "Brazil (modest)",
        "home_gk": ("Alisson", "reactor"), "away_gk": ("Nyland", "unknown"),
        "home_takers": "Vinícius, M. Cunha, Casemiro; Neymar if he's on the pitch",
        "away_takers": "Haaland, Ødegaard, Sørloth — but zero WC shootout experience as a nation",
        "note": "Brazil are 8W-7L all-time in WC shootouts (won the '94 final); Norway have NEVER "
                "contested a WC shootout. Experience favors Brazil, but only 53% historically — modest.",
    },
    {
        "home": "Mexico", "away": "England", "date": "Jul 5",
        "so_home": 40, "draw90": 26, "edge": "England (clear)",
        "home_gk": ("Rangel", "unknown"), "away_gk": ("Pickford", "pre-committer"),
        "home_takers": "Thin, untested taker pool; Mexico are 0-2 all-time in WC shootouts",
        "away_takers": "Kane 88%, Saka, Palmer, Bellingham — the deepest elite pool in the field",
        "note": "Mexico are 0W-2L in WC shootouts (dreadful); England are 1W-3L but improving, with "
                "Pickford's water-bottle dossier and a deep taker pool. Clear England edge — and with "
                "a ~26% draw prob, a shootout is genuinely live. This reinforces England to advance.",
    },
    {
        "home": "Portugal", "away": "Spain", "date": "Jul 6",
        "so_home": 58, "draw90": 27, "edge": "Portugal (clear)",
        "home_gk": ("Diogo Costa", "mixed"), "away_gk": ("Unai Simón", "reactor"),
        "home_takers": "Ronaldo 86%, B. Fernandes 91%, Neves, N. Mendes",
        "away_takers": "Oyarzábal 87.5%, Rodri, Yamal",
        "note": "Portugal have a near-perfect recent shootout record and beat Spain 5-3 on pens in the "
                "2025 Nations League final; Spain are 1W-4L in WC shootouts — the worst of any major "
                "nation. Real Portugal edge, but the to-advance line already discounts it (no clean vehicle).",
    },
    {
        "home": "United States", "away": "Belgium", "date": "Jul 6",
        "so_home": 42, "draw90": 25, "edge": "Belgium (clear)",
        "home_gk": ("Freese", "pre-committer"), "away_gk": ("Courtois", "pre-committer"),
        "home_takers": "Pulisic 87%; taker pool thinner with Balogun suspended",
        "away_takers": "Lukaku 85%, De Bruyne 75%, Tielemans (buried the 124' winner vs SEN)",
        "note": "Courtois is an elite shootout keeper (Belgium won the '22 R16 shootout 3-0 vs Spain); "
                "the USA have minimal WC shootout experience. Belgium edge in a shootout — part of why "
                "Belgium-to-advance stays a WATCH rather than a full bet.",
    },
    {
        "home": "Argentina", "away": "Egypt", "date": "Jul 7",
        "so_home": 74, "draw90": 24, "edge": "Argentina (huge)",
        "home_gk": ("Emi Martínez", "mixed"), "away_gk": ("Shobeir", "unknown"),
        "home_takers": "Messi 84.6% (shootout), Lautaro, Álvarez, De Paul",
        "away_takers": "Salah (Panenka vs AUS), Marmoush — both missed the Jan-'26 AFCON shootout",
        "note": "Dibu Martínez is the world's best shootout GK (Argentina 6-1 all-time, won the '22 "
                "title on shootouts). Egypt won their R32 shootout vs Australia (Salah rehabbed with a "
                "Panenka), but Argentina's edge is enormous — though at ~80% to win in 90, pens are unlikely.",
    },
    {
        "home": "Switzerland", "away": "Colombia", "date": "Jul 7",
        "so_home": 50, "draw90": 27, "edge": "Even (no edge)",
        "home_gk": ("Kobel", "pre-committer"), "away_gk": ("Vargas", "mixed"),
        "home_takers": "Xhaka, Embolo, Ndoye",
        "away_takers": "James 83%, L. Díaz, Arias, Ríos",
        "note": "Both nations are 0-1 in WC shootouts (SUI lost to Ukraine '06, COL to England '18) — "
                "symmetric and inexperienced. No shootout edge either way.",
    },
]

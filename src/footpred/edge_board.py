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
AS_OF = "2026-07-01 · Round of 32 → Round of 16"

# --- Best bets: status is BET (actionable) / WATCH (conditional) -------------
BEST_BETS = [
    {
        "status": "BET",
        "bet": "Belgium to advance",
        "game": "Belgium v Senegal",
        "date": "Jul 1 · Seattle",
        "market": "~60%",
        "model": "70%",
        "edge": "+10pp",
        "conviction": "Medium",
        "size": "2 units (≈½-Kelly on a conservative 65% fair)",
        "mechanism": (
            "Three independent signals point the same way. (1) The model rates "
            "Belgium's regulation advance ABOVE the market — the opposite of its "
            "usual under-favorite bias, so it survives the bias filter. (2) A "
            "nameable penalty edge: Courtois is a dossier-driven pre-committer, "
            "while Senegal's shootout specialist Édouard Mendy is OUT — his "
            "untested backup Diaw replaces him. (3) Belgium's takers (Lukaku 85%, "
            "De Bruyne 75%) outrank Senegal's."
        ),
        "signals": [
            "Model advance 70% vs market 60% (+10pp) — contra the under-favorite bias",
            "Courtois = pre-committer with confirmed shooter dossiers",
            "Senegal's shootout hero Mendy OUT → Diaw (2 career pen saves) starts",
            "Taker quality: Lukaku 85% / De Bruyne 75% > Mané (~53%) / Jackson",
        ],
        "caveat": (
            "Thin-ish book ($1.2M) and a Jul 1 kickoff — act early. A shootout is "
            "only reached ~15% of the time, so most of the edge is the regulation "
            "model, not the penalty angle. Size to conviction, not to the full Kelly."
        ),
    },
    {
        "status": "WATCH",
        "bet": "Australia to advance",
        "game": "Australia v Egypt",
        "date": "Jul 3 · Dallas",
        "market": "~44%",
        "model": "59%",
        "edge": "+16pp",
        "conviction": "Do not bet yet",
        "size": "—",
        "mechanism": (
            "The model's single biggest divergence (a sign-flip: it makes "
            "Australia the favorite) — but this is almost certainly a MODEL BLIND "
            "SPOT, not an edge. Opta's supercomputer (Egypt ~54%) agrees with the "
            "market against us, and the goals-only model can't see Egypt's "
            "individual attacking quality (Salah + Marmoush) vs Australia's "
            "Championship-level forward line."
        ),
        "signals": [
            "Opta ~54% Egypt to advance — 2nd independent model agrees with market",
            "Egypt drew Belgium in the group; better opposition quality",
            "Salah hamstring is the ONE live variable — flip to a BET only if he is ruled out at the teamsheet",
            "Egypt's top 2 takers (Salah, Marmoush) BOTH missed the Jan-2026 AFCON shootout — the sole pro-Australia note",
        ],
        "caveat": (
            "Highest draw prob on the board (32%), so a shootout is genuinely "
            "live. But back Australia ONLY if Salah is confirmed out — otherwise "
            "the market/Opta are right and this is our model's blind spot."
        ),
    },
]

# Passed the rest: the model under-rates the favorites (its known bias) and the
# market is right. Shown as a one-line footnote on the tab.
PASS_NOTE = (
    "Everything else is a Pass: Argentina / England / Spain / Colombia / Portugal "
    "to advance all show the model's known under-favorite bias, and the market "
    "prices them fairly. No named mechanism → no bet."
)

# --- Penalty-shootout scout --------------------------------------------------
# style: 'pre-committer' (dives early off a scouted dossier), 'reactor' (waits &
# reads the shot), 'mixed' (prepared reads + deception), 'unknown' (no profile).
PENALTY_SCOUT = [
    {
        "home": "Belgium", "away": "Senegal", "date": "Jul 1",
        "so_home": 62, "draw90": 27, "edge": "Belgium",
        "home_gk": ("Courtois", "pre-committer"), "away_gk": ("Diaw", "unknown"),
        "home_takers": "Lukaku 85%, De Bruyne 75%, Tielemans",
        "away_takers": "Mané (~53%), Sarr 75%, Jackson",
        "note": "Courtois studies dossiers and pre-picks a side; Senegal's shootout "
                "specialist Mendy is OUT (Diaw has 2 career pen saves). Clear Belgium edge.",
    },
    {
        "home": "England", "away": "DR Congo", "date": "Jul 1",
        "so_home": 67, "draw90": 20, "edge": "England",
        "home_gk": ("Pickford", "pre-committer"), "away_gk": ("Mpasi / Fayulu", "unknown"),
        "home_takers": "Kane 88%, Toney 93%, Saka, Rashford, Bellingham",
        "away_takers": "Wissa, Mbemba; Bakambu & Masuaku unreliable",
        "note": "Pickford's water-bottle cheat-sheet + the deepest elite taker pool at "
                "the tournament. Big England edge — but a shootout is unlikely (Eng heavy fav).",
    },
    {
        "home": "United States", "away": "Bosnia and Herzegovina", "date": "Jul 1",
        "so_home": 55, "draw90": 21, "edge": "USA (modest)",
        "home_gk": ("Freese", "pre-committer"), "away_gk": ("Vasilj", "unknown"),
        "home_takers": "Pulisic 87%, Richards, Tillman; Balogun 62% (weak link)",
        "away_takers": "Džeko 56.5% (age 40), Alajbegović, Demirović",
        "note": "Freese is an analytical pre-committer (Harvard pen paper, reads hips). "
                "But Bosnia qualified via TWO shootouts and Vasilj intimidates — only a modest edge.",
    },
    {
        "home": "Switzerland", "away": "Algeria", "date": "Jul 2",
        "so_home": 56, "draw90": 26, "edge": "Switzerland (narrow)",
        "home_gk": ("Kobel", "pre-committer"), "away_gk": ("L. Zidane", "unknown"),
        "home_takers": "Xhaka, Embolo (both converting), Amdouni",
        "away_takers": "Mahrez 75% (50% recent) — no confirmed 2nd taker",
        "note": "Kobel arrives with a dossier vs Zidane (no shootout record). But Algeria's "
                "coach Petković used to manage Switzerland and knows Kobel — partly neutralised.",
    },
    {
        "home": "Spain", "away": "Austria", "date": "Jul 2",
        "so_home": 58, "draw90": 22, "edge": "Spain",
        "home_gk": ("Unai Simón", "reactor"), "away_gk": ("Pentz", "unknown"),
        "home_takers": "Oyarzábal 87.5%, Rodri, Yamal; Morata a liability",
        "away_takers": "Arnautović 82%, Sabitzer 7/7 (100%)",
        "note": "Simón is a tested reactor (7 shootout saves for Spain). But Spain's recent "
                "shootout record is poor and Sabitzer is perfect — edge is real but modest.",
    },
    {
        "home": "Portugal", "away": "Croatia", "date": "Jul 2",
        "so_home": 53, "draw90": 25, "edge": "Portugal (coin-flip)",
        "home_gk": ("Diogo Costa", "mixed"), "away_gk": ("Livaković", "mixed"),
        "home_takers": "Ronaldo 86%, B. Fernandes 91%, Neves, N. Mendes",
        "away_takers": "Modrić 3/3 WC, Kramarić 90%, Perišić",
        "note": "Two elite shootout keepers. Diogo Costa (3/3 vs Slovenia, 1/1 vs Spain) is "
                "the slight differentiator vs Croatia's 4-0 WC shootout culture. Near 50/50.",
    },
    {
        "home": "Argentina", "away": "Cape Verde", "date": "Jul 3",
        "so_home": 78, "draw90": 15, "edge": "Argentina (huge)",
        "home_gk": ("Emi Martínez", "mixed"), "away_gk": ("Vozinha", "unknown"),
        "home_takers": "Messi 78% (84.6% shootout), Lautaro, Álvarez, De Paul",
        "away_takers": "R. Mendes, Rodrigues — no data at this level",
        "note": "Dibu is the world's best shootout GK (4W-0L, ~52% opp conversion + mind games). "
                "Dominant edge — but Argentina win in 90 ~81%, so a shootout is a long shot.",
    },
    {
        "home": "Australia", "away": "Egypt", "date": "Jul 3",
        "so_home": 57, "draw90": 32, "edge": "Australia (slight)",
        "home_gk": ("Mat Ryan", "reactor"), "away_gk": ("Shobeir", "unknown"),
        "home_takers": "Hrustić, Mabil (both scored the 2022 Peru shootout)",
        "away_takers": "Salah & Marmoush — BOTH missed the Jan-2026 AFCON shootout",
        "note": "Highest draw prob remaining (32%) → shootout is genuinely live. Egypt's two "
                "stars both missed their last shootout. NB: the market still (rightly) favors Egypt overall.",
    },
    {
        "home": "Colombia", "away": "Ghana", "date": "Jul 3",
        "so_home": 58, "draw90": 20, "edge": "Colombia",
        "home_gk": ("Vargas", "mixed"), "away_gk": ("Asare", "unknown"),
        "home_takers": "James 83%, L. Díaz, Arias, Ríos",
        "away_takers": "Jordan Ayew 17/17 (100%) — everyone else unknown",
        "note": "Ghana's Ayew is a perfect-record wildcard, but Ghana's #2-5 are unstudied and "
                "Asare is a domestic-league keeper on his first WC start (Ati-Zigi injured).",
    },
    {
        "home": "Canada", "away": "Morocco", "date": "Jul 4 · R16",
        "so_home": 30, "draw90": 28, "edge": "Morocco (clear)",
        "home_gk": ("Crépeau", "unknown"), "away_gk": ("Bono", "mixed"),
        "home_takers": "J. David 82%; Larin & Davies have missed big shootout pens",
        "away_takers": "Rahimi, Saibari (clutch vs NED); Díaz & Hakimi both missed",
        "note": "Bono is the best shootout GK in the world right now (67% save rate over 3 "
                "tournaments, counter-feint style). The market already prices Morocco — no Canada bet.",
    },
]

"""Ad-hoc model-vs-market scan across ALL Polymarket markets (not just 1X2).

For each upcoming fixture: derive every market the model can price from its
scoreline grid (game totals, team totals, BTTS, first-to-score), then dump every
market Polymarket actually lists in the per-match + more-markets bundle, so we can
spot edges beyond Home/Draw/Away. Read-only; hits the keyless Gamma API.
"""
import sys
sys.path.insert(0, "src")
import numpy as np
from footpred import model, predict as predmod, polymarket as pm

idata = model.load_trace()
teams = list(idata.attrs.get("teams", []))

TARGETS = [
    ("Uruguay", "Spain", "2026-06-26"),
    ("Cape Verde", "Saudi Arabia", "2026-06-26"),
    ("New Zealand", "Belgium", "2026-06-26"),
    ("Egypt", "Iran", "2026-06-26"),
    ("Panama", "England", "2026-06-27"),
    ("Croatia", "Ghana", "2026-06-27"),
    ("Colombia", "Portugal", "2026-06-27"),
    ("DR Congo", "Uzbekistan", "2026-06-27"),
    ("Algeria", "Austria", "2026-06-27"),
    ("Jordan", "Argentina", "2026-06-27"),
]

print("[scan] resolving polymarket markets ...")
matches, _ = pm.resolve_odds(TARGETS, teams)
events = pm.fetch_open_events()
by_slug = {e.get("slug", ""): e for e in events}
print(f"[scan] resolved {len(matches)}/{len(TARGETS)} matches, {len(events)} open events\n")


def model_block(pred):
    g = pred.grid
    G = g.shape[0]
    i = np.arange(G)
    tot = i[:, None] + i[None, :]
    hg = g.sum(axis=1)   # home-goal marginal
    ag = g.sum(axis=0)   # away-goal marginal
    lh, la = pred.exp_home_goals, pred.exp_away_goals
    p00 = float(g[0, 0])
    return {
        "1X2": (pred.p_home_win, pred.p_draw, pred.p_away_win),
        "proj": (lh, la),
        "G_O1.5": float(g[tot >= 2].sum()),
        "G_O2.5": float(g[tot >= 3].sum()),
        "G_O3.5": float(g[tot >= 4].sum()),
        "H_O0.5": float(hg[1:].sum()),
        "H_O1.5": float(hg[2:].sum()),
        "A_O0.5": float(ag[1:].sum()),
        "A_O1.5": float(ag[2:].sum()),
        "BTTS": float(g[1:, 1:].sum()),
        "FTS_home": (lh / (lh + la)) * (1 - p00),
        "FTS_away": (la / (lh + la)) * (1 - p00),
        "FTS_none": p00,
    }


for home, away, date in TARGETS:
    print("=" * 74)
    print(f"{home} v {away}   ({date})")
    try:
        pred = predmod.predict(idata, home, away, neutral=True)
    except Exception as ex:
        print(f"  MODEL ERROR: {ex}\n")
        continue
    mb = model_block(pred)
    h, d, a = mb["1X2"]
    lh, la = mb["proj"]
    print(f"  MODEL 1X2 H/D/A = {h:.0%}/{d:.0%}/{a:.0%}   proj {lh:.2f}-{la:.2f}")
    print(f"  MODEL totals: G O1.5={mb['G_O1.5']:.0%}  O2.5={mb['G_O2.5']:.0%}  O3.5={mb['G_O3.5']:.0%}"
          f"   BTTS={mb['BTTS']:.0%}")
    print(f"  MODEL team:  {home} O0.5={mb['H_O0.5']:.0%} O1.5={mb['H_O1.5']:.0%}"
          f"   {away} O0.5={mb['A_O0.5']:.0%} O1.5={mb['A_O1.5']:.0%}")
    print(f"  MODEL 1st-to-score: {home}={mb['FTS_home']:.0%}  {away}={mb['FTS_away']:.0%}  none={mb['FTS_none']:.0%}")

    res = matches.get((home, away, date))
    if not res:
        print("  [no Polymarket match resolved]\n")
        continue
    print(f"  POLYMARKET (vol ${res['volume']/1e6:.1f}M) markets:")
    # main event 1X2 markets
    main = by_slug.get(res["slug"])
    if main:
        for m in main.get("markets", []):
            q = m.get("groupItemTitle") or m.get("question") or "?"
            print(f"    [1X2] {q}: outcomes={m.get('outcomes')} prices={m.get('outcomePrices')}")
    more = by_slug.get(res["slug"] + "-more-markets")
    if more:
        for m in more.get("markets", []):
            q = m.get("question") or m.get("groupItemTitle") or "?"
            print(f"    [more] {q}: outcomes={m.get('outcomes')} prices={m.get('outcomePrices')}")
    else:
        print("    [no more-markets bundle found]")
    print()

"""Live (in-play) fair-value table from the model.

Re-runs the double-Poisson conditional on a game state (current score + minute):
remaining goals ~ Poisson(lambda * time_left/90), final = current + remaining.
Gives the model's updated win/draw/lose so we can spot when the LIVE market
over-reacts (e.g. a strong favourite over-drops after conceding early).

Baseline (constant scoring rate). Ignores game-state effects (a leading team
parking the bus, red cards, fatigue) — a fair-value anchor, not gospel.
"""
import sys
sys.path.insert(0, "src")
import numpy as np
from scipy.stats import poisson
from footpred import model

idata = model.load_trace()
teams = list(idata.attrs.get("teams", []))
post = idata.posterior


def flat(v):
    return post[v].stack(s=("chain", "draw")).transpose("s", ...).values


intercept, home_adv, atk, deff = flat("intercept"), flat("home_adv"), flat("def".replace("def", "atk")), flat("def")
# (atk loaded explicitly below to avoid the reserved word shuffle)
atk = flat("atk")
tid = {t: i for i, t in enumerate(teams)}


def lams(home, away, neutral=True):
    h, a = tid[home], tid[away]
    ha = 0.0 if neutral else 1.0
    lh = float(np.exp(intercept + home_adv * ha + atk[:, h] - deff[:, a]).mean())
    la = float(np.exp(intercept + atk[:, a] - deff[:, h]).mean())
    return lh, la


def live(lh, la, hs, as_, minute, K=14):
    f = max(0.0, (90.0 - minute) / 90.0)
    ph = poisson.pmf(np.arange(K), lh * f)
    pa = poisson.pmf(np.arange(K), la * f)
    g = np.outer(ph, pa)
    i = np.arange(K)
    H = i[:, None] + hs
    A = i[None, :] + as_
    return float(g[H > A].sum()), float(g[H == A].sum()), float(g[H < A].sum())


GAMES = [
    ("Jordan", "Argentina", "away", "Argentina"),
    ("Panama", "England", "away", "England"),
    ("Croatia", "Ghana", "home", "Croatia"),
    ("Colombia", "Portugal", "away", "Portugal"),
]

for home, away, fav, favname in GAMES:
    lh, la = lams(home, away)
    fav_home = fav == "home"

    def favprob(hs, as_, minute):
        pH, pD, pA = live(lh, la, hs, as_, minute)
        return (pH if fav_home else pA), pD, (pA if fav_home else pH)

    print(f"\n=== {home} v {away} ===  ({favname} favourite)  proj {lh:.2f}-{la:.2f}")
    fw, dr, dg = favprob(0, 0, 0)
    print(f"  pregame 0-0          : {favname} {fw:.0%} | draw {dr:.0%} | underdog {dg:.0%}")
    for mnt in (10, 20, 30, 45):
        if fav_home:
            fw, dr, dg = favprob(0, 1, mnt)
        else:
            fw, dr, dg = favprob(1, 0, mnt)
        print(f"  {favname} 0-1 DOWN @ {mnt:>2}'   : {favname} {fw:.0%} | draw {dr:.0%} | underdog {dg:.0%}")
    for mnt in (60, 75):
        fw, dr, dg = favprob(0, 0, mnt)
        print(f"  still 0-0 @ {mnt}'       : {favname} {fw:.0%} | draw {dr:.0%} | underdog {dg:.0%}")

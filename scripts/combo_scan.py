"""Spreads + same-game-combo scan for the June 27 slate.

Single-market edges were already nil. This checks two things the prior scan
didn't: (1) handicap/spread markets, and (2) correlated same-game combos, where
the model's JOINT (from the scoreline grid) is compared to the market's product
of marginals — the condition for a correlation edge if a venue prices legs
independently (model_joint > market_product => underpriced combo).
"""
import sys
sys.path.insert(0, "src")
import numpy as np
from footpred import model, predict as predmod

idata = model.load_trace()

# market marginals pulled from edge_scan.py output (Polymarket, raw outcomePrices)
GAMES = {
    "Panama v England": dict(home="Panama", away="England", fav="away",
        hw=.055, dr=.105, aw=.845, o15=.855, o25=.665, o35=.445, btts=.425,
        fav_m15=.625, fav_m25=.405, fav_t2=.78),
    "Croatia v Ghana": dict(home="Croatia", away="Ghana", fav="home",
        hw=.545, dr=.295, aw=.165, o15=.675, o25=.405, o35=.205, btts=.445,
        fav_m15=.285, fav_m25=.115, fav_t2=.465),
    "Colombia v Portugal": dict(home="Colombia", away="Portugal", fav="away",
        hw=.235, dr=.245, aw=.515, o15=.735, o25=.495, o35=.275, btts=.52,
        fav_m15=.265, fav_m25=.105, fav_t2=.485),
    "DR Congo v Uzbekistan": dict(home="DR Congo", away="Uzbekistan", fav="home",
        hw=.555, dr=.235, aw=.215, o15=.735, o25=.475, o35=.255, btts=.49,
        fav_m15=.285, fav_m25=.115, fav_t2=.495),
    "Algeria v Austria": dict(home="Algeria", away="Austria", fav="away",
        hw=.235, dr=.445, aw=.335, o15=.59, o25=.305, o35=.145, btts=.445,
        fav_m15=.335, fav_m25=.105, fav_t2=.27),
    "Jordan v Argentina": dict(home="Jordan", away="Argentina", fav="away",
        hw=.053, dr=.105, aw=.835, o15=.82, o25=.615, o35=.385, btts=.37,
        fav_m15=.615, fav_m25=.38, fav_t2=.745),
}


def pc(x):
    return f"{x:+.0%}"


for name, m in GAMES.items():
    pred = predmod.predict(idata, m["home"], m["away"], neutral=True)
    g = pred.grid
    G = g.shape[0]
    i = np.arange(G)
    H = i[:, None]
    A = i[None, :]
    T = H + A
    P = lambda mask: float(g[mask].sum())

    fav_home = m["fav"] == "home"
    fav_win = (H > A) if fav_home else (A > H)
    fav_margin = (H - A) if fav_home else (A - H)
    fav_goals = H if fav_home else A
    o15, o25 = T >= 2, T >= 3
    btts = (H >= 1) & (A >= 1)
    bn = ~btts
    favname = m["home"] if fav_home else m["away"]

    # model spread + combos
    sp15 = P(fav_margin >= 2)
    sp25 = P(fav_margin >= 3)
    favwin_p = m["aw"] if not fav_home else m["hw"]

    print(f"\n=== {name} ===  proj {pred.exp_home_goals:.2f}-{pred.exp_away_goals:.2f}"
          f"   ({favname} fav)")
    print(f"  SPREAD {favname} -1.5: model {sp15:.0%}  market {m['fav_m15']:.0%}  edge {pc(sp15-m['fav_m15'])}")
    print(f"  SPREAD {favname} -2.5: model {sp25:.0%}  market {m['fav_m25']:.0%}  edge {pc(sp25-m['fav_m25'])}")

    combos = [
        (f"{favname} win & Over 1.5", P(fav_win & o15), favwin_p * m["o15"]),
        (f"{favname} win & Over 2.5", P(fav_win & o25), favwin_p * m["o25"]),
        (f"{favname} win & {favname} 2+ goals", P(fav_win & (fav_goals >= 2)), favwin_p * m["fav_t2"]),
        (f"{favname} win & BTTS-No", P(fav_win & bn), favwin_p * (1 - m["btts"])),
        ("Over 1.5 & BTTS-No", P(o15 & bn), m["o15"] * (1 - m["btts"])),
    ]
    for label, mj, prod in combos:
        flag = "  <== model>product" if mj - prod > 0.03 else ""
        print(f"    {label}: model {mj:.0%}  vs indep-product {prod:.0%}  edge {pc(mj-prod)}{flag}")

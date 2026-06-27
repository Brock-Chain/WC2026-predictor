"""Round-of-32 model predictions for locked matchups.

Knockout adaptation: there is no advancing 'draw', so
  P(advance) = P(win in 90) + P(draw in 90) * P(win the ET+penalties | level).
ET modelled as 30 more minutes of Poisson at 1/3 the match rate from level,
then 50/50 penalties if still level. Host nations (USA/Mexico) get home adv.
"""
import sys
sys.path.insert(0, "src")
import numpy as np
from scipy.stats import poisson
from footpred import model, predict as predmod

idata = model.load_trace()
teams = set(idata.attrs.get("teams", []))
HOSTS = {"United States", "Mexico", "Canada"}

# locked R32 matchups (home listed first per bracket)
LOCKED = [
    ("South Africa", "Canada", "Jun 28"),
    ("Germany", "Paraguay", "Jun 29"),
    ("Netherlands", "Morocco", "Jun 29"),
    ("Brazil", "Japan", "Jun 29"),
    ("France", "Sweden", "Jun 30"),
    ("Ivory Coast", "Norway", "Jun 30"),
    ("Mexico", "Ecuador", "Jun 30"),
    ("United States", "Bosnia and Herzegovina", "Jul 1"),
    ("Argentina", "Cape Verde", "Jul 3"),
    ("Australia", "Egypt", "Jul 3"),
]


def advance(grid, lh, la):
    G = grid.shape[0]
    i = np.arange(G)
    H, A = i[:, None], i[None, :]
    p_h90 = float(grid[H > A].sum())
    p_d90 = float(grid[H == A].sum())
    p_a90 = float(grid[H < A].sum())
    # extra time: 30 min at 1/3 rate from level, then pens
    f = 30.0 / 90.0
    K = 10
    ph = poisson.pmf(np.arange(K), lh * f)
    pa = poisson.pmf(np.arange(K), la * f)
    et = np.outer(ph, pa)
    ii = np.arange(K)
    p_h_et = float(et[ii[:, None] > ii[None, :]].sum())
    p_a_et = float(et[ii[:, None] < ii[None, :]].sum())
    p_lvl = float(et[ii[:, None] == ii[None, :]].sum())
    h_given_draw = p_h_et + p_lvl * 0.5
    a_given_draw = p_a_et + p_lvl * 0.5
    return p_h90, p_d90, p_a90, p_h90 + p_d90 * h_given_draw, p_a90 + p_d90 * a_given_draw


print("Round of 32 — locked matchups (model)\n")
for home, away, date in LOCKED:
    miss = [t for t in (home, away) if t not in teams]
    if miss:
        print(f"=== {home} v {away} ({date}) ===  SKIP — unknown team(s): {miss}\n")
        continue
    neutral = home not in HOSTS
    pred = predmod.predict(idata, home, away, neutral=neutral)
    g = pred.grid
    lh, la = pred.exp_home_goals, pred.exp_away_goals
    Gn = g.shape[0]
    i = np.arange(Gn)
    o25 = float(g[(i[:, None] + i[None, :]) >= 3].sum())
    btts = float(g[1:, 1:].sum())
    h90, d90, a90, hadv, aadv = advance(g, lh, la)
    tag = "" if neutral else "  [host home adv]"
    print(f"=== {home} v {away} ({date}){tag} ===  proj {lh:.2f}-{la:.2f}")
    print(f"  90-min:  {home} {h90:.0%} | draw {d90:.0%} | {away} {a90:.0%}   (O2.5 {o25:.0%}, BTTS {btts:.0%})")
    print(f"  ADVANCE: {home} {hadv:.0%}  |  {away} {aadv:.0%}\n")

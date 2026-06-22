"""Monte-Carlo group-stage simulation for the WC2026 forecast.

Replaces a backward-looking standings table with a forward-looking one: how
likely is each team to *advance*? We fix already-played results, then play out
every remaining group match by sampling whole scorelines from that fixture's
posterior-predictive grid (the same grid the heatmap shows). Repeating this
thousands of times yields, per team:

- ``p_win``      — probability of winning the group,
- ``p_top2``     — probability of finishing top two,
- ``p_advance``  — probability of reaching the Round of 32 under the actual
  48-team format: the top two of each group **plus the eight best
  third-placed teams across all groups** (so the groups are simulated
  *jointly*, not independently, to rank the third-placed teams correctly).

Tiebreakers use points, then goal difference, then goals for (a faithful-enough
proxy for FIFA's full tiebreak ladder), with a tiny random jitter to split
exact ties fairly.
"""
from __future__ import annotations

import numpy as np

# FIFA-style ranking key: points dominate, then GD, then GF. Scales are chosen
# so each criterion strictly outranks the next given realistic group totals.
_PTS, _GD, _GF = 1e6, 1e3, 1.0
N_ADVANCE_THIRDS = 8          # best third-placed teams that also advance


def _sample_scorelines(grid: np.ndarray, rng: np.random.Generator, n: int):
    """Sample ``n`` (home_goals, away_goals) pairs from a scoreline grid."""
    g = grid.shape[0]
    flat = grid.ravel().astype(float)
    flat /= flat.sum()
    idx = rng.choice(g * g, size=n, p=flat)
    return idx // g, idx % g


def _collect_groups(preds):
    """group letter -> dict(teams, played[list], upcoming[list])."""
    groups: dict[str, dict] = {}
    for r, p in preds:
        g = getattr(r, "group", "")
        if not g:
            continue
        d = groups.setdefault(g, {"teams": set(), "played": [], "upcoming": []})
        d["teams"].update((r.home_team, r.away_team))
        if getattr(r, "played", False):
            d["played"].append(
                (r.home_team, r.away_team, int(r.home_score), int(r.away_score))
            )
        else:
            # p is None only if a team is unseen; carry it so we can bail safely.
            d["upcoming"].append((r.home_team, r.away_team, None if p is None else p.grid))
    return groups


def simulate_advancement(preds, n_sims: int = 20000, seed: int = 0) -> dict:
    """Return ``group -> {team -> {p_win, p_top2, p_advance, pts}}``.

    A group is returned as ``None`` if it cannot be simulated (an upcoming match
    involves a team with no prediction).
    """
    rng = np.random.default_rng(seed)
    groups = _collect_groups(preds)
    gkeys = sorted(groups)

    sim: dict[str, dict] = {}     # per-group intermediate arrays
    third_clean = []              # [n_sims] clean key of each group's 3rd team
    third_owner_groups = []       # parallel list of group letters (jointly sim'd)

    for g in gkeys:
        d = groups[g]
        teams = sorted(d["teams"])
        tix = {t: i for i, t in enumerate(teams)}
        T = len(teams)

        pts = np.zeros((n_sims, T))
        gd = np.zeros((n_sims, T))
        gf = np.zeros((n_sims, T))

        base_pts = np.zeros(T)
        for h, a, hg, ag in d["played"]:
            hi, ai = tix[h], tix[a]
            _apply_played(base_pts, gd, gf, hi, ai, hg, ag)
        pts += base_pts

        bad = False
        for h, a, grid in d["upcoming"]:
            if grid is None:
                bad = True
                break
            hg, ag = _sample_scorelines(grid, rng, n_sims)
            hi, ai = tix[h], tix[a]
            hw, dr, aw = hg > ag, hg == ag, hg < ag
            pts[hw, hi] += 3
            pts[aw, ai] += 3
            pts[dr, hi] += 1
            pts[dr, ai] += 1
            diff = (hg - ag).astype(float)
            gd[:, hi] += diff
            gd[:, ai] -= diff
            gf[:, hi] += hg
            gf[:, ai] += ag
        if bad:
            sim[g] = None
            continue

        clean = pts * _PTS + gd * _GD + gf * _GF
        key = clean + rng.random((n_sims, T)) * 1e-2     # jitter for fair ties
        order = np.argsort(-key, axis=1)                 # [n_sims, T]
        rows = np.arange(n_sims)
        third_idx = order[:, 2]
        sim[g] = {
            "teams": teams,
            "order": order,
            "pts": base_pts,
            "T": T,
        }
        # clean key of the third-placed team, for cross-group comparison.
        third_clean.append(clean[rows, third_idx] + rng.random(n_sims) * 1e-2)
        third_owner_groups.append(g)

    # Rank third-placed teams across all (simulable) groups; best 8 advance.
    valid = [g for g in gkeys if sim.get(g) is not None]
    third_qual = {}
    if valid:
        tk = np.stack(third_clean, axis=1)               # [n_sims, n_valid]
        n_valid = tk.shape[1]
        k = min(N_ADVANCE_THIRDS, n_valid)
        # columns of the k largest thirds per sim -> qualifying mask.
        top = np.argpartition(-tk, kth=k - 1, axis=1)[:, :k]
        qual_mask = np.zeros_like(tk, dtype=bool)
        np.put_along_axis(qual_mask, top, True, axis=1)
        for col, g in enumerate(third_owner_groups):
            third_qual[g] = qual_mask[:, col]

    out: dict[str, dict | None] = {}
    for g in gkeys:
        s = sim.get(g)
        if s is None:
            out[g] = None
            continue
        order, T, teams = s["order"], s["T"], s["teams"]
        winner, second, third = order[:, 0], order[:, 1], order[:, 2]
        tq = third_qual[g]
        res = {}
        for i, team in enumerate(teams):
            p_win = float(np.mean(winner == i))
            p_top2 = float(np.mean((winner == i) | (second == i)))
            p_adv = p_top2 + float(np.mean((third == i) & tq))
            res[team] = {
                "p_win": p_win,
                "p_top2": p_top2,
                "p_advance": p_adv,
                "pts": float(s["pts"][i]),
            }
        out[g] = res
    return out


def _apply_played(pts, gd, gf, hi, ai, hg, ag):
    gd[:, hi] += hg - ag
    gd[:, ai] += ag - hg
    gf[:, hi] += hg
    gf[:, ai] += ag
    if hg > ag:
        pts[hi] += 3
    elif hg < ag:
        pts[ai] += 3
    else:
        pts[hi] += 1
        pts[ai] += 1

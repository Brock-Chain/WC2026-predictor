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


# --- full-tournament simulation (title odds) -------------------------------
# WC2026 knockout bracket (verified). Slots: ('1',X) group winner, ('2',X)
# runner-up, ('3',k) the k-th best-third-placed team (k in 0..7, assigned to the
# eight winner-vs-third slots in group-letter order — a documented simplification
# of FIFA's 495-row Annex-C table that barely affects title odds).
_R32 = [
    (("2", "A"), ("2", "B")),   # M1
    (("1", "E"), ("3", 0)),     # M2
    (("1", "F"), ("2", "C")),   # M3
    (("1", "C"), ("2", "F")),   # M4
    (("1", "I"), ("3", 1)),     # M5
    (("2", "E"), ("2", "I")),   # M6
    (("1", "A"), ("3", 2)),     # M7
    (("1", "L"), ("3", 3)),     # M8
    (("1", "D"), ("3", 4)),     # M9
    (("1", "G"), ("3", 5)),     # M10
    (("2", "K"), ("2", "L")),   # M11
    (("1", "H"), ("2", "J")),   # M12
    (("1", "B"), ("3", 6)),     # M13
    (("1", "J"), ("2", "H")),   # M14
    (("1", "K"), ("3", 7)),     # M15
    (("2", "D"), ("2", "G")),   # M16
]
_R16 = [(1, 4), (0, 2), (3, 5), (6, 7), (10, 11), (8, 9), (13, 15), (12, 14)]
_QF = [(0, 1), (4, 5), (2, 3), (6, 7)]
_SF = [(0, 1), (2, 3)]
N_QUAL_THIRDS = 8


def simulate_tournament(preds, adv_prob, wc_teams, n_sims: int = 20000, seed: int = 1):
    """Full-tournament Monte-Carlo -> per-team round-reach + title probabilities.

    Simulates the group stage (sampling remaining matches from each fixture's
    posterior grid, fixing played results), determines the 32 qualifiers (top 2
    + 8 best thirds), fills the verified bracket, and plays every knockout tie
    with ``adv_prob`` — the pre-computed P(team i beats team j) in a neutral
    knockout (regulation win-prob plus a coin-flip on draws, i.e. the shootout).

    ``adv_prob`` is an NxN matrix indexed by ``wc_teams`` order. Returns
    ``team -> {p_r32, p_r16, p_qf, p_sf, p_final, p_champion}`` or ``None`` if a
    group can't be simulated.
    """
    rng = np.random.default_rng(seed)
    tidx = {t: i for i, t in enumerate(wc_teams)}
    N = len(wc_teams)
    groups = _collect_groups(preds)
    gletters = sorted(groups)
    gli = {g: i for i, g in enumerate(gletters)}
    ng = len(gletters)

    winner_g = np.full((n_sims, ng), -1, dtype=int)
    runner_g = np.full((n_sims, ng), -1, dtype=int)
    third_g = np.full((n_sims, ng), -1, dtype=int)
    third_key = np.full((n_sims, ng), -1e18)

    for g in gletters:
        d = groups[g]
        teams = sorted(d["teams"])
        T = len(teams)
        loc = {t: i for i, t in enumerate(teams)}
        pts = np.zeros((n_sims, T)); gd = np.zeros((n_sims, T)); gf = np.zeros((n_sims, T))
        base = np.zeros(T)
        for h, a, hg, ag in d["played"]:
            _apply_played(base, gd, gf, loc[h], loc[a], hg, ag)
        pts += base
        for h, a, grid in d["upcoming"]:
            if grid is None:
                return None
            hg, ag = _sample_scorelines(grid, rng, n_sims)
            hi, ai = loc[h], loc[a]
            hw, dr, aw = hg > ag, hg == ag, hg < ag
            pts[hw, hi] += 3; pts[aw, ai] += 3; pts[dr, hi] += 1; pts[dr, ai] += 1
            diff = (hg - ag).astype(float)
            gd[:, hi] += diff; gd[:, ai] -= diff
            gf[:, hi] += hg; gf[:, ai] += ag
        clean = pts * _PTS + gd * _GD + gf * _GF
        key = clean + rng.random((n_sims, T)) * 1e-2
        order = np.argsort(-key, axis=1)
        gteam = np.array([tidx[t] for t in teams])
        gi = gli[g]
        rows = np.arange(n_sims)
        winner_g[:, gi] = gteam[order[:, 0]]
        runner_g[:, gi] = gteam[order[:, 1]]
        third_g[:, gi] = gteam[order[:, 2]]
        third_key[:, gi] = clean[rows, order[:, 2]] + rng.random(n_sims) * 1e-2

    # Best-8 thirds qualify; assign them to the 8 third-slots in group-letter order.
    top_groups = np.argsort(-third_key, axis=1)[:, :N_QUAL_THIRDS]
    qual_mask = np.zeros((n_sims, ng), dtype=bool)
    np.put_along_axis(qual_mask, top_groups, True, axis=1)
    rank = np.where(qual_mask, np.arange(ng)[None, :], 1000 + np.arange(ng)[None, :])
    qual_sorted = np.argsort(rank, axis=1)[:, :N_QUAL_THIRDS]   # group idx, letter order
    rows = np.arange(n_sims)
    third_slot = np.stack(
        [third_g[rows, qual_sorted[:, s]] for s in range(N_QUAL_THIRDS)], axis=1
    )  # [n_sims, 8] global team idx per third-slot

    def resolve(slot):
        kind, val = slot
        if kind == "1":
            return winner_g[:, gli[val]]
        if kind == "2":
            return runner_g[:, gli[val]]
        return third_slot[:, val]

    def play(top, bottom):
        p = adv_prob[top, bottom]
        return np.where(rng.random(n_sims) < p, top, bottom)

    r32w = [play(resolve(t), resolve(b)) for t, b in _R32]
    r16w = [play(r32w[a], r32w[b]) for a, b in _R16]
    qfw = [play(r16w[a], r16w[b]) for a, b in _QF]
    sfw = [play(qfw[a], qfw[b]) for a, b in _SF]
    champ = play(sfw[0], sfw[1])

    def reach(arrays):
        cnt = np.bincount(np.concatenate(arrays), minlength=N)
        return cnt / n_sims

    occupants = (
        [winner_g[:, g] for g in range(ng)]
        + [runner_g[:, g] for g in range(ng)]
        + [third_slot[:, k] for k in range(N_QUAL_THIRDS)]
    )
    p_r32 = reach(occupants)
    p_r16 = reach(r32w)
    p_qf = reach(r16w)
    p_sf = reach(qfw)
    p_final = reach(sfw)
    p_champ = np.bincount(champ, minlength=N) / n_sims

    return {
        wc_teams[i]: {
            "p_r32": float(p_r32[i]), "p_r16": float(p_r16[i]),
            "p_qf": float(p_qf[i]), "p_sf": float(p_sf[i]),
            "p_final": float(p_final[i]), "p_champion": float(p_champ[i]),
        }
        for i in range(N)
    }


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

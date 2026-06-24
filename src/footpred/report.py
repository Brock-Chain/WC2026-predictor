"""Phase 6 deliverable: a premium, self-contained HTML report with predictions
for every WC2026 fixture.

Design goals (redesign pass):
- A **hero** with credibility tiles (accuracy, RPS vs Elo, calibration) and
  standout callouts (most-confident pick, brewing upset, goal-fest).
- The signature output — the **scoreline probability heatmap** — rendered per
  match (not just text chips), with the modal scoreline headlined.
- A clear split between **validated results** (played) and **forward-looking
  predictions** (upcoming).
- Sticky group navigation + per-group **chance-to-advance** forecast (each
  team's simulated probability of reaching the knockouts), replacing a
  backward-looking standings table.
- Flags, confidence chips, polish, and lightweight vanilla-JS interactivity
  (filter played/upcoming, collapse groups, hover tooltips).

One ``.html`` file, inline CSS+JS, no external assets.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .flags_svg import flag_svg
from .predict import Prediction, predict
from .simulate import (
    _QF, _R16, _R32, _SF,
    simulate_advancement,
    simulate_tournament,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = PROJECT_ROOT / "wc2026_predictions.html"

# Host nations (2026: USA, Canada, Mexico) play at home — not neutral.
HOSTS = {"United States", "Canada", "Mexico"}

# Default headline metrics (from our temporal backtest); override via render_report.
DEFAULT_METRICS = {
    "bayes_rps": 0.166,
    "elo_rps": 0.182,
    "naive_rps": 0.228,
    "calibration": "well-calibrated",
}

# Flag emoji for the WC2026 field. Scotland/England use subdivision flags.
FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "Czech Republic": "🇨🇿",
    "South Korea": "🇰🇷", "Canada": "🇨🇦", "Bosnia and Herzegovina": "🇧🇦",
    "Qatar": "🇶🇦", "Switzerland": "🇨🇭", "Brazil": "🇧🇷", "Morocco": "🇲🇦",
    "Scotland": "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "Haiti": "🇭🇹", "United States": "🇺🇸", "Paraguay": "🇵🇾",
    "Australia": "🇦🇺", "Turkey": "🇹🇷", "Germany": "🇩🇪", "Curaçao": "🇨🇼",
    "Ivory Coast": "🇨🇮", "Ecuador": "🇪🇨", "Netherlands": "🇳🇱", "Japan": "🇯🇵",
    "Sweden": "🇸🇪", "Tunisia": "🇹🇳", "Belgium": "🇧🇪", "Egypt": "🇪🇬",
    "Iran": "🇮🇷", "New Zealand": "🇳🇿", "Spain": "🇪🇸", "Cape Verde": "🇨🇻",
    "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾", "France": "🇫🇷", "Senegal": "🇸🇳",
    "Norway": "🇳🇴", "Iraq": "🇮🇶", "Argentina": "🇦🇷", "Algeria": "🇩🇿",
    "Austria": "🇦🇹", "Jordan": "🇯🇴", "Portugal": "🇵🇹", "DR Congo": "🇨🇩",
    "Colombia": "🇨🇴", "Uzbekistan": "🇺🇿",
    "England": "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "Croatia": "🇭🇷", "Ghana": "🇬🇭", "Panama": "🇵🇦",
}

# Cap the heatmap at 0..N goals (tail beyond is negligible).
HEAT_N = 6


def _flag(team: str) -> str:
    """Inline circular SVG flag (renders identically on every OS, unlike emoji
    flags which degrade to letter-pairs on Windows). Sized via the .flag CSS."""
    svg = flag_svg(team)
    return f"<span class='flag'>{svg}</span>" if svg else ""


def _result_label(p: Prediction) -> str:
    probs = [("home", p.p_home_win), ("draw", p.p_draw), ("away", p.p_away_win)]
    return max(probs, key=lambda x: x[1])[0]


def _actual_label(hg: int, ag: int) -> str:
    return "home" if hg > ag else ("draw" if hg == ag else "away")


def _confidence(p: Prediction):
    """(label, css-class) from how strong the top 1X2 outcome is."""
    top = max(p.p_home_win, p.p_draw, p.p_away_win)
    if top >= 0.60:
        return "Strong", "c-strong"
    if top >= 0.45:
        return "Lean", "c-lean"
    return "Open", "c-open"


def build_predictions(idata, fixtures: pd.DataFrame, teams: list[str]):
    """Return a list of (fixture_row, Prediction|None). None if a team is
    unseen in the training window."""
    out = []
    known = set(teams)
    for r in fixtures.itertuples():
        if r.home_team not in known or r.away_team not in known:
            out.append((r, None))
            continue
        neutral = not (r.home_team in HOSTS or r.away_team in HOSTS)
        pred = predict(idata, r.home_team, r.away_team,
                       neutral=neutral, teams=teams)
        out.append((r, pred))
    return out


# --- HTML fragments --------------------------------------------------------

def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _goal_breakdown(pred: Prediction):
    """Derive richer goal markets from the scoreline grid: both-teams-to-score
    and over 1.5 / 2.5 / 3.5, plus a short qualitative tone."""
    g = pred.grid
    n = g.shape[0]
    totals = np.add.outer(np.arange(n), np.arange(n))
    btts = float(g[1:, 1:].sum())
    o15 = float(g[totals >= 2].sum())
    o25 = float(g[totals >= 3].sum())
    o35 = float(g[totals >= 4].sum())
    exp_total = pred.exp_home_goals + pred.exp_away_goals
    if exp_total >= 2.9:
        tone = "open, high-scoring"
    elif exp_total <= 1.9:
        tone = "tight, low-scoring"
    else:
        tone = "balanced"
    return dict(btts=btts, o15=o15, o25=o25, o35=o35, tone=tone)


def _bar_html(p: Prediction) -> str:
    segs = [("h", p.p_home_win, "Home win"), ("d", p.p_draw, "Draw"),
            ("a", p.p_away_win, "Away win")]
    parts = []
    for cls, val, lab in segs:
        label = _pct(val) if val >= 0.12 else ""
        parts.append(
            f"<div class='seg {cls}' style='width:{val*100:.2f}%' "
            f"title='{lab}: {_pct(val)}'>{label}</div>"
        )
    return f"<div class='bar'>{''.join(parts)}</div>"


def _heatmap_html(p: Prediction, actual: tuple[int, int] | None = None) -> str:
    """A color-graded scoreline grid rendered as an inline SVG.
    Rows = home goals 0..n, columns = away goals 0..n.
    One <rect> per cell replaces the old div-grid (~49 divs → 1 SVG + n² rects).
    """
    g = p.grid
    n = min(HEAT_N, p.max_goals)
    sub = g[: n + 1, : n + 1]
    vmax = float(sub.max()) or 1.0
    mi, mj, _ = p.top_scorelines(1)[0]

    # Layout constants (SVG user-units; viewBox = "0 0 W H")
    MARGIN_L = 16   # left margin for row-axis labels
    MARGIN_T = 14   # top margin for col-axis labels
    GAP = 1         # gap between cells
    CELL = 18       # cell size
    NCOLS = n + 1   # columns: away goals 0..n
    NROWS = n + 1   # rows: home goals 0..n

    W = MARGIN_L + NCOLS * CELL + (NCOLS - 1) * GAP
    H = MARGIN_T + NROWS * CELL + (NROWS - 1) * GAP

    parts: list[str] = [f"<svg class='hm' viewBox='0 0 {W} {H}' "
                        f"xmlns='http://www.w3.org/2000/svg'>"]

    # Corner label "H\A"
    parts.append(
        f"<text x='0' y='{MARGIN_T - 3}' class='hm-lbl hm-corner-lbl'"
        f" font-size='8.5'>H\\A</text>"
    )

    # Away-axis column headers (0..n)
    for j in range(NCOLS):
        cx = MARGIN_L + j * (CELL + GAP) + CELL // 2
        parts.append(
            f"<text x='{cx}' y='{MARGIN_T - 3}' class='hm-lbl'"
            f" text-anchor='middle' font-size='9.5'>{j}</text>"
        )

    # Home-axis row headers (0..n) + cell rects
    for i in range(NROWS):
        ry = MARGIN_T + i * (CELL + GAP)
        cy_label = ry + CELL // 2 + 3   # +3 = rough visual baseline offset
        parts.append(
            f"<text x='{MARGIN_L - 3}' y='{cy_label}' class='hm-lbl'"
            f" text-anchor='end' font-size='9.5'>{i}</text>"
        )
        for j in range(NCOLS):
            v = float(g[i, j])
            alpha = (v / vmax) ** 0.6   # gamma for visible low-prob cells
            fill_opacity = 0.04 + alpha * 0.96
            rx_val = MARGIN_L + j * (CELL + GAP)

            stroke_attr = ""
            if i == mi and j == mj:
                stroke_attr += " stroke='#bfe3ff' stroke-width='1.5'"
            if actual is not None and (i, j) == actual:
                # green ring overrides the mode outline when they coincide
                stroke_attr = " stroke='#34d399' stroke-width='1.5'"

            parts.append(
                f"<rect x='{rx_val}' y='{ry}' width='{CELL}' height='{CELL}'"
                f" rx='3' fill='#60a5fa' fill-opacity='{fill_opacity:.3f}'"
                f"{stroke_attr}"
                f" data-s='{i}&#8211;{j}' data-p='{_pct(v)}'>"
                f"<title>{i}–{j}: {_pct(v)}</title>"
                f"</rect>"
            )

    parts.append("</svg>")
    return "".join(parts)


def _match_card(row, pred: Prediction | None) -> str:
    hf, af = _flag(row.home_team), _flag(row.away_team)
    home = f"{hf} {html.escape(row.home_team)}".strip()
    away = f"{html.escape(row.away_team)} {af}".strip()
    date = pd.Timestamp(row.date).strftime("%b %d") if pd.notna(row.date) else ""
    t = str(getattr(row, "time_et", "") or "").strip()
    meta = f"{date} &middot; {t} ET" if t else date
    played = bool(getattr(row, "played", False))

    if pred is None:
        return (f"<div class='match skip' data-state='skip'>"
                f"<div class='m-top'><span class='teams'>{home} "
                f"<span class='vs'>v</span> {away}</span>"
                f"<span class='meta'>{meta}</span></div>"
                f"<div class='skip-note'>No prediction — a team has "
                f"insufficient recent data (unseen in the 2018+ window).</div>"
                f"</div>")

    mi, mj, mp = pred.top_scorelines(1)[0]
    conf_lbl, conf_cls = _confidence(pred)
    fav = _result_label(pred)
    state = "played" if played else "upcoming"
    actual = (int(row.home_score), int(row.away_score)) if played else None
    teams_attr = f"{row.home_team} {row.away_team}".lower()

    # The "draw paradox": the single most-likely score is a tie, yet the summed
    # 1X2 mass favours one side. Flag it with an explained info marker.
    paradox = ""
    if mi == mj and fav != "draw":
        fav_team = row.home_team if fav == "home" else row.away_team
        fav_p = pred.p_home_win if fav == "home" else pred.p_away_win
        paradox = (
            f"<span class='info' tabindex='0' title='The single most likely "
            f"exact score is a {mi}&#8211;{mj} draw, but adding up every winning "
            f"scoreline, {html.escape(fav_team)} is favoured at {_pct(fav_p)}.'>"
            f"&#9432;</span>"
        )

    # Headline: predicted modal scoreline, or actual result if played.
    if played:
        hg, ag = actual
        ok = _actual_label(hg, ag) == _result_label(pred)
        badge = ("<span class='ok'>&#10003; called it</span>" if ok
                 else "<span class='miss'>&#10007; missed</span>")
        headline = (f"<div class='headline'><span class='score'>{hg}&#8211;{ag}</span>"
                    f"<span class='hl-sub'>final &middot; predicted {mi}&#8211;{mj} "
                    f"&middot; {badge}</span></div>")
    else:
        headline = (f"<div class='headline'><span class='score pred'>{mi}&#8211;{mj}"
                    f"</span>{paradox}<span class='hl-sub'>most likely &middot; {_pct(mp)} "
                    f"&middot; <span class='chip {conf_cls}'>{conf_lbl}</span></span></div>")

    gb = _goal_breakdown(pred)
    stats = (
        f"<div class='row'>"
        f"<span title='Model-projected goals (Poisson mean), not shot-based xG'>"
        f"Proj. <b>{pred.exp_home_goals:.2f}&#8211;{pred.exp_away_goals:.2f}</b></span>"
        f"<span class='tone'>{gb['tone']}</span>"
        f"<span class='venue' title='Neutral venue = no home advantage applied'>"
        f"{'Neutral' if pred.neutral else 'Host (home)'}</span>"
        f"</div>"
        f"<div class='goals' title='Derived from the full scoreline grid'>"
        f"<span>O1.5 <b>{_pct(gb['o15'])}</b></span>"
        f"<span>O2.5 <b>{_pct(gb['o25'])}</b></span>"
        f"<span>O3.5 <b>{_pct(gb['o35'])}</b></span>"
        f"<span title='Both teams to score'>BTTS <b>{_pct(gb['btts'])}</b></span>"
        f"</div>"
    )

    # Per-card "Model vs Market" expander (upcoming only). Emitted hidden; the
    # market JS reveals + fills it only when window.POLY has a matching entry,
    # using the SAME live fetch (or baked snapshot) as the Model-vs-Market tab.
    expander = ""
    if not played:
        expander = (
            "<div class='mvm' hidden>"
            "<button class='mvm-toggle' onclick='toggleExpander(this)'>"
            "Model vs Market <span class='mvm-caret'>&#9662;</span></button>"
            "<div class='mvm-body'><div class='mvm-rows'></div>"
            "<div class='mvm-note'></div></div></div>"
        )

    return (
        f"<div class='match' data-state='{state}' data-teams='{html.escape(teams_attr)}'>"
        f"<div class='m-top'><span class='teams'>{home} "
        f"<span class='vs'>v</span> {away}</span>"
        f"<span class='meta'>{meta}</span></div>"
        f"{_bar_html(pred)}"
        f"<div class='m-body'>"
        f"<div class='m-left'>{headline}{stats}</div>"
        f"<div class='m-right'>{_heatmap_html(pred, actual)}</div>"
        f"</div>{expander}</div>"
    )


def _group_forecast_html(adv: dict | None, played_n: int, total_n: int) -> str:
    """Forward-looking replacement for a standings table: each team's
    model-simulated chance to reach the knockouts (and to win the group)."""
    if not adv:
        return ""
    rows = sorted(adv.items(),
                  key=lambda kv: (-kv[1]["p_advance"], -kv[1]["p_win"]))
    items = [
        "<div class='gf-colhead'><span class='gf-spacer'></span>"
        "<span>adv</span><span>win</span></div>"
    ]
    for team, d in rows:
        adv_pct = d["p_advance"] * 100
        win_pct = d["p_win"] * 100
        tier = "hi" if adv_pct >= 75 else ("mid" if adv_pct >= 40 else "lo")
        items.append(
            f"<div class='gf-row'>"
            f"<span class='gf-team'>{_flag(team)} {html.escape(team)}"
            f"<span class='gf-pts'>{d['pts']:.0f} pts</span></span>"
            f"<div class='gf-track' title='reach knockouts: {adv_pct:.0f}%'>"
            f"<div class='gf-fill {tier}' style='width:{max(adv_pct,2):.1f}%'></div>"
            f"<span class='gf-adv'>{adv_pct:.0f}%</span></div>"
            f"<span class='gf-win' title='win the group'>{win_pct:.0f}%</span>"
            f"</div>"
        )
    note = (f"{played_n}/{total_n} played &middot; "
            f"top 2 + 8 best 3rd-placed advance")
    return (
        f"<div class='gforecast'>"
        f"<div class='gf-head'>Chance to reach the knockouts"
        f"<span class='gf-note'>{note}</span></div>"
        f"{''.join(items)}"
        f"</div>"
    )


def _build_adv_prob(idata, wc_teams: list[str], teams: list[str]):
    """NxN matrix: P(team i beats team j) in a neutral knockout, i.e. regulation
    win probability plus a coin-flip shootout on draws. Indexed by wc_teams."""
    n = len(wc_teams)
    adv = np.full((n, n), 0.5)
    known = set(teams)
    for i in range(n):
        if wc_teams[i] not in known:
            continue
        for j in range(i + 1, n):
            if wc_teams[j] not in known:
                continue
            p = predict(idata, wc_teams[i], wc_teams[j], neutral=True, teams=teams)
            adv[i, j] = p.p_home_win + 0.5 * p.p_draw
            adv[j, i] = p.p_away_win + 0.5 * p.p_draw
    return adv


def _title_odds_section(odds: dict | None) -> str:
    """Headline knockout deliverable: each team's simulated chance to win the
    World Cup, reach the final, and reach the round of 16."""
    if not odds:
        return ""
    rows = sorted(odds.items(), key=lambda kv: -kv[1]["p_champion"])
    cmax = max((r["p_champion"] for _, r in rows), default=0) or 1.0

    items = []
    for rank, (team, d) in enumerate(rows, 1):
        champ = d["p_champion"] * 100
        w = max(champ / (cmax * 100) * 100, 1.5)
        items.append(
            f"<div class='to-row'>"
            f"<span class='to-rank'>{rank}</span>"
            f"<span class='to-team'>{_flag(team)} {html.escape(team)}</span>"
            f"<div class='to-track' title='Win the World Cup: {champ:.1f}%'>"
            f"<div class='to-fill' style='width:{w:.1f}%'></div>"
            f"<span class='to-val'>{champ:.1f}%</span></div>"
            f"<span class='to-sub' title='Reach the final'>F {d['p_final']*100:.0f}%</span>"
            f"<span class='to-sub' title='Reach the round of 16'>R16 {d['p_r16']*100:.0f}%</span>"
            f"</div>"
        )
    return (
        "<section class='titleodds' id='titleodds'>"
        "<div class='g-head' onclick=\"toggleTitle()\">"
        "<h2>Title odds &middot; who wins the World Cup?</h2>"
        "<span class='g-toggle'>&#9662;</span></div>"
        "<div class='to-body' id='to-body'>"
        "<p class='to-lead'>Each team's chance to lift the trophy, from "
        "<b>20,000 simulations</b> of the whole tournament — every remaining "
        "group match sampled from the model, then the verified knockout bracket "
        "played out (ties resolved by extra-time/penalty coin-flip). "
        "<span class='to-bars'>Bar = championship probability; "
        "<b>F</b> = reach final, <b>R16</b> = reach round of 16.</span></p>"
        f"<div class='to-grid'>{''.join(items)}</div>"
        "</div></section>"
    )


def _strength_section(idata, fixtures: pd.DataFrame) -> str:
    """What the model learned: each WC2026 team's latent attack and defense
    (posterior means). This is the engine behind every projected scoreline —
    surfacing it explains *why* a given goal count is expected."""
    teams_all = list(idata.attrs.get("teams", idata.posterior["team"].values))
    atk = idata.posterior["atk"].mean(("chain", "draw")).values
    deff = idata.posterior["def"].mean(("chain", "draw")).values
    strength = {t: (float(atk[i]), float(deff[i])) for i, t in enumerate(teams_all)}

    wc_teams = sorted(set(fixtures["home_team"]) | set(fixtures["away_team"]))
    rows = [(t, strength[t][0], strength[t][1]) for t in wc_teams if t in strength]
    if not rows:
        return ""

    a_vals = [r[1] for r in rows]
    d_vals = [r[2] for r in rows]
    a_lo, a_hi = min(a_vals), max(a_vals)
    d_lo, d_hi = min(d_vals), max(d_vals)

    def norm(v, lo, hi):
        return 0.0 if hi <= lo else (v - lo) / (hi - lo)

    # Sort by overall quality (attack + defense are both "higher = better").
    rows.sort(key=lambda r: -(r[1] + r[2]))

    items = []
    for rank, (team, a, d) in enumerate(rows, 1):
        items.append(
            f"<div class='st-row'>"
            f"<span class='st-rank'>{rank}</span>"
            f"<span class='st-team'>{_flag(team)} {html.escape(team)}</span>"
            f"<span class='st-bars'>"
            f"<span class='st-bar' title='Attack rating'>"
            f"<span class='st-fill atk' style='width:{norm(a,a_lo,a_hi)*100:.0f}%'></span></span>"
            f"<span class='st-bar' title='Defense rating'>"
            f"<span class='st-fill def' style='width:{norm(d,d_lo,d_hi)*100:.0f}%'></span></span>"
            f"</span></div>"
        )

    return (
        "<section class='insight' id='insight'>"
        "<div class='g-head' onclick=\"toggleInsight()\">"
        "<h2>What the model learned &middot; team strength</h2>"
        "<span class='g-toggle'>&#9662;</span></div>"
        "<div class='insight-body' id='insight-body'>"
        "<p class='insight-sub'>Latent <b class='lbl-atk'>attack</b> and "
        "<b class='lbl-def'>defense</b> strengths (posterior means, ranked by "
        "overall quality). These are the parameters the model fits from goals — "
        "the reason behind every projected scoreline. Bars are relative to the "
        "WC2026 field.</p>"
        f"<div class='st-grid'>{''.join(items)}</div>"
        "</div></section>"
    )


def _callouts(preds) -> str:
    """Standout cards drawn from UPCOMING matches."""
    up = [(r, p) for r, p in preds
          if p is not None and not getattr(r, "played", False)]
    if not up:
        return ""

    def matchup(r):
        return (f"{_flag(r.home_team)} {html.escape(r.home_team)} v "
                f"{html.escape(r.away_team)} {_flag(r.away_team)}")

    # Most confident pick.
    conf = max(up, key=lambda rp: max(rp[1].p_home_win, rp[1].p_away_win))
    cr, cp = conf
    cside = "home" if cp.p_home_win >= cp.p_away_win else "away"
    cwin = cr.home_team if cside == "home" else cr.away_team
    cprob = max(cp.p_home_win, cp.p_away_win)

    # Closest match (toss-up): smallest gap between top-2 of the three outcomes.
    def spread(p):
        s = sorted([p.p_home_win, p.p_draw, p.p_away_win], reverse=True)
        return s[0] - s[1]
    toss = min(up, key=lambda rp: spread(rp[1]))
    tr, tp = toss

    # Highest expected goals.
    goals = max(up, key=lambda rp: rp[1].exp_home_goals + rp[1].exp_away_goals)
    gr, gp = goals
    gtot = gp.exp_home_goals + gp.exp_away_goals

    def card(tag, title, body):
        return (f"<div class='callout'><div class='co-tag'>{tag}</div>"
                f"<div class='co-title'>{title}</div>"
                f"<div class='co-body'>{body}</div></div>")

    return (
        "<div class='callouts'>"
        + card("Most confident", f"{_flag(cwin)} {html.escape(cwin)} to win",
               f"{matchup(cr)} &middot; {_pct(cprob)}")
        + card("Tightest call", "Coin-flip of the round",
               f"{matchup(tr)} &middot; {_pct(tp.p_home_win)}/"
               f"{_pct(tp.p_draw)}/{_pct(tp.p_away_win)}")
        + card("Goal-fest watch", f"~{gtot:.1f} goals expected",
               f"{matchup(gr)} &middot; over 2.5: {_pct(gp.p_over_2_5)}")
        + "</div>"
    )


_STAGE_ORDER = ["Group"]


def _variant_table_html() -> str:
    """If a model-variant backtest comparison exists, render it as a table."""
    path = PROJECT_ROOT / "reports" / "model_variants.json"
    if not path.exists():
        return ""
    try:
        rows = json.loads(path.read_text())
    except Exception:
        return ""
    order = ["baseline", "dixon_coles", "confederation", "dc+confed", "elo"]
    label = {"baseline": "Double-Poisson (shipped)", "dixon_coles": "+ Dixon–Coles",
             "confederation": "+ Confederation layer", "dc+confed": "+ Both",
             "elo": "Elo baseline"}
    best_rps = min((r["RPS"] for r in rows.values()), default=None)
    body = []
    for k in order:
        if k not in rows:
            continue
        r = rows[k]
        star = " &#9733;" if r["RPS"] == best_rps else ""
        body.append(
            f"<tr><td class='tl'>{label.get(k, k)}{star}</td>"
            f"<td>{r['RPS']:.4f}</td><td>{r['log_loss']:.3f}</td>"
            f"<td>{r['Brier']:.3f}</td><td>{r.get('accuracy', 0)*100:.1f}%</td></tr>"
        )
    return (
        "<table class='mtable'><thead><tr><th class='tl'>Model</th>"
        "<th>RPS</th><th>log-loss</th><th>Brier</th><th>acc</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
        "<p class='m-note'>Lower RPS / log-loss / Brier is better. &#9733; = best. "
        "Expanding-window temporal backtest, no leakage.</p>"
    )


def _method_section(metrics: dict, n_teams: int) -> str:
    """The 'Method' tab: what the model is, the data, validation, and an honest
    record of what was tested and rejected — the portfolio narrative."""
    rps_edge = (metrics["elo_rps"] - metrics["bayes_rps"]) / metrics["elo_rps"] * 100
    scoring_note = ""
    if metrics.get("scored_n"):
        scoring_note = (
            f"<p class='m-note'>On the <b>{metrics['scored_n']}</b> WC2026 matches "
            f"played so far it has called <b>{metrics['ou_acc']:.0f}%</b> of "
            f"over/under-2.5 totals correctly and nailed <b>{metrics['exact_hits']}/"
            f"{metrics['scored_n']}</b> exact final scores, placing on average "
            f"<b>{metrics['total_mass']*100:.0f}%</b> of its probability on the "
            f"actual goal total. These are small-sample, in-tournament numbers — "
            f"the backtest figures are the stable measure of skill.</p>"
        )
    return (
        "<section class='method' id='method'>"
        "<h2>How this works</h2>"
        "<p class='m-lead'>Every number on this page comes from one Bayesian "
        "statistical model fit to historical results — no hand-tuning, no "
        "bookmaker odds. Here's the honest version of what it does and what it "
        "can't.</p>"

        "<div class='m-grid'>"

        "<div class='m-card'><h3>The model</h3>"
        "<p>A <b>Bayesian hierarchical double-Poisson</b> (the Dixon–Coles "
        "lineage). Each team carries a latent <b class='lbl-atk'>attack</b> and "
        "<b class='lbl-def'>defense</b> strength; goals are Poisson-distributed "
        "around those strengths, with a single home-advantage term that switches "
        "off at neutral venues.</p>"
        "<pre class='m-eq'>log &#955;_home = intercept + home_adv&#183;(1&#8722;neutral) "
        "+ atk[home] &#8722; def[away]\nlog &#955;_away = intercept "
        "+ atk[away] &#8722; def[home]</pre>"
        "<p>It's fit by <b>MCMC</b> (PyMC + nutpie), so every prediction "
        "integrates over the full posterior — the scoreline grid reflects "
        "genuine parameter uncertainty, not a single point estimate.</p></div>"

        "<div class='m-card'><h3>The data</h3>"
        "<p>The CC0 <a href='https://github.com/martj42/international_results'>"
        "martj42/international_results</a> dataset — <b>8,000+</b> men's "
        f"international matches since 2018, <b>{n_teams}</b> teams. The model "
        "uses only <b>goals, venue (neutral flag), date and tournament</b>.</p>"
        "<p class='m-warn'>It deliberately has <b>no</b> xG, shots, lineups, "
        "player ratings, or betting odds — those barely exist for international "
        "football and aren't in a free, redistributable source. This is a "
        "goals-only model, and honest about it.</p></div>"

        "<div class='m-card'><h3>Does it actually work?</h3>"
        f"<p>On a temporal backtest (train on the past, predict the future, no "
        f"leakage) it scores <b>RPS {metrics['bayes_rps']:.3f}</b> — about "
        f"<b>{rps_edge:.0f}% better than Elo</b> ({metrics['elo_rps']:.3f}) — and "
        "is well-calibrated (predicted probabilities match observed frequencies). "
        "RPS is the standard proper score for ordered 1X2 outcomes.</p>"
        f"{scoring_note}"
        f"{_variant_table_html()}</div>"

        "<div class='m-card'><h3>What we tested and rejected</h3>"
        "<p>The interesting part of a model is what <i>didn't</i> help. On the "
        "same backtest, all of these were within run-to-run noise or worse, so "
        "they're <b>off</b>:</p>"
        "<ul class='m-list'>"
        "<li><b>Time-decay weighting</b> (recent matches count more) — best "
        "variant ~&#8722;0.3% RPS, inside the noise.</li>"
        "<li><b>Tournament-importance weighting</b> — slightly <i>hurt</i>.</li>"
        "<li><b>Blending with Elo</b> — a weighted average only got worse as more "
        "Elo was added; pure Bayesian was optimal.</li>"
        "<li><b>Confederation hierarchy</b> (shrink teams toward their "
        "AFC/CAF/… mean) — a hair better on paper but inside the noise, and it "
        "muddied the model's convergence, so it's off.</li>"
        "<li><b>Dixon–Coles low-score correction</b> — once correctly bounded, "
        "it's RPS-neutral (a genuinely tiny effect for international football).</li>"
        "</ul>"
        "<p class='m-note'>The model sits at the <b>goals-only information "
        "ceiling</b>: with this data, the plain double-Poisson is as good as it "
        "gets. We measured that rather than assuming it.</p></div>"

        "</div>"

        "<p class='m-foot'>Source: martj42/international_results (CC0). "
        "Built with Python, pandas, PyMC. Predictions are probabilistic — a 70% "
        "favourite still loses three times in ten.</p>"
        "</section>"
    )


# --- chronological view (shared by Upcoming and Results) -------------------

def _chrono_section(rows_preds, section_id: str, css_class: str,
                    title: str, sub: str) -> str:
    """Flat chronological list (grouped by day) of the given (row, pred) pairs,
    in kickoff order. Powers both the Upcoming and Results tabs so they look and
    behave identically."""
    days: list[list] = []
    cur_day = None
    for r, p in rows_preds:
        day = pd.Timestamp(r.date).strftime("%Y-%m-%d") if pd.notna(r.date) else "?"
        if day != cur_day:
            label = (pd.Timestamp(r.date).strftime("%a &middot; %b %d")
                     if pd.notna(r.date) else "Date TBD")
            days.append([label, []])
            cur_day = day
        days[-1][1].append(_match_card(r, p))
    body = "".join(
        f"<div class='chrono-day'>{label}</div>"
        f"<div class='cards'>{''.join(cards)}</div>"
        for label, cards in days
    )
    if not days:
        body = "<p class='chrono-empty'>Nothing here yet.</p>"
    return (
        f"<section class='chrono {css_class}' id='{section_id}'>"
        f"<div class='chrono-head'><h2>{title}</h2>"
        f"<span class='chrono-sub'>{sub}</span></div>"
        f"{body}</section>"
    )


# --- knockout bracket ------------------------------------------------------

# CSV `stage` values, in bracket order. Knockout fixtures appended to the
# fixtures CSV (in bracket order within each stage) populate the tree; until
# then the slots show only their source label + the model's projected occupant.
_KO_STAGES = ["Round of 32", "Round of 16", "Quarter-final", "Semi-final", "Final"]


def _projected_qualifiers(advancement: dict | None) -> dict:
    """Model's projected group winner / runner-up per group (top two by chance
    to advance). Keyed by bracket slot: ('1', G) -> (team, p_advance),
    ('2', G) -> (team, p_advance). Used to pre-fill the bracket faintly."""
    proj: dict = {}
    for g, adv in (advancement or {}).items():
        if not adv:
            continue
        ranked = sorted(adv.items(), key=lambda kv: -kv[1]["p_advance"])
        if len(ranked) >= 1:
            proj[("1", g)] = (ranked[0][0], ranked[0][1]["p_advance"])
        if len(ranked) >= 2:
            proj[("2", g)] = (ranked[1][0], ranked[1][1]["p_advance"])
    return proj


def _bk_skeleton_slot(slot, proj: dict) -> str:
    """A bracket slot before its team is known: source label, plus the model's
    projected occupant (faint) where we can name one. Always emits a .bk-src
    label zone and a .bk-val value zone so every slot is the same height."""
    kind, val = slot
    if kind == "3":
        return ("<div class='bk-team empty'>"
                "<span class='bk-src'>Best 3rd-placed</span>"
                "<span class='bk-val'>&mdash;</span></div>")
    src = f"Winner {val}" if kind == "1" else f"Runner-up {val}"
    pj = proj.get(slot)
    if pj:
        team, padv = pj
        return (f"<div class='bk-team proj'><span class='bk-src'>{src}</span>"
                f"<span class='bk-val'><span class='bk-proj'>{_flag(team)} "
                f"{html.escape(team)}</span>"
                f"<span class='bk-pp' title='projected to advance'>"
                f"{padv*100:.0f}%</span></span></div>")
    return (f"<div class='bk-team empty'><span class='bk-src'>{src}</span>"
            f"<span class='bk-val'>&mdash;</span></div>")


def _bk_winner_slot(label: str) -> str:
    return (f"<div class='bk-team empty'><span class='bk-src'>{label}</span>"
            f"<span class='bk-val'>&mdash;</span></div>")


def _bk_actual_cell(row, pred) -> str:
    """A knockout cell once the matchup is real (from a CSV knockout row)."""
    home, away = row.home_team, row.away_team
    played = bool(getattr(row, "played", False))

    def team_line(name, side):
        win = ""
        if pred is not None:
            # neutral knockout win prob = regulation win + coin-flip on draws
            ph = pred.p_home_win + 0.5 * pred.p_draw
            pa = pred.p_away_win + 0.5 * pred.p_draw
            wp = ph if side == "home" else pa
            win = f"<span class='bk-wp'>{wp*100:.0f}%</span>"
        return (f"<div class='bk-team real'>"
                f"<span class='bk-val'>"
                f"<span class='bk-name'>{_flag(name)} {html.escape(name)}</span>"
                f"{win}</span></div>")

    cell = team_line(home, "home") + team_line(away, "away")
    if played:
        hg, ag = int(row.home_score), int(row.away_score)
        cell += f"<div class='bk-score'>{hg}&#8211;{ag}</div>"
    return cell


def _bracket_section(preds, advancement: dict | None) -> str:
    """Pre-built knockout bracket (R32 -> Final). Empty slots show their source
    label and the model's projected occupant; real matchups appear as knockout
    rows are added to the fixtures CSV (in bracket order per stage)."""
    proj = _projected_qualifiers(advancement)

    # Actual knockout fixtures by stage, in kickoff order (preds is sorted).
    by_stage: dict[str, list] = {s: [] for s in _KO_STAGES}
    for r, p in preds:
        st = getattr(r, "stage", "")
        if st in by_stage:
            by_stage[st].append((r, p))
    have_actual = any(by_stage[s] for s in _KO_STAGES)

    def cell(match_html: str) -> str:
        return f"<div class='bk-match'>{match_html}</div>"

    # Round of 32 — from the verified slot structure, overlaid with actuals.
    r32 = by_stage["Round of 32"]
    r32_cells = []
    for i, (sa, sb) in enumerate(_R32):
        if i < len(r32):
            r, p = r32[i]
            r32_cells.append(cell(_bk_actual_cell(r, p)))
        else:
            r32_cells.append(cell(_bk_skeleton_slot(sa, proj)
                                  + _bk_skeleton_slot(sb, proj)))

    def downstream(stage_name, pairs, feed_label):
        actual = by_stage[stage_name]
        cells = []
        for j, (a, b) in enumerate(pairs):
            if j < len(actual):
                r, p = actual[j]
                cells.append(cell(_bk_actual_cell(r, p)))
            else:
                cells.append(cell(
                    _bk_winner_slot(f"Winner {feed_label} {a + 1}")
                    + _bk_winner_slot(f"Winner {feed_label} {b + 1}")))
        return cells

    r16_cells = downstream("Round of 16", _R16, "R32")
    qf_cells = downstream("Quarter-final", _QF, "R16")
    sf_cells = downstream("Semi-final", _SF, "QF")
    # Final: winners of the two semis.
    fin = by_stage["Final"]
    if fin:
        r, p = fin[0]
        final_cells = [cell(_bk_actual_cell(r, p))]
    else:
        final_cells = [cell(_bk_winner_slot("Winner SF 1")
                            + _bk_winner_slot("Winner SF 2"))]

    cols = [
        ("Round of 32", r32_cells),
        ("Round of 16", r16_cells),
        ("Quarter-finals", qf_cells),
        ("Semi-finals", sf_cells),
        ("Final", final_cells),
    ]
    col_html = "".join(
        f"<div class='bk-col'><div class='bk-col-h'>{name}</div>"
        f"{''.join(cells)}</div>"
        for name, cells in cols
    )

    note = ("Real matchups appear here as knockout fixtures are confirmed. "
            if not have_actual else "")
    lead = (
        "<p class='bk-lead'>The verified WC2026 knockout tree. "
        f"{note}Empty slots show the model's <b class='bk-proj-lbl'>projected</b> "
        "qualifier (top two per group by chance to advance); "
        "<b>Best 3rd-placed</b> slots are cross-group and filled once the "
        "eight qualifying third places are known.</p>"
    )
    return (
        "<section class='bracket' id='bracket'>"
        "<div class='bk-head'><h2>Knockout bracket</h2></div>"
        f"{lead}"
        f"<div class='bk-scroll'>{col_html}</div>"
        "</section>"
    )


# --- "Model vs Market" (Polymarket) tab ------------------------------------

def _poly_blob(preds, title_odds, odds_meta, asof: str):
    """Merge our model probabilities with the resolved Polymarket identifiers
    into the JSON blob baked into the page. The page's JS fetches live prices
    for these slugs; the snapshot is the offline fallback. Returns None if there
    is nothing to compare (no odds resolved)."""
    if not odds_meta:
        return None
    matches_meta, title_meta = odds_meta
    matches_meta = matches_meta or {}
    title_meta = title_meta or {}

    out_matches = []
    for r, p in preds:
        if p is None or getattr(r, "played", False):
            continue
        date_str = (pd.Timestamp(r.date).strftime("%Y-%m-%d")
                    if pd.notna(r.date) else "")
        meta = matches_meta.get((r.home_team, r.away_team, date_str))
        if not meta:
            continue
        out_matches.append({
            "home": r.home_team, "away": r.away_team, "date": date_str,
            "slug": meta["slug"], "moreSlug": meta["more_slug"],
            "homeGit": meta["home_git"], "drawGit": meta["draw_git"],
            "awayGit": meta["away_git"],
            "bttsQ": meta["btts_q"], "o25Q": meta["o25_q"],
            "vol": meta["volume"], "snap": meta["snapshot"],
            "model": {
                "h": round(p.p_home_win, 4), "d": round(p.p_draw, 4),
                "a": round(p.p_away_win, 4),
                "btts": round(float(p.grid[1:, 1:].sum()), 4),
                "o25": round(p.p_over_2_5, 4),
            },
        })

    out_title = []
    teams_meta = title_meta.get("teams", {})
    for team, d in (title_odds or {}).items():
        tm = teams_meta.get(team)
        if not tm:
            continue
        out_title.append({"team": team, "git": tm["git"],
                          "model": round(d["p_champion"], 4), "snap": tm["snap"]})
    out_title.sort(key=lambda x: -x["snap"])

    if not out_matches and not out_title:
        return None
    return {
        "asof": asof,
        "matches": out_matches,
        "title": {"slug": title_meta.get("slug", "world-cup-winner"),
                  "sum": round(title_meta.get("sum", 1.0), 5),
                  "teams": out_title},
    }


def _market_section(blob) -> str:
    """Static shell for the Model-vs-Market tab. The two tables are filled by JS
    (from the live Gamma API, falling back to the baked snapshot); this renders
    the disclaimer, controls, table scaffolding and footnotes."""
    if not blob:
        return (
            "<section class='market' id='market'>"
            "<div class='mk-head'><h2>Model vs Market</h2></div>"
            "<p class='mk-lead'>Live market comparison is currently unavailable "
            "(no open Polymarket markets resolved at build time). It returns "
            "automatically once upcoming-match markets are live.</p>"
            "</section>"
        )

    disclaimer = (
        "<div class='mk-disclaimer'>"
        "<b>Read this first — divergence is not value.</b> This tab shows where "
        "our <b>goals-only</b> model disagrees with Polymarket's market-implied "
        "odds. The market is liquid and prices things we can't see — lineups, "
        "injuries, money flow — and our model is at its information ceiling. So a "
        "gap almost always means <i>the market knows something we don't</i>, not "
        "that there's a bet to make. Treat every row as a hypothesis about our "
        "blind spots. <b>Informational, not betting advice.</b>"
        "</div>"
    )
    controls = (
        "<div class='mk-controls'>"
        "<span class='mk-asof'>Odds as of <b id='mk-asof'>snapshot</b>"
        "<span class='mk-dot' id='mk-dot' title='live'></span></span>"
        "<button class='mk-refresh' id='mk-refresh' onclick='refreshMarket()'>"
        "&#8635; Refresh odds</button>"
        "</div>"
    )
    pm_table = (
        "<h3 class='mk-h3'>Per-match &middot; biggest disagreements first"
        "<span class='mk-sub'>tap a column to sort</span></h3>"
        "<div class='mk-tablewrap'><table class='mk-table mk-sortable'><thead><tr>"
        "<th class='tl' data-key='match' onclick='mvmSort(this)'>Match</th>"
        "<th class='tl' data-key='out' onclick='mvmSort(this)'>Outcome</th>"
        "<th data-key='model' onclick='mvmSort(this)'>Model</th>"
        "<th data-key='mkt' onclick='mvmSort(this)'>Market</th>"
        "<th data-key='edge' class='mk-sorted-desc' onclick='mvmSort(this)'>Edge</th>"
        "<th data-key='ev' onclick='mvmSort(this)'>EV</th>"
        "<th data-key='vig' onclick='mvmSort(this)'>Vig</th>"
        "<th data-key='vol' onclick='mvmSort(this)'>Vol</th></tr></thead>"
        "<tbody id='mk-rows'></tbody></table></div>"
        "<p class='mk-empty' id='mk-rows-empty' style='display:none'>"
        "No open per-match markets right now.</p>"
    )
    title_table = (
        "<h3 class='mk-h3'>Title odds &middot; model champion% vs the winner market"
        "<span class='mk-sub'>~$2.9B market &middot; favourites first</span></h3>"
        "<div class='mk-tablewrap'><table class='mk-table mk-sortable'><thead><tr>"
        "<th class='tl' data-key='team' onclick='mvmSortT(this)'>Team</th>"
        "<th data-key='model' onclick='mvmSortT(this)'>Model</th>"
        "<th data-key='mkt' class='mk-sorted-desc' onclick='mvmSortT(this)'>Market</th>"
        "<th data-key='edge' onclick='mvmSortT(this)'>Edge</th>"
        "</tr></thead><tbody id='mk-title'></tbody></table></div>"
    )
    foot = (
        "<p class='mk-foot'>Market probabilities are de-vigged proportionally "
        "(price &divide; sum of outcomes); <b>Edge</b> = model &minus; market in "
        "percentage points; <b>EV</b> = model &divide; market &minus; 1 for a unit "
        "stake. Rows where the market is thin (low volume) or the overround is "
        "high (&gt;6%) are greyed; EV is hidden for sub-5% market prices "
        "(favourite&#8211;longshot noise). Source: Polymarket Gamma API (keyless, "
        "fetched live in your browser). Not affiliated with Polymarket; "
        "educational comparison only.</p>"
    )
    return (
        "<section class='market' id='market'>"
        "<div class='mk-head'><h2>Model vs Market</h2></div>"
        f"{disclaimer}{controls}"
        "<div class='mk-status' id='mk-status'></div>"
        f"{pm_table}{title_table}{foot}"
        "</section>"
    )


# --- page assembly ---------------------------------------------------------

def render_report(
    idata,
    fixtures: pd.DataFrame,
    teams: list[str],
    out_path: Path | None = None,
    generated_on: str = "",
    metrics: dict | None = None,
    odds_meta=None,
) -> Path:
    out_path = out_path or DEFAULT_OUT
    metrics = {**DEFAULT_METRICS, **(metrics or {})}
    preds = build_predictions(idata, fixtures, teams)
    advancement = simulate_advancement(preds)

    # Full-tournament title odds (champion / reach-round probabilities).
    wc_teams = sorted(set(fixtures["home_team"]) | set(fixtures["away_team"]))
    try:
        adv_prob = _build_adv_prob(idata, wc_teams, teams)
        title_odds = simulate_tournament(preds, adv_prob, wc_teams)
    except Exception:
        title_odds = None

    # Played / total counts per group (for the forecast caption).
    played_by_group: dict[str, int] = {}
    total_by_group: dict[str, int] = {}
    for r, _ in preds:
        g = getattr(r, "group", "")
        if not g:
            continue
        total_by_group[g] = total_by_group.get(g, 0) + 1
        if getattr(r, "played", False):
            played_by_group[g] = played_by_group.get(g, 0) + 1

    # Accuracy on played matches: 1X2 picks plus goals-market accuracy (used by
    # the hero scoring tile + the Method tab).
    n_played = n_correct = 0
    ou_hits = exact_hits = 0
    goal_mass_sum = 0.0
    for row, pred in preds:
        if pred is not None and getattr(row, "played", False):
            n_played += 1
            hs, as_ = int(row.home_score), int(row.away_score)
            if _actual_label(hs, as_) == _result_label(pred):
                n_correct += 1
            # over/under 2.5 directional call
            if (pred.p_over_2_5 >= 0.5) == ((hs + as_) >= 3):
                ou_hits += 1
            # exact modal scoreline
            mi, mj, _mp = pred.top_scorelines(1)[0]
            if (mi, mj) == (hs, as_):
                exact_hits += 1
            # probability mass the model placed on the actual goal total
            gn = pred.grid.shape[0]
            totals = np.add.outer(np.arange(gn), np.arange(gn))
            goal_mass_sum += float(pred.grid[totals == (hs + as_)].sum())
    n_upcoming = sum(1 for r, p in preds
                     if p is not None and not getattr(r, "played", False))
    acc_pct = (n_correct / n_played * 100) if n_played else 0
    ou_acc = (ou_hits / n_played * 100) if n_played else 0.0
    total_mass = (goal_mass_sum / n_played) if n_played else 0.0
    # Hand the in-tournament scoring stats to the Method tab.
    metrics = {**metrics, "ou_acc": ou_acc, "exact_hits": exact_hits,
               "scored_n": n_played, "total_mass": total_mass}

    # Group sections (A..L), each: advance forecast + cards.
    group_letters = sorted({getattr(r, "group", "") for r, _ in preds
                            if getattr(r, "group", "")})
    sections = []
    for g in group_letters:
        cards = [_match_card(r, p) for r, p in preds
                 if getattr(r, "group", "") == g]
        sec = (
            f"<section class='group' id='grp-{g}'>"
            f"<div class='g-head' onclick=\"toggleGroup('{g}')\">"
            f"<h2>Group {g}</h2><span class='g-toggle'>&#9662;</span></div>"
            f"<div class='g-body' id='body-{g}'>"
            f"{_group_forecast_html(advancement.get(g), played_by_group.get(g, 0), total_by_group.get(g, 6))}"
            f"<div class='cards'>{''.join(cards)}</div>"
            f"</div></section>"
        )
        sections.append(sec)

    # Chronological flat views (grouped by day, kickoff order) for the Upcoming
    # and Results tabs. The grouped per-group view stays for the All tab (where
    # the group pills still let you jump around).
    upcoming_rp = [(r, p) for r, p in preds
                   if p is not None and not getattr(r, "played", False)]
    played_rp = [(r, p) for r, p in preds
                 if p is not None and getattr(r, "played", False)]
    chrono_html = _chrono_section(
        upcoming_rp, "chrono-upcoming", "chrono-up",
        "Upcoming matches", "chronological &middot; soonest first")
    results_html = _chrono_section(
        played_rp, "chrono-results", "chrono-res",
        "Results", "chronological &middot; every played match")
    bracket_html = _bracket_section(preds, advancement)
    poly_blob = _poly_blob(preds, title_odds, odds_meta,
                           asof=generated_on or "snapshot")
    market_html = _market_section(poly_blob)
    poly_json = (json.dumps(poly_blob).replace("<", "\\u003c")
                 if poly_blob else "null")

    nav_pills = "".join(
        f"<a class='pill' href='#grp-{g}'>{g}</a>" for g in group_letters
    )

    gen = f" &middot; as of {html.escape(generated_on)}" if generated_on else ""
    rps_edge = (metrics["elo_rps"] - metrics["bayes_rps"]) / metrics["elo_rps"] * 100

    tiles = (
        f"<div class='tiles'>"
        f"<div class='tile'><div class='t-val'>{n_correct}/{n_played}</div>"
        f"<div class='t-lab'>correct picks &middot; {acc_pct:.0f}%</div></div>"
        f"<div class='tile'><div class='t-val'>{metrics['bayes_rps']:.3f}</div>"
        f"<div class='t-lab'>RPS &middot; {rps_edge:.0f}% better than Elo</div></div>"
        f"<div class='tile'><div class='t-val'>{n_upcoming}</div>"
        f"<div class='t-lab'>matches still to play</div></div>"
        f"<div class='tile'><div class='t-val'>{ou_acc:.0f}%</div>"
        f"<div class='t-lab'>over/under 2.5 calls right &middot; "
        f"{exact_hits}/{n_played} exact scores</div></div>"
        f"</div>"
    )

    doc = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>World Cup 2026 — Match Predictions</title>"
        f"<style>{_CSS}</style></head><body>"
        "<div class='hero'><div class='wrap'>"
        "<div class='eyebrow'>Bayesian hierarchical Poisson &middot; MCMC</div>"
        "<h1>World Cup 2026<br><span class='accent'>Match Predictions</span></h1>"
        f"<p class='sub'>Trained on 8,000+ international matches since 2018. "
        f"Every probability integrates over the full posterior.{gen}</p>"
        f"{tiles}"
        f"{_callouts(preds)}"
        "</div></div>"
        "<nav class='nav'><div class='wrap nav-in'>"
        "<div class='filters'>"
        "<button class='f-btn active' data-filter='all' onclick=\"setFilter('all',this)\">All</button>"
        "<button class='f-btn' data-filter='upcoming' onclick=\"setFilter('upcoming',this)\">Upcoming</button>"
        "<button class='f-btn' data-filter='played' onclick=\"setFilter('played',this)\">Results</button>"
        "<button class='f-btn' data-filter='bracket' onclick=\"setFilter('bracket',this)\">Bracket</button>"
        "<button class='f-btn' data-filter='market' onclick=\"setFilter('market',this)\">Model vs Market</button>"
        "<button class='f-btn' data-filter='method' onclick=\"setFilter('method',this)\">Method</button>"
        "</div>"
        "<input id='search' class='search' type='search' autocomplete='off' "
        "placeholder='Search a team…' aria-label='Search for a team' "
        "oninput='searchTeams(this.value)'>"
        f"<div class='pills'>{nav_pills}</div>"
        "</div></nav>"
        "<main class='wrap'>"
        "<div class='legend'>Bars: <i class='lh'>home</i> &middot; "
        "<i class='ld'>draw</i> &middot; <i class='la'>away</i>. "
        "Heatmap rows = home goals, columns = away goals; brighter = more likely, "
        "outlined cell = most-likely score"
        " (<span class='sw-mode'></span>), green ring = actual result"
        " (<span class='sw-actual'></span>).</div>"
        f"{_title_odds_section(title_odds)}"
        f"{_strength_section(idata, fixtures)}"
        f"<div class='no-results' id='no-results'>No matches for that team.</div>"
        f"{''.join(sections)}"
        f"{chrono_html}"
        f"{results_html}"
        f"{bracket_html}"
        f"{market_html}"
        f"{_method_section(metrics, len(teams))}"
        "<footer>Double-Poisson with hierarchical attack/defense strengths and "
        "neutral-gated home advantage, fit via MCMC (PyMC/nutpie). "
        "Backtest beats Elo on RPS, log-loss and Brier. "
        "Source: martj42/international_results (CC0). "
        "Knockout fixtures are added once group standings are final.</footer>"
        "</main>"
        "<div id='tip' class='tip' role='tooltip'></div>"
        f"<script>window.POLY={poly_json};</script>"
        f"<script>{_JS}</script>"
        "<script>" + _MARKET_JS + "</script>"
        "</body></html>"
    )
    out_path.write_text(doc, encoding="utf-8")
    return out_path


_CSS = """
:root{
 --bg:#0a0e14;--bg2:#0e141d;--card:#141b26;--card2:#19212e;--ink:#eef3f8;
 --muted:#8a97a6;--faint:#5b6675;--line:#232c3a;--line2:#2c3645;
 --home:#34d399;--draw:#fbbf24;--away:#fb7185;--accent:#60a5fa;
 --good:#34d399;--shadow:0 8px 30px rgba(0,0,0,.35)}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
 -webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
b{font-variant-numeric:tabular-nums}
.flag{display:inline-block;line-height:0;vertical-align:-.16em}
.flag svg{width:1.15em;height:1.15em;display:block;border-radius:50%}

/* hero */
.hero{background:
  radial-gradient(900px 380px at 80% -10%,rgba(96,165,250,.18),transparent 60%),
  radial-gradient(700px 320px at 0% 0%,rgba(52,211,153,.12),transparent 55%),
  linear-gradient(180deg,#0c121b,var(--bg));
 border-bottom:1px solid var(--line);padding:46px 0 30px}
.eyebrow{color:var(--accent);font-size:12.5px;font-weight:700;letter-spacing:.14em;
 text-transform:uppercase;margin-bottom:10px}
h1{font-size:clamp(30px,6vw,50px);line-height:1.04;margin:0;font-weight:800;
 letter-spacing:-.02em}
h1 .accent{background:linear-gradient(90deg,#7dd3fc,#34d399);
 -webkit-background-clip:text;background-clip:text;color:transparent}
.sub{color:var(--muted);margin:14px 0 26px;max-width:620px;font-size:15.5px}

/* metric tiles */
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:22px}
.tile{background:linear-gradient(180deg,var(--card2),var(--card));
 border:1px solid var(--line2);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}
.t-val{font-size:30px;font-weight:800;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.t-val.good{color:var(--good)}
.t-lab{color:var(--muted);font-size:12.5px;margin-top:3px;line-height:1.35}

/* callouts */
.callouts{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.callout{background:var(--card);border:1px solid var(--line);border-radius:14px;
 padding:14px 16px;border-left:3px solid var(--accent)}
.co-tag{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
 color:var(--accent)}
.co-title{font-size:16.5px;font-weight:700;margin:4px 0 4px}
.co-body{color:var(--muted);font-size:13px}

/* sticky nav */
.nav{position:sticky;top:0;z-index:20;background:rgba(10,14,20,.82);
 backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.nav-in{display:flex;align-items:center;justify-content:space-between;gap:14px;
 padding-top:10px;padding-bottom:10px;flex-wrap:wrap}
.filters{display:flex;gap:4px;background:var(--card);border:1px solid var(--line2);
 border-radius:10px;padding:3px}
.f-btn{appearance:none;border:0;background:transparent;color:var(--muted);
 font:inherit;font-size:13px;font-weight:600;padding:6px 13px;border-radius:7px;
 cursor:pointer}
.f-btn.active{background:var(--accent);color:#06101f}
.pills{display:flex;gap:5px;flex-wrap:wrap}
.pill{width:27px;height:27px;display:grid;place-items:center;border-radius:7px;
 background:var(--card);border:1px solid var(--line2);color:var(--muted);
 font-size:12.5px;font-weight:700;text-decoration:none}
.pill:hover,.pill.active{background:var(--accent);color:#06101f;border-color:var(--accent)}

main{padding:24px 0 70px}
.legend{color:var(--muted);font-size:12.5px;margin:6px 0 18px}
.legend i{font-style:normal;font-weight:700}
.legend .lh{color:var(--home)}.legend .ld{color:var(--draw)}.legend .la{color:var(--away)}
.sw-mode,.sw-actual{display:inline-block;width:11px;height:11px;border-radius:3px;
 vertical-align:-1px}
.sw-mode{border:1.5px solid #cfe;background:rgba(96,165,250,.25)}
.sw-actual{box-shadow:0 0 0 1.5px var(--home) inset;background:transparent}

/* group */
.group{margin:22px 0}
.g-head{display:flex;align-items:center;gap:8px;cursor:pointer;
 border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:14px}
.g-head h2{font-size:19px;margin:0;font-weight:700}
.g-toggle{color:var(--muted);transition:transform .2s;margin-left:2px}
.group.collapsed .g-toggle{transform:rotate(-90deg)}
.group.collapsed .g-body{display:none}

/* group forecast (chance to advance) */
.gforecast{background:var(--card);border:1px solid var(--line);border-radius:12px;
 padding:12px 14px 8px;margin-bottom:16px}
.gf-head{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;
 gap:6px;font-weight:700;font-size:13.5px;margin-bottom:8px}
.gf-note{color:var(--faint);font-size:11px;font-weight:500;letter-spacing:.01em}
.gf-colhead,.gf-row{display:grid;grid-template-columns:1fr 150px 40px;align-items:center;gap:12px}
.gf-colhead{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em;
 margin-bottom:5px}
.gf-colhead span{text-align:right}
.gf-row{padding:4px 0;font-size:13px}
.gf-team{display:flex;align-items:baseline;gap:7px;font-weight:600;min-width:0;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gf-pts{color:var(--faint);font-size:11px;font-weight:500}
.gf-track{position:relative;height:18px;background:var(--bg2);border:1px solid var(--line);
 border-radius:5px;overflow:hidden}
.gf-fill{position:absolute;left:0;top:0;bottom:0;border-radius:5px 0 0 5px}
.gf-fill.hi{background:linear-gradient(90deg,rgba(52,211,153,.45),rgba(52,211,153,.9))}
.gf-fill.mid{background:linear-gradient(90deg,rgba(96,165,250,.4),rgba(96,165,250,.8))}
.gf-fill.lo{background:linear-gradient(90deg,rgba(138,151,166,.3),rgba(138,151,166,.55))}
.gf-adv{position:absolute;right:6px;top:50%;transform:translateY(-50%);font-size:11px;
 font-weight:700;font-variant-numeric:tabular-nums}
.gf-win{text-align:right;color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}

/* match cards */
.cards{display:grid;grid-template-columns:repeat(2,1fr);gap:13px}
.match{background:linear-gradient(180deg,var(--card2),var(--card));
 border:1px solid var(--line);border-radius:14px;padding:15px 16px;
 transition:border-color .15s,transform .15s}
.match:hover{border-color:var(--line2);transform:translateY(-2px)}
.match[data-state='upcoming']{border-left:3px solid var(--accent)}
.match[data-state='played']{border-left:3px solid var(--line2)}
.m-top{display:flex;justify-content:space-between;align-items:baseline;gap:10px;
 margin-bottom:10px}
.teams{font-weight:700;font-size:15.5px}
.vs{color:var(--muted);font-weight:500;font-size:12px}
.meta{color:var(--muted);font-size:12px;white-space:nowrap}
.bar{display:flex;height:24px;border-radius:7px;overflow:hidden;font-size:11.5px;
 font-weight:700;margin-bottom:12px}
.seg{display:flex;align-items:center;justify-content:center;color:#06101f;
 min-width:0;overflow:hidden;white-space:nowrap}
.seg.h{background:var(--home)}.seg.d{background:var(--draw)}.seg.a{background:var(--away)}
.m-body{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.m-left{min-width:0}
.headline{margin-bottom:8px}
.score{font-size:26px;font-weight:800;letter-spacing:-.01em;font-variant-numeric:tabular-nums}
.score.pred{color:var(--accent)}
.hl-sub{display:block;color:var(--muted);font-size:12px;margin-top:1px}
.chip{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;
 font-weight:700}
.c-strong{background:rgba(52,211,153,.16);color:var(--home)}
.c-lean{background:rgba(251,191,36,.16);color:var(--draw)}
.c-open{background:rgba(138,151,166,.16);color:var(--muted)}
.row{display:flex;flex-wrap:wrap;gap:6px 14px;color:var(--muted);font-size:12.5px;
 align-items:center}
.row b{color:var(--ink)}
.venue{color:var(--faint)}
.tone{font-size:11px;font-weight:700;color:var(--accent);background:rgba(96,165,250,.12);
 padding:1px 8px;border-radius:20px}
.goals{display:flex;flex-wrap:wrap;gap:4px 12px;color:var(--muted);font-size:11.5px;
 margin-top:6px}
.goals b{color:var(--ink);font-variant-numeric:tabular-nums}

/* draw-paradox info marker */
.info{display:inline-block;margin-left:6px;color:var(--accent);cursor:help;
 font-size:14px;vertical-align:2px;font-weight:700}
.info:hover,.info:focus{color:#bfe3ff;outline:none}

/* team-strength insight section */
.insight{margin:18px 0 6px}
.insight .g-head{margin-bottom:0}
.insight.collapsed .insight-body{display:none}
.insight-sub{color:var(--muted);font-size:12.5px;margin:12px 0 14px;max-width:760px}
.lbl-atk{color:var(--home)}.lbl-def{color:var(--accent)}
.st-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:4px 26px}
.st-row{display:grid;grid-template-columns:20px 1fr 96px;align-items:center;gap:9px;
 padding:3px 0;font-size:12.5px}
.st-rank{color:var(--faint);font-size:11px;text-align:right;font-variant-numeric:tabular-nums}
.st-team{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.st-bars{display:flex;flex-direction:column;gap:3px}
.st-bar{height:5px;background:var(--bg2);border-radius:3px;overflow:hidden}
.st-fill{display:block;height:100%;border-radius:3px}
.st-fill.atk{background:var(--home)}
.st-fill.def{background:var(--accent)}

/* title odds (championship probabilities) */
.titleodds{margin:18px 0 6px}
.titleodds .g-head{margin-bottom:0}
.titleodds.collapsed .to-body{display:none}
.to-lead{color:var(--muted);font-size:13px;margin:12px 0 14px;max-width:780px}
.to-lead b{color:var(--ink)}
.to-bars{display:block;margin-top:4px;color:var(--faint);font-size:12px}
.to-grid{display:flex;flex-direction:column;gap:3px}
.to-row{display:grid;grid-template-columns:24px minmax(110px,1.1fr) 2fr 44px 52px;
 align-items:center;gap:10px;font-size:13px;padding:2px 0}
.to-rank{color:var(--faint);font-size:11px;text-align:right;font-variant-numeric:tabular-nums}
.to-team{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.to-track{position:relative;height:18px;background:var(--bg2);border:1px solid var(--line);
 border-radius:5px;overflow:hidden}
.to-fill{position:absolute;left:0;top:0;bottom:0;border-radius:5px 0 0 5px;
 background:linear-gradient(90deg,rgba(96,165,250,.5),rgba(52,211,153,.9))}
.to-val{position:absolute;right:7px;top:50%;transform:translateY(-50%);font-size:11px;
 font-weight:700;font-variant-numeric:tabular-nums}
.to-sub{color:var(--muted);font-size:11.5px;text-align:right;font-variant-numeric:tabular-nums}

/* search box + states */
.search{appearance:none;background:var(--card);border:1px solid var(--line2);
 color:var(--ink);font:inherit;font-size:13px;padding:7px 12px;border-radius:9px;
 width:180px;outline:none}
.search:focus{border-color:var(--accent)}
.search::placeholder{color:var(--faint)}
.match.search-hide{display:none}
.group.search-empty,.chrono.search-empty{display:none}
body.searching .gforecast,body.searching .insight{display:none}
.no-results{display:none;color:var(--muted);text-align:center;padding:30px;font-size:14px}
body.searching.no-hits .no-results{display:block}

/* custom heatmap tooltip */
.tip{position:fixed;z-index:50;pointer-events:none;opacity:0;transition:opacity .08s;
 background:#06101f;color:var(--ink);border:1px solid var(--line2);border-radius:8px;
 padding:5px 9px;font-size:12px;font-weight:600;box-shadow:var(--shadow);white-space:nowrap}
.tip.on{opacity:1}
.tip .tip-p{color:var(--accent)}

/* heatmap — SVG-based; replaces old div-grid */
.hm{width:152px;height:auto;flex:none;display:block}
.hm rect{stroke-linejoin:round}
.hm-lbl{fill:var(--muted);font-variant-numeric:tabular-nums}
.hm-corner-lbl{fill:var(--faint)}

/* skip card */
.match.skip{border-left:3px dashed var(--line2);background:var(--card)}
.skip-note{color:var(--muted);font-size:12.5px}

footer{color:var(--faint);font-size:11.5px;margin-top:34px;border-top:1px solid var(--line);
 padding-top:16px;line-height:1.5}

/* chronological flat views (Upcoming + Results): each replaces the grouped
   sections under its own filter. The All tab keeps the grouped view + pills. */
.chrono{display:none}
body[data-filter='upcoming'] .chrono-up{display:block}
body[data-filter='played'] .chrono-res{display:block}
body[data-filter='upcoming'] section.group,
body[data-filter='played'] section.group{display:none}
body[data-filter='upcoming'] .pills,
body[data-filter='played'] .pills{display:none}
.chrono-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
 border-bottom:1px solid var(--line);padding-bottom:8px;margin:6px 0 4px}
.chrono-head h2{font-size:19px;margin:0;font-weight:700}
.chrono-sub{color:var(--faint);font-size:12px}
.chrono-day{font-size:12px;font-weight:700;color:var(--accent);text-transform:uppercase;
 letter-spacing:.06em;margin:18px 0 10px}
.chrono-empty{color:var(--muted);font-size:14px;padding:20px 0}

/* knockout bracket */
.bracket{display:none}
body[data-filter='bracket'] .bracket{display:block}
body[data-filter='bracket'] section.group,body[data-filter='bracket'] .chrono,
body[data-filter='bracket'] .titleodds,body[data-filter='bracket'] .insight,
body[data-filter='bracket'] .legend,body[data-filter='bracket'] .pills,
body[data-filter='bracket'] .search,body[data-filter='bracket'] .no-results{display:none}
.bk-head h2{font-size:23px;margin:6px 0 6px}
.bk-lead{color:var(--muted);font-size:13.5px;max-width:760px;margin:0 0 18px}
.bk-lead b{color:var(--ink)}.bk-proj-lbl{color:var(--accent)}
.bk-scroll{display:flex;gap:14px;overflow-x:auto;padding-bottom:14px;align-items:stretch}
.bk-col{flex:0 0 196px;display:flex;flex-direction:column;gap:12px;
 justify-content:space-around}
.bk-col-h{font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
 color:var(--accent);position:sticky;top:54px;z-index:5;background:var(--bg);
 padding:8px 2px 6px;margin:0 -2px}
.bk-match{background:linear-gradient(180deg,var(--card2),var(--card));
 border:1px solid var(--line);border-radius:10px;padding:4px;display:flex;
 flex-direction:column;gap:3px}
.bk-team{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;
 gap:2px;padding:6px 9px;border-radius:7px;font-size:12.5px;min-height:46px;
 box-sizing:border-box}
.bk-src{font-size:10.5px;color:var(--faint);font-weight:600;text-transform:uppercase;
 letter-spacing:.04em;white-space:nowrap;line-height:1.2}
.bk-val{display:flex;align-items:center;justify-content:space-between;gap:6px;width:100%;
 min-height:18px;line-height:1.2}
.bk-team.empty{color:var(--faint)}
.bk-team.empty .bk-val{color:var(--faint);opacity:.6}
.bk-team.proj .bk-proj{display:flex;align-items:center;gap:5px;font-weight:600;color:var(--ink)}
.bk-pp{color:var(--muted);font-size:10.5px;font-weight:600;margin-left:2px}
.bk-team.real{background:var(--bg2);font-weight:600}
.bk-name{display:flex;align-items:center;gap:6px;min-width:0;overflow:hidden;
 text-overflow:ellipsis;white-space:nowrap}
.bk-wp{color:var(--muted);font-size:11px;font-variant-numeric:tabular-nums;flex:0 0 auto}
.bk-score{text-align:center;font-weight:800;font-size:14px;color:var(--accent);
 font-variant-numeric:tabular-nums;padding:1px 0 3px}

/* model vs market tab */
.market{display:none}
body[data-filter='market'] .market{display:block}
body[data-filter='market'] section.group,body[data-filter='market'] .chrono,
body[data-filter='market'] .bracket,body[data-filter='market'] .titleodds,
body[data-filter='market'] .insight,body[data-filter='market'] .legend,
body[data-filter='market'] .pills,body[data-filter='market'] .search,
body[data-filter='market'] .no-results{display:none}
.mk-head h2{font-size:23px;margin:6px 0 6px}
.mk-lead{color:var(--muted);max-width:680px;font-size:14px}
.mk-disclaimer{background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.28);
 border-left:3px solid var(--draw);border-radius:12px;padding:13px 16px;font-size:13px;
 color:var(--muted);max-width:880px;margin:4px 0 16px;line-height:1.55}
.mk-disclaimer b{color:var(--ink)}
.mk-controls{display:flex;align-items:center;gap:14px;margin-bottom:6px;flex-wrap:wrap}
.mk-asof{color:var(--muted);font-size:12.5px}.mk-asof b{color:var(--ink)}
.mk-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-left:7px;
 background:var(--faint);vertical-align:1px}
.mk-dot.live{background:var(--home);box-shadow:0 0 0 3px rgba(52,211,153,.18)}
.mk-dot.stale{background:var(--draw)}
.mk-refresh{appearance:none;border:1px solid var(--line2);background:var(--card);
 color:var(--ink);font:inherit;font-size:12.5px;font-weight:600;padding:6px 13px;
 border-radius:9px;cursor:pointer}
.mk-refresh:hover{border-color:var(--accent)}
.mk-refresh:disabled,.mk-refresh.loading{opacity:.5;cursor:wait}
.mk-status{color:var(--faint);font-size:12px;min-height:16px;margin:2px 0 6px}
.mk-h3{font-size:15.5px;margin:22px 0 8px;display:flex;align-items:baseline;gap:10px;
 flex-wrap:wrap}
.mk-sub{color:var(--faint);font-size:11.5px;font-weight:500}
.mk-tablewrap{overflow-x:auto}
.mk-table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:540px}
.mk-table th{color:var(--muted);font-weight:600;text-align:right;padding:7px 8px;
 font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;
 border-bottom:1px solid var(--line)}
.mk-table th.tl,.mk-table td.tl{text-align:left}
.mk-table td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--line);
 font-variant-numeric:tabular-nums}
.mk-match{font-weight:600;color:var(--ink)}
.mk-table tr.mk-muted td{color:var(--faint);opacity:.55}
.mk-table tr.mk-big td{background:rgba(96,165,250,.07)}
.mk-pos{color:var(--home);font-weight:700}
.mk-neg{color:var(--away);font-weight:700}
.mk-foot{color:var(--faint);font-size:11.5px;margin-top:16px;border-top:1px solid var(--line);
 padding-top:12px;line-height:1.55;max-width:880px}
.mk-empty{color:var(--muted);font-size:13px}
/* sortable market headers */
.mk-sortable th[data-key]{cursor:pointer;user-select:none;position:relative;
 padding-right:15px;white-space:nowrap}
.mk-sortable th[data-key]:hover{color:var(--ink)}
.mk-sortable th[data-key]::after{content:'';position:absolute;right:5px;top:50%;
 transform:translateY(-50%);border-left:3px solid transparent;border-right:3px solid transparent;
 opacity:0;transition:opacity .12s}
.mk-sortable th.mk-sorted-asc::after{opacity:.9;border-bottom:4px solid var(--accent)}
.mk-sortable th.mk-sorted-desc::after{opacity:.9;border-top:4px solid var(--accent)}
.mk-sortable th.mk-sorted-asc,.mk-sortable th.mk-sorted-desc{color:var(--ink)}

/* per-card Model-vs-Market expander */
.mvm{margin-top:11px;border-top:1px solid var(--line);padding-top:9px}
.mvm-toggle{appearance:none;border:0;background:transparent;color:var(--accent);
 font:inherit;font-size:12px;font-weight:700;letter-spacing:.02em;padding:0;
 cursor:pointer;display:flex;align-items:center;gap:6px}
.mvm-toggle:hover{color:#bfe3ff}
.mvm-caret{display:inline-block;transition:transform .2s;font-size:10px}
.mvm.open .mvm-caret{transform:rotate(180deg)}
.mvm-body{display:none;margin-top:9px}
.mvm.open .mvm-body{display:block}
.mvm-rows{display:flex;flex-direction:column;gap:2px}
.mvm-line{display:grid;grid-template-columns:1fr 46px 46px 46px;align-items:center;
 gap:8px;font-size:12px;padding:2px 0;font-variant-numeric:tabular-nums}
.mvm-colhead{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.05em}
.mvm-line span:not(.mvm-out){text-align:right}
.mvm-out{color:var(--ink);font-weight:600}
.mvm-line .mvm-pos{color:var(--home);font-weight:700}
.mvm-line .mvm-neg{color:var(--away);font-weight:700}
.mvm-note{color:var(--faint);font-size:10.5px;margin-top:7px;line-height:1.45}
.mvm-loading{color:var(--muted);font-size:12px;padding:4px 0}

/* method tab */
.method{display:none}
body[data-filter='method'] .method{display:block}
body[data-filter='method'] section.group,
body[data-filter='method'] .chrono,
body[data-filter='method'] .bracket,
body[data-filter='method'] .market,
body[data-filter='method'] .insight,
body[data-filter='method'] .titleodds,
body[data-filter='method'] .legend,
body[data-filter='method'] .no-results,
body[data-filter='method'] .pills,
body[data-filter='method'] .search{display:none}
/* title odds + strength are tournament-level: show only in the All view */
body[data-filter='upcoming'] .titleodds,body[data-filter='played'] .titleodds,
body[data-filter='upcoming'] .insight,body[data-filter='played'] .insight,
body[data-filter='bracket'] .titleodds,body[data-filter='bracket'] .insight,
body.searching .titleodds,body.searching .insight{display:none}
.method h2{font-size:23px;margin:6px 0 6px}
.m-lead{color:var(--muted);max-width:680px;margin:0 0 20px;font-size:15px}
.m-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.m-card{background:linear-gradient(180deg,var(--card2),var(--card));
 border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.m-card h3{margin:0 0 8px;font-size:15.5px}
.m-card p{color:var(--muted);font-size:13.5px;margin:8px 0}
.m-card b{color:var(--ink)}
.m-card a{color:var(--accent)}
.m-eq{background:#0a0e14;border:1px solid var(--line);border-radius:8px;padding:10px 12px;
 font-size:11.5px;color:var(--ink);overflow-x:auto;white-space:pre;line-height:1.6}
.m-warn{border-left:3px solid var(--draw);padding-left:10px}
.m-list{color:var(--muted);font-size:13.5px;margin:8px 0;padding-left:18px}
.m-list li{margin:4px 0}.m-list b{color:var(--ink)}
.m-note{color:var(--faint);font-size:12px;margin-top:8px}
.m-foot{color:var(--faint);font-size:12.5px;margin-top:18px;border-top:1px solid var(--line);
 padding-top:14px}
.mtable{width:100%;border-collapse:collapse;margin:10px 0 4px;font-size:12.5px}
.mtable th{color:var(--muted);font-weight:600;text-align:center;padding:6px 5px;
 font-size:11px;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--line)}
.mtable td{text-align:center;padding:6px 5px;border-bottom:1px solid var(--line);
 font-variant-numeric:tabular-nums}
.mtable .tl{text-align:left}

@media(max-width:760px){
 .tiles{grid-template-columns:repeat(2,1fr)}
 .callouts{grid-template-columns:1fr}
 .cards{grid-template-columns:1fr}
 .st-grid{grid-template-columns:1fr}
 .m-grid{grid-template-columns:1fr}
 .search{width:100%;order:3}
 .to-row{grid-template-columns:20px minmax(78px,1fr) 1.5fr 42px;gap:7px}
 .to-row .to-sub:last-child{display:none}
}
"""

_JS = """
function setFilter(f,btn){
  document.body.setAttribute('data-filter',f);
  document.querySelectorAll('.f-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
}
function toggleGroup(g){
  document.getElementById('grp-'+g).classList.toggle('collapsed');
}
function toggleInsight(){
  document.getElementById('insight').classList.toggle('collapsed');
}
function toggleTitle(){
  document.getElementById('titleodds').classList.toggle('collapsed');
}
function toggleExpander(btn){
  var box=btn.closest('.mvm');
  box.classList.toggle('open');
  // On first open, ensure the shared live odds fetch has run (same data the
  // Model-vs-Market tab uses).
  if(box.classList.contains('open') && window.mvmEnsureFetch){ window.mvmEnsureFetch(); }
}
// Team search: filter match cards across groups + chrono, hide empty sections.
function searchTeams(q){
  q=q.trim().toLowerCase();
  document.body.classList.toggle('searching', q.length>0);
  document.querySelectorAll('.match').forEach(m=>{
    const hit = !q || (m.dataset.teams||'').indexOf(q)>=0;
    m.classList.toggle('search-hide', !hit);
  });
  let anyGlobal=false;
  document.querySelectorAll('section.group, section.chrono').forEach(s=>{
    const any=[...s.querySelectorAll('.match')].some(m=>!m.classList.contains('search-hide'));
    s.classList.toggle('search-empty', q && !any);
    if(any) anyGlobal=true;
  });
  document.body.classList.toggle('no-hits', q.length>0 && !anyGlobal);
}
// active pill on scroll
const pills=[...document.querySelectorAll('.pill')];
const obs=new IntersectionObserver((es)=>{
  es.forEach(e=>{if(e.isIntersecting){
    const id=e.target.id.replace('grp-','');
    pills.forEach(p=>p.classList.toggle('active',p.getAttribute('href')==='#grp-'+id));
  }});
},{rootMargin:'-45% 0px -50% 0px'});
document.querySelectorAll('section.group').forEach(s=>obs.observe(s));
// custom heatmap tooltip (instant, mobile-friendly fallback keeps native title)
const tip=document.getElementById('tip');
function moveTip(e){ tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY+14)+'px'; }
document.addEventListener('mouseover',e=>{
  const c=e.target.closest('[data-s]'); if(!c) return;
  tip.innerHTML="<span class='tip-s'>"+c.dataset.s+"</span> &middot; <span class='tip-p'>"+c.dataset.p+"</span>";
  tip.classList.add('on'); moveTip(e);
});
document.addEventListener('mousemove',e=>{ if(tip.classList.contains('on')) moveTip(e); });
document.addEventListener('mouseout',e=>{ if(e.target.closest('[data-s]')) tip.classList.remove('on'); });
"""


# Live "Model vs Market" logic. Reads the baked window.POLY (model probs +
# resolved Polymarket slugs/market-ids + a price snapshot), fetches live prices
# from the keyless Gamma API in the browser, de-vigs, computes edges, and fills
# the two tables. No matching logic here — that was resolved at build time.
_MARKET_JS = r"""
(function(){
  var P = window.POLY;
  var rowsEl = document.getElementById('mk-rows');
  if(!P || !rowsEl){ return; }
  var asofEl=document.getElementById('mk-asof'), dotEl=document.getElementById('mk-dot'),
      statusEl=document.getElementById('mk-status'), titleEl=document.getElementById('mk-title'),
      emptyEl=document.getElementById('mk-rows-empty'), btn=document.getElementById('mk-refresh');
  var GAMMA='https://gamma-api.polymarket.com', SERIES=11433,
      VIG_MAX=0.06, MIN_VOL=20000, P_FLOOR=0.05, INTERVAL=600000;
  // sort state + last-rendered rows, so header clicks re-sort the CURRENT data
  // (live or snapshot) without refetching. Defaults match the initial order.
  var lastMatchRows=[], matchSort={key:'edge', dir:-1};
  var lastTitleRows=[], titleSort={key:'mkt', dir:-1};
  var warmed=false;
  // index POLY matches by the card key (data-teams = "home away", lowercased)
  var matchByKey={};
  if(P.matches){ P.matches.forEach(function(m){ matchByKey[(m.home+' '+m.away).toLowerCase()]=m; }); }

  function pct(x){ return (x*100).toFixed(0)+'%'; }
  function pct1(x){ return (x*100).toFixed(1)+'%'; }
  function pp(x){ var v=x*100; return (v>=0?'+':'')+v.toFixed(1); }
  function evfmt(m,k){ if(k<P_FLOOR) return '—'; var ev=m/k-1; return (ev>=0?'+':'')+(ev*100).toFixed(0)+'%'; }
  function jp(s){ try{ return typeof s==='string'?JSON.parse(s):s; }catch(e){ return null; } }
  function esc(s){ return String(s).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];}); }
  function volfmt(v){ if(v>=1e6) return '$'+(v/1e6).toFixed(1)+'M'; if(v>=1e3) return '$'+(v/1e3).toFixed(0)+'K'; return '$'+(v||0).toFixed(0); }
  function devig(arr){ var s=arr.reduce(function(a,b){return a+b;},0)||1; return {p:arr.map(function(x){return x/s;}), vig:s-1}; }

  function ft(url){   // fetch with a hard timeout so one slow endpoint can't hang the UI
    var c=new AbortController(), t=setTimeout(function(){ c.abort(); }, 15000);
    return fetch(url,{signal:c.signal}).then(function(r){ clearTimeout(t); return r; });
  }
  function fetchLive(){
    // Fetch ONLY the baked slugs (indexed lookups are fast; the series-listing
    // query can be very slow). Batch to keep URLs short; run batches in parallel.
    var slugs=[];
    P.matches.forEach(function(m){ slugs.push(m.slug); if(m.moreSlug) slugs.push(m.moreSlug); });
    var bySlug={}, reqs=[];
    for(var i=0;i<slugs.length;i+=15){
      var qs=slugs.slice(i,i+15).map(function(s){ return 'slug='+encodeURIComponent(s); }).join('&');
      reqs.push(ft(GAMMA+'/events?'+qs)
        .then(function(r){ return r.ok?r.json():[]; })
        // keep OPEN events only: a since-kicked-off match returns a settled
        // 0/1 event whose "odds" would be a bogus comparison.
        .then(function(arr){ (arr||[]).forEach(function(e){ if(e && !e.closed) bySlug[e.slug]=e; }); })
        .catch(function(){}));
    }
    var winnerP=ft(GAMMA+'/events?slug='+encodeURIComponent(P.title.slug))
      .then(function(r){ return r.ok?r.json():null; })
      .then(function(a){ return a&&a[0]; }).catch(function(){ return null; });
    return Promise.all(reqs.concat([winnerP])).then(function(res){
      return {bySlug:bySlug, winner:res[res.length-1]};
    });
  }

  function liveMatchPrices(m, bySlug){
    var ev=bySlug[m.slug]; if(!ev||!ev.markets) return null;
    var h=null,d=null,a=null;
    ev.markets.forEach(function(mk){
      var g=mk.groupItemTitle||'', pr=jp(mk.outcomePrices); if(!pr) return;
      if(g===m.homeGit) h=+pr[0]; else if(g===m.drawGit) d=+pr[0]; else if(g===m.awayGit) a=+pr[0];
    });
    if(h==null||d==null||a==null) return null;
    var out={h:h,d:d,a:a,btts:null,o25:null};
    if(m.moreSlug && bySlug[m.moreSlug] && bySlug[m.moreSlug].markets){
      bySlug[m.moreSlug].markets.forEach(function(mk){
        var q=mk.question||'', pr=jp(mk.outcomePrices); if(!pr) return;
        if(q===m.bttsQ) out.btts=[+pr[0],+pr[1]]; else if(q===m.o25Q) out.o25=[+pr[0],+pr[1]];
      });
    }
    return out;
  }
  function snapMatch(m){
    var s=m.snap; if(s.h==null||s.d==null||s.a==null) return null;
    return {h:s.h,d:s.d,a:s.a, btts:(s.btts!=null?[s.btts,1-s.btts]:null), o25:(s.o25!=null?[s.o25,1-s.o25]:null)};
  }

  function buildMatchRows(get){
    var rows=[];
    P.matches.forEach(function(m){
      var pr=get(m); if(!pr) return;
      var dv=devig([pr.h,pr.d,pr.a]), pm=dv.p, vig=dv.vig;
      var lowvol=m.vol<MIN_VOL, hivig=Math.abs(vig)>VIG_MAX, name=m.home+' v '+m.away;
      [['Home',m.model.h,pm[0]],['Draw',m.model.d,pm[1]],['Away',m.model.a,pm[2]]].forEach(function(o){
        rows.push({match:name,out:o[0],model:o[1],mkt:o[2],vig:vig,vol:m.vol,lowvol:lowvol,hivig:hivig,edge:o[1]-o[2]});
      });
      if(pr.btts){ var bs=pr.btts[0]+pr.btts[1], b=pr.btts[0]/(bs||1);
        rows.push({match:name,out:'BTTS',model:m.model.btts,mkt:b,vig:bs-1,vol:m.vol,lowvol:lowvol,hivig:Math.abs(bs-1)>VIG_MAX,edge:m.model.btts-b}); }
      if(pr.o25){ var os=pr.o25[0]+pr.o25[1], ov=pr.o25[0]/(os||1);
        rows.push({match:name,out:'Over 2.5',model:m.model.o25,mkt:ov,vig:os-1,vol:m.vol,lowvol:lowvol,hivig:Math.abs(os-1)>VIG_MAX,edge:m.model.o25-ov}); }
    });
    rows.sort(function(x,y){ return Math.abs(y.edge)-Math.abs(x.edge); });
    return rows;
  }
  function renderMatchRows(rows){
    lastMatchRows=rows;                       // cache for header re-sort
    rows=sortRows(rows.slice(), matchSort);   // apply current sort
    if(!rows.length){ rowsEl.innerHTML=''; if(emptyEl) emptyEl.style.display='block'; return; }
    if(emptyEl) emptyEl.style.display='none';
    rowsEl.innerHTML=rows.map(function(r){
      var cls=((r.lowvol||r.hivig)?' mk-muted':'')+(Math.abs(r.edge)>=0.08?' mk-big':'');
      return "<tr class='"+cls+"'><td class='tl mk-match'>"+esc(r.match)+"</td><td class='tl'>"+r.out+"</td>"
        +"<td>"+pct(r.model)+"</td><td>"+pct(r.mkt)+"</td>"
        +"<td class='"+(r.edge>=0?'mk-pos':'mk-neg')+"'>"+pp(r.edge)+"</td>"
        +"<td>"+evfmt(r.model,r.mkt)+"</td><td>"+(r.vig*100).toFixed(1)+"%</td><td>"+volfmt(r.vol)+"</td></tr>";
    }).join('');
  }
  function buildTitleRows(get){
    var rows=[];
    P.title.teams.forEach(function(t){ var mp=get(t); if(mp==null) return; rows.push({team:t.team,model:t.model,mkt:mp,edge:t.model-mp}); });
    rows.sort(function(x,y){ return y.mkt-x.mkt; });
    return rows;
  }
  function renderTitleRows(rows){
    lastTitleRows=rows;                        // cache for header re-sort
    rows=sortRows(rows.slice(), titleSort);
    titleEl.innerHTML=rows.map(function(r){
      return "<tr><td class='tl mk-match'>"+esc(r.team)+"</td><td>"+pct1(r.model)+"</td><td>"+pct1(r.mkt)
        +"</td><td class='"+(r.edge>=0?'mk-pos':'mk-neg')+"'>"+pp(r.edge)+"</td></tr>";
    }).join('');
  }

  // --- sorting (Feature: clickable headers) ------------------------------
  function sortVal(r,key){
    if(key==='edge') return Math.abs(r.edge);          // |edge| keeps "biggest gap" intent
    if(key==='ev')   return (r.mkt<P_FLOOR? -Infinity : r.model/r.mkt-1);
    var v=r[key];
    return typeof v==='string'? v.toLowerCase() : v;
  }
  function sortRows(rows,st){
    rows.sort(function(a,b){ var x=sortVal(a,st.key), y=sortVal(b,st.key);
      return x<y? -st.dir : (x>y? st.dir : 0); });
    return rows;
  }
  function markHeader(th,dir){
    var tr=th.parentNode;
    [].forEach.call(tr.children,function(h){ h.classList.remove('mk-sorted-asc','mk-sorted-desc'); });
    th.classList.add(dir>0?'mk-sorted-asc':'mk-sorted-desc');
  }
  function mvmSort(th){ var key=th.dataset.key;
    matchSort.dir=(matchSort.key===key)? -matchSort.dir : ((key==='match'||key==='out')?1:-1);
    matchSort.key=key; markHeader(th, matchSort.dir); renderMatchRows(lastMatchRows);
  }
  function mvmSortT(th){ var key=th.dataset.key;
    titleSort.dir=(titleSort.key===key)? -titleSort.dir : (key==='team'?1:-1);
    titleSort.key=key; markHeader(th, titleSort.dir); renderTitleRows(lastTitleRows);
  }
  window.mvmSort=mvmSort; window.mvmSortT=mvmSortT;

  // --- per-card expanders (Feature: fill from the SAME fetch) -------------
  function mvmFillCards(get){
    document.querySelectorAll('.match[data-state="upcoming"] .mvm').forEach(function(box){
      var card=box.closest('.match'), m=matchByKey[card.dataset.teams||''];
      if(!m) return;                                   // no odds -> stays hidden
      box.hidden=false;                                // odds exist -> reveal toggle
      var pr=get(m), rEl=box.querySelector('.mvm-rows'), nEl=box.querySelector('.mvm-note');
      if(!pr){ rEl.innerHTML="<div class='mvm-loading'>Live odds unavailable.</div>"; nEl.textContent=''; return; }
      var dv=devig([pr.h,pr.d,pr.a]), pm=dv.p;
      var lines=[['Home',m.model.h,pm[0]],['Draw',m.model.d,pm[1]],['Away',m.model.a,pm[2]]];
      if(pr.btts){ var bs=pr.btts[0]+pr.btts[1]; lines.push(['BTTS',m.model.btts,pr.btts[0]/(bs||1)]); }
      if(pr.o25){ var os=pr.o25[0]+pr.o25[1]; lines.push(['Over 2.5',m.model.o25,pr.o25[0]/(os||1)]); }
      var head="<div class='mvm-line mvm-colhead'><span class='mvm-out'>Outcome</span>"
        +"<span>Model</span><span>Market</span><span>Edge</span></div>";
      rEl.innerHTML=head+lines.map(function(o){ var edge=o[1]-o[2];
        return "<div class='mvm-line'><span class='mvm-out'>"+o[0]+"</span><span>"+pct(o[1])+"</span><span>"
          +pct(o[2])+"</span><span class='"+(edge>=0?'mvm-pos':'mvm-neg')+"'>"+pp(edge)+"</span></div>";
      }).join('');
      nEl.innerHTML="Vig "+(dv.vig*100).toFixed(1)+"% &middot; vol "+volfmt(m.vol)
        +". Model &minus; market in pts. Divergence is not value.";
    });
  }

  function renderSnapshot(){
    renderMatchRows(buildMatchRows(snapMatch));
    renderTitleRows(buildTitleRows(function(t){ return t.snap!=null? t.snap/(P.title.sum||1):null; }));
    mvmFillCards(snapMatch);                  // fill card expanders from snapshot
    if(asofEl) asofEl.textContent=P.asof+' (snapshot)';
    if(dotEl) dotEl.className='mk-dot stale';
  }
  function renderLive(live){
    // Wholesale fetch failure (network / CORS / all batches timed out): keep
    // whatever is already painted (the snapshot or last good live data) rather
    // than wiping the tables + cards with empty "live" results.
    if(!Object.keys(live.bySlug).length && !live.winner){
      if(statusEl) statusEl.textContent='Live odds unavailable right now — showing the last values.';
      if(dotEl) dotEl.className='mk-dot stale';
      return;
    }
    var get=function(m){ return liveMatchPrices(m, live.bySlug); };
    renderMatchRows(buildMatchRows(get));
    var tsum=0, wmap={};
    if(live.winner&&live.winner.markets){ live.winner.markets.forEach(function(mk){ var pr=jp(mk.outcomePrices); if(pr){ wmap[mk.groupItemTitle]=+pr[0]; tsum+=(+pr[0]); } }); }
    renderTitleRows(buildTitleRows(function(t){ var v=wmap[t.git]; return v==null?null:v/(tsum||1); }));
    mvmFillCards(get);                        // fill card expanders from live data
    if(asofEl) asofEl.textContent=new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
    if(dotEl) dotEl.className='mk-dot live';
    if(statusEl) statusEl.textContent='';
  }

  var loading=false;
  function refresh(){
    if(loading) return; loading=true;
    if(btn){ btn.disabled=true; btn.classList.add('loading'); }
    if(statusEl) statusEl.textContent='Fetching live odds…';
    fetchLive().then(renderLive).catch(function(){
      if(statusEl) statusEl.textContent='Live odds unavailable right now — showing the last snapshot.';
      if(dotEl) dotEl.className='mk-dot stale';
    }).then(function(){ loading=false; if(btn){ btn.disabled=false; btn.classList.remove('loading'); } });
  }
  window.refreshMarket=refresh;
  // A card's first expand triggers the SAME shared fetch, once.
  window.mvmEnsureFetch=function(){ if(!warmed){ warmed=true; refresh(); } };

  renderSnapshot();                       // instant, no network; also fills cards
  var mb=document.querySelector("button[data-filter='market']");
  if(mb){ mb.addEventListener('click', function(){ if(!warmed){ warmed=true; refresh(); } }); }
  setInterval(function(){
    if(!document.hidden && document.body.getAttribute('data-filter')==='market') refresh();
  }, INTERVAL);
})();
"""

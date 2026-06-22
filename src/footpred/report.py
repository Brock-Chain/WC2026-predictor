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
from pathlib import Path

import pandas as pd

from .predict import Prediction, predict
from .simulate import simulate_advancement

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
    return FLAGS.get(team, "")


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
    """A color-graded scoreline grid: rows = home goals, cols = away goals."""
    g = p.grid
    n = min(HEAT_N, p.max_goals)
    sub = g[: n + 1, : n + 1]
    vmax = float(sub.max()) or 1.0
    mi, mj, _ = p.top_scorelines(1)[0]

    cells = ["<div class='hm'>"]
    # top-left corner + away-axis header
    cells.append("<div class='hm-corner'>H\\A</div>")
    for j in range(n + 1):
        cells.append(f"<div class='hm-ax'>{j}</div>")
    for i in range(n + 1):
        cells.append(f"<div class='hm-ax'>{i}</div>")
        for j in range(n + 1):
            v = float(g[i, j])
            alpha = (v / vmax) ** 0.6  # gamma for visible low cells
            klass = "hm-c"
            if i == mi and j == mj:
                klass += " hm-mode"
            if actual is not None and (i, j) == actual:
                klass += " hm-actual"
            cells.append(
                f"<div class='{klass}' style='--a:{alpha:.3f}' "
                f"title='{i}–{j}: {_pct(v)}'></div>"
            )
    cells.append("</div>")
    return "".join(cells)


def _match_card(row, pred: Prediction | None) -> str:
    hf, af = _flag(row.home_team), _flag(row.away_team)
    home = f"{hf} {html.escape(row.home_team)}".strip()
    away = f"{html.escape(row.away_team)} {af}".strip()
    date = pd.Timestamp(row.date).strftime("%b %d") if pd.notna(row.date) else ""
    played = bool(getattr(row, "played", False))

    if pred is None:
        return (f"<div class='match skip' data-state='skip'>"
                f"<div class='m-top'><span class='teams'>{home} "
                f"<span class='vs'>v</span> {away}</span>"
                f"<span class='meta'>{date}</span></div>"
                f"<div class='skip-note'>No prediction — a team has "
                f"insufficient recent data (unseen in the 2018+ window).</div>"
                f"</div>")

    mi, mj, mp = pred.top_scorelines(1)[0]
    conf_lbl, conf_cls = _confidence(pred)
    state = "played" if played else "upcoming"
    actual = (int(row.home_score), int(row.away_score)) if played else None

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
                    f"</span><span class='hl-sub'>most likely &middot; {_pct(mp)} "
                    f"&middot; <span class='chip {conf_cls}'>{conf_lbl}</span></span></div>")

    stats = (
        f"<div class='row'>"
        f"<span title='Model-projected goals (Poisson mean), not shot-based xG'>"
        f"Proj. <b>{pred.exp_home_goals:.2f}&#8211;{pred.exp_away_goals:.2f}</b></span>"
        f"<span>Over 2.5 <b>{_pct(pred.p_over_2_5)}</b></span>"
        f"<span class='venue' title='Neutral venue = no home advantage applied'>"
        f"{'Neutral' if pred.neutral else 'Host (home)'}</span>"
        f"</div>"
    )

    return (
        f"<div class='match' data-state='{state}'>"
        f"<div class='m-top'><span class='teams'>{home} "
        f"<span class='vs'>v</span> {away}</span>"
        f"<span class='meta'>{date}</span></div>"
        f"{_bar_html(pred)}"
        f"<div class='m-body'>"
        f"<div class='m-left'>{headline}{stats}</div>"
        f"<div class='m-right'>{_heatmap_html(pred, actual)}</div>"
        f"</div></div>"
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


# --- page assembly ---------------------------------------------------------

def render_report(
    idata,
    fixtures: pd.DataFrame,
    teams: list[str],
    out_path: Path | None = None,
    generated_on: str = "",
    metrics: dict | None = None,
) -> Path:
    out_path = out_path or DEFAULT_OUT
    metrics = {**DEFAULT_METRICS, **(metrics or {})}
    preds = build_predictions(idata, fixtures, teams)
    advancement = simulate_advancement(preds)

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

    # Accuracy on played matches.
    n_played = n_correct = 0
    for row, pred in preds:
        if pred is not None and getattr(row, "played", False):
            n_played += 1
            if _actual_label(int(row.home_score), int(row.away_score)) == _result_label(pred):
                n_correct += 1
    n_upcoming = sum(1 for r, p in preds
                     if p is not None and not getattr(r, "played", False))
    acc_pct = (n_correct / n_played * 100) if n_played else 0

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
        f"<div class='t-lab'>matches still to predict</div></div>"
        f"<div class='tile'><div class='t-val good'>&#10003;</div>"
        f"<div class='t-lab'>{html.escape(metrics['calibration'])}</div></div>"
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
        "</div>"
        f"<div class='pills'>{nav_pills}</div>"
        "</div></nav>"
        "<main class='wrap'>"
        "<div class='legend'>Bars: <i class='lh'>home</i> &middot; "
        "<i class='ld'>draw</i> &middot; <i class='la'>away</i>. "
        "Heatmap rows = home goals, columns = away goals; brighter = more likely, "
        "outlined cell = most-likely score"
        " (<span class='sw-mode'></span>), green ring = actual result"
        " (<span class='sw-actual'></span>).</div>"
        f"{''.join(sections)}"
        "<footer>Double-Poisson with hierarchical attack/defense strengths and "
        "neutral-gated home advantage, fit via MCMC (PyMC/nutpie). "
        "Backtest beats Elo on RPS, log-loss and Brier. "
        "Source: martj42/international_results (CC0). "
        "Knockout fixtures are added once group standings are final.</footer>"
        "</main>"
        f"<script>{_JS}</script>"
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
.row{display:flex;flex-wrap:wrap;gap:10px 14px;color:var(--muted);font-size:12.5px}
.row b{color:var(--ink)}
.venue{color:var(--faint)}

/* heatmap */
.hm{display:grid;grid-template-columns:repeat(8,1fr);gap:2px;width:152px;flex:none}
.hm-corner{font-size:8.5px;color:var(--faint);display:grid;place-items:center}
.hm-ax{font-size:9.5px;color:var(--muted);display:grid;place-items:center;
 font-variant-numeric:tabular-nums}
.hm-c{aspect-ratio:1;border-radius:3px;
 background:rgba(96,165,250,calc(.04 + var(--a)*.96))}
.hm-c.hm-mode{outline:1.5px solid #bfe3ff;outline-offset:-1.5px}
.hm-c.hm-actual{box-shadow:0 0 0 1.5px var(--home) inset}

/* skip card */
.match.skip{border-left:3px dashed var(--line2);background:var(--card)}
.skip-note{color:var(--muted);font-size:12.5px}

footer{color:var(--faint);font-size:11.5px;margin-top:34px;border-top:1px solid var(--line);
 padding-top:16px;line-height:1.5}

/* filter states */
body[data-filter='upcoming'] .match[data-state='played']{display:none}
body[data-filter='played'] .match[data-state='upcoming']{display:none}
body[data-filter='played'] .match[data-state='skip']{display:none}

@media(max-width:760px){
 .tiles{grid-template-columns:repeat(2,1fr)}
 .callouts{grid-template-columns:1fr}
 .cards{grid-template-columns:1fr}
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
// active pill on scroll
const pills=[...document.querySelectorAll('.pill')];
const obs=new IntersectionObserver((es)=>{
  es.forEach(e=>{if(e.isIntersecting){
    const id=e.target.id.replace('grp-','');
    pills.forEach(p=>p.classList.toggle('active',p.getAttribute('href')==='#grp-'+id));
  }});
},{rootMargin:'-45% 0px -50% 0px'});
document.querySelectorAll('section.group').forEach(s=>obs.observe(s));
"""

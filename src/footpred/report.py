"""Phase 6 deliverable: a single self-contained HTML report with predictions
for every WC2026 fixture.

For each fixture we run :func:`footpred.predict.predict` (neutral=True — a
World Cup is at neutral venues for all but the host) and render:
- P(home win / draw / away win) as a stacked bar,
- expected goals, P(over 2.5),
- the most-likely scorelines,
- and for already-played matches, the actual result + whether the model's
  top pick (1X2) was correct.

The output is one ``.html`` file with inline CSS — no external assets — so it
opens anywhere and can be shared as-is.
"""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

from .predict import Prediction, predict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = PROJECT_ROOT / "wc2026_predictions.html"

# Host nations (2026: USA, Canada, Mexico) play at home — not neutral.
HOSTS = {"United States", "Canada", "Mexico"}


def _result_label(p: Prediction) -> str:
    probs = [("home", p.p_home_win), ("draw", p.p_draw), ("away", p.p_away_win)]
    return max(probs, key=lambda x: x[1])[0]


def _actual_label(hg: int, ag: int) -> str:
    return "home" if hg > ag else ("draw" if hg == ag else "away")


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


# --- HTML rendering --------------------------------------------------------

_CSS = """
:root{--bg:#0f1419;--card:#1a212b;--ink:#e6edf3;--muted:#8b98a5;
--home:#3fb950;--draw:#d29922;--away:#f85149;--line:#2d333b;--accent:#58a6ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:30px;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 28px}
h2{font-size:20px;margin:38px 0 14px;border-bottom:1px solid var(--line);
padding-bottom:8px}
.match{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:16px 18px;margin:12px 0}
.mh{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.teams{font-weight:600;font-size:17px}
.meta{color:var(--muted);font-size:13px;white-space:nowrap}
.bar{display:flex;height:26px;border-radius:6px;overflow:hidden;margin:12px 0 8px;
font-size:12px;font-weight:600}
.seg{display:flex;align-items:center;justify-content:center;color:#0b0e13;
min-width:0;overflow:hidden}
.seg.h{background:var(--home)}.seg.d{background:var(--draw)}.seg.a{background:var(--away)}
.row{display:flex;flex-wrap:wrap;gap:18px;color:var(--muted);font-size:13px}
.row b{color:var(--ink)}
.scorelines{margin-top:8px;font-size:13px;color:var(--muted)}
.scorelines span{display:inline-block;background:#0d1117;border:1px solid var(--line);
border-radius:5px;padding:2px 7px;margin:3px 5px 0 0;color:var(--ink)}
.played{margin-top:10px;padding-top:10px;border-top:1px dashed var(--line);font-size:14px}
.ok{color:var(--home);font-weight:600}.miss{color:var(--away);font-weight:600}
.skip{background:var(--card);border:1px dashed var(--line);border-radius:10px;
padding:10px 14px;margin:10px 0;color:var(--muted);font-size:13px}
.legend{color:var(--muted);font-size:13px;margin-bottom:10px}
.legend i{font-style:normal;font-weight:600}
.legend .h{color:var(--home)}.legend .d{color:var(--draw)}.legend .a{color:var(--away)}
footer{color:var(--muted);font-size:12px;margin-top:40px;border-top:1px solid var(--line);
padding-top:16px}
"""


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _match_html(row, pred: Prediction | None) -> str:
    teams = f"{html.escape(row.home_team)} <span class='meta'>vs</span> {html.escape(row.away_team)}"
    date = pd.Timestamp(row.date).strftime("%b %d") if pd.notna(row.date) else ""
    grp = f"Group {row.group}" if getattr(row, "group", "") else getattr(row, "stage", "")
    meta = f"{date} · {html.escape(str(grp))}"

    if pred is None:
        return (f"<div class='skip'><b>{teams}</b> — {meta}. "
                f"No prediction: a team has insufficient recent data "
                f"(unseen in the 2018+ training window).</div>")

    ph, pd_, pa = pred.p_home_win, pred.p_draw, pred.p_away_win
    bar = (
        f"<div class='bar'>"
        f"<div class='seg h' style='width:{ph*100:.2f}%' title='Home'>{_pct(ph)}</div>"
        f"<div class='seg d' style='width:{pd_*100:.2f}%' title='Draw'>{_pct(pd_)}</div>"
        f"<div class='seg a' style='width:{pa*100:.2f}%' title='Away'>{_pct(pa)}</div>"
        f"</div>"
    )
    sl = "".join(
        f"<span>{i}–{j} · {_pct(p)}</span>"
        for i, j, p in pred.top_scorelines(4)
    )
    stats = (
        f"<div class='row'>"
        f"<div>xG <b>{pred.exp_home_goals:.2f}–{pred.exp_away_goals:.2f}</b></div>"
        f"<div>Over 2.5: <b>{_pct(pred.p_over_2_5)}</b></div>"
        f"<div>Venue: <b>{'neutral' if pred.neutral else 'home'}</b></div>"
        f"</div>"
    )

    played = ""
    if getattr(row, "played", False):
        hg, ag = int(row.home_score), int(row.away_score)
        actual = _actual_label(hg, ag)
        picked = _result_label(pred)
        ok = actual == picked
        verdict = ("<span class='ok'>✓ correct</span>" if ok
                   else "<span class='miss'>✗ missed</span>")
        played = (f"<div class='played'>Actual: <b>{hg}–{ag}</b> "
                  f"({actual} win) — model's pick: {picked} {verdict}</div>")

    return (
        f"<div class='match'>"
        f"<div class='mh'><div class='teams'>{teams}</div>"
        f"<div class='meta'>{meta}</div></div>"
        f"{bar}{stats}<div class='scorelines'>{sl}</div>{played}"
        f"</div>"
    )


# Display order for stages.
_STAGE_ORDER = [
    "Group", "Round of 32", "Round of 16", "Quarter-final",
    "Semi-final", "Third place", "Final",
]


def render_report(
    idata,
    fixtures: pd.DataFrame,
    teams: list[str],
    out_path: Path | None = None,
    generated_on: str = "",
) -> Path:
    out_path = out_path or DEFAULT_OUT
    preds = build_predictions(idata, fixtures, teams)

    # Tally accuracy on already-played matches.
    n_played = n_correct = 0
    for row, pred in preds:
        if pred is not None and getattr(row, "played", False):
            n_played += 1
            if _actual_label(int(row.home_score), int(row.away_score)) == _result_label(pred):
                n_correct += 1

    # Group by stage in display order, then group letter, then date.
    def stage_key(item):
        s = getattr(item[0], "stage", "")
        return _STAGE_ORDER.index(s) if s in _STAGE_ORDER else 99

    preds_sorted = sorted(preds, key=lambda it: (
        stage_key(it), str(getattr(it[0], "group", "")),
        pd.Timestamp(it[0].date) if pd.notna(it[0].date) else pd.Timestamp.max,
    ))

    sections: list[str] = []
    current = None
    buf: list[str] = []
    for row, pred in preds_sorted:
        stage = getattr(row, "stage", "Fixtures")
        grp = getattr(row, "group", "")
        header = f"{stage} {grp}".strip() if stage == "Group" else stage
        if header != current:
            if buf:
                sections.append(f"<h2>{html.escape(current)}</h2>" + "".join(buf))
            current, buf = header, []
        buf.append(_match_html(row, pred))
    if buf:
        sections.append(f"<h2>{html.escape(current)}</h2>" + "".join(buf))

    acc = f"{n_correct}/{n_played} ({n_correct/n_played*100:.0f}%)" if n_played else "—"
    legend = (
        "<div class='legend'>Bars show "
        "<i class='h'>home win</i> · <i class='d'>draw</i> · "
        "<i class='a'>away win</i> probability. "
        "Predictions from a Bayesian hierarchical Poisson model (MCMC).</div>"
    )
    gen = f" · generated {html.escape(generated_on)}" if generated_on else ""

    doc = (
        f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>World Cup 2026 — Match Predictions</title>"
        f"<style>{_CSS}</style></head><body><div class='wrap'>"
        f"<h1>World Cup 2026 — Match Predictions</h1>"
        f"<p class='sub'>Bayesian hierarchical Poisson · trained on 2018+ "
        f"internationals · pick accuracy on played matches: <b>{acc}</b>{gen}</p>"
        f"{legend}"
        f"{''.join(sections)}"
        f"<footer>Model: double-Poisson with hierarchical attack/defense "
        f"strengths and neutral-gated home advantage, fit via MCMC (PyMC). "
        f"Probabilities integrate over the full posterior. Source data: "
        f"martj42/international_results (CC0).</footer>"
        f"</div></body></html>"
    )
    out_path.write_text(doc, encoding="utf-8")
    return out_path

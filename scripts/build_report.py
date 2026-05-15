#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data" / "summary.json"
OUT_PATH = ROOT / "index.html"
ROUNDS_INDEX_PATH = ROOT / "data" / "rounds" / "index.html"

PROVIDER_ORDER = ["croon", "elevenlabs", "heygen", "rask", "youtube_auto"]
PROVIDER_LABELS = {
    "croon": "CROON",
    "elevenlabs": "ElevenLabs",
    "heygen": "HeyGen",
    "rask": "Rask",
    "youtube_auto": "YouTube Auto-dub",
}
PROVIDER_SHORT_LABELS = {
    "croon": "CR",
    "elevenlabs": "EL",
    "heygen": "HG",
    "rask": "RK",
    "youtube_auto": "YT",
}
COLORS = {
    "croon": "#ff7a1a",
    "elevenlabs": "#77839a",
    "heygen": "#4d95ff",
    "rask": "#36b77c",
    "youtube_auto": "#ff4d4f",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def load_summary() -> dict[str, object]:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def provider_key_from_name(name: str) -> str:
    for key, label in PROVIDER_LABELS.items():
        if label == name:
            return key
    return name.lower().replace(" ", "_")


def build_language_cards(cases: list[dict[str, object]]) -> str:
    cards = []
    for case in cases:
        providers = case["providers"]
        winner = case["winner"]
        winner_key = winner["provider_key"]
        bars = []
        for key in PROVIDER_ORDER:
            provider = providers.get(key)
            if not provider:
                continue
            width = max(2, provider["top1_count"] * 10)
            active = key == winner_key
            bars.append(
                f"""
          <div class="bar-row {'winner-row' if active else ''}">
            <div class="bar-label">{esc(PROVIDER_LABELS[key])}</div>
            <div class="bar-track"><div class="bar-fill" style="width:{width}%; background:{COLORS[key]}"></div></div>
            <div class="bar-value">{provider['top1_count']}/10</div>
          </div>"""
            )
        source = case["source_video"]
        cards.append(
            f"""
      <section class="lang-card {'croon-win' if winner_key == 'croon' else ''}">
        <div class="lang-head">
          <div>
            <h3>{esc(case['target_language'])}</h3>
            <p>{esc(case['source_language'])} to {esc(case['target_language'])}</p>
          </div>
          <div class="winner-pill">#1 {esc(winner['provider_name'])}</div>
        </div>
        <div class="bars">{''.join(bars)}</div>
        <dl class="metrics">
          <div><dt>Source</dt><dd><a href="{esc(source['url'])}">{esc(source['title'])}</a></dd></div>
          <div><dt>Clip</dt><dd>{esc(case['clip_range'])}</dd></div>
          <div><dt>Winner avg rank</dt><dd>{fmt(winner['average_rank'])}</dd></div>
          <div><dt>Winner Borda</dt><dd>{fmt(winner['borda_score'])}</dd></div>
        </dl>
      </section>"""
        )
    return "".join(cards)


def build_leaderboard(summary: dict[str, object]) -> tuple[str, str]:
    provider_votes: Counter[str] = Counter()
    language_wins: Counter[str] = Counter()
    for case in summary["cases"]:
        language_wins[case["winner"]["provider_name"]] += 1
        for provider in case["providers"].values():
            provider_votes[provider["provider_name"]] += provider["top1_count"]

    max_votes = max(provider_votes.values())
    vote_rows = []
    for name, votes in provider_votes.most_common():
        key = provider_key_from_name(name)
        width = round((votes / max_votes) * 100, 2)
        vote_rows.append(
            f"""
          <div class="leader-row">
            <div class="leader-label">{esc(name)}</div>
            <div class="leader-track"><div class="leader-fill" style="width:{width}%; background:{COLORS.get(key, '#888')}"></div></div>
            <div class="leader-value">{votes}</div>
          </div>"""
        )

    max_wins = max(language_wins.values())
    win_rows = []
    for name, wins in language_wins.most_common():
        key = provider_key_from_name(name)
        width = round((wins / max_wins) * 100, 2)
        win_rows.append(
            f"""
          <div class="leader-row">
            <div class="leader-label">{esc(name)}</div>
            <div class="leader-track"><div class="leader-fill" style="width:{width}%; background:{COLORS.get(key, '#888')}"></div></div>
            <div class="leader-value">{wins}/10</div>
          </div>"""
        )
    return "".join(win_rows), "".join(vote_rows)


def mini_chart(title: str, subtitle: str, values: list[tuple[str, str, float, str]], max_value: float) -> str:
    bars = []
    for key, label, value, display in values:
        height = 0 if max_value == 0 else max(3, round((value / max_value) * 100, 2))
        bars.append(
            f"""
            <div class="mini-bar-cell">
              <div class="mini-value">{esc(display)}</div>
              <div class="mini-bar-rail"><div class="mini-bar-fill" style="--bar:{height}%; height:{height}%; background:{COLORS.get(key, '#888')}"></div></div>
              <div class="mini-label" title="{esc(label)}">{esc(PROVIDER_SHORT_LABELS.get(key, label))}</div>
            </div>"""
        )
    return (
        f"""
      <section class="mini-chart">
        <div class="mini-bars">{''.join(bars)}</div>
        <div class="mini-caption">
          <h3>{esc(title)}</h3>
          <p>{esc(subtitle)}</p>
        </div>
      </section>"""
    )


def build_provider_legend() -> str:
    items = []
    for key in PROVIDER_ORDER:
        items.append(
            f"""
        <div class="legend-item">
          <span style="background:{COLORS[key]}"></span>
          <strong>{esc(PROVIDER_SHORT_LABELS[key])}</strong>
          <em>{esc(PROVIDER_LABELS[key])}</em>
        </div>"""
        )
    return f"""<section class="provider-legend">{''.join(items)}</section>"""


def build_language_chart_wall(cases: list[dict[str, object]]) -> str:
    charts = []
    for case in cases:
        values = []
        for key in PROVIDER_ORDER:
            provider = case["providers"][key]
            values.append((key, PROVIDER_LABELS[key], provider["top1_count"], f"{provider['top1_count']}"))
        charts.append(
            mini_chart(
                str(case["target_language"]),
                f"{case['source_language']} to {case['target_language']} / top-1 votes",
                values,
                10,
            )
        )
    return "".join(charts)


def build_source_chart_wall(cases: list[dict[str, object]]) -> str:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for case in cases:
        grouped[str(case["source_video_id"])].append(case)

    charts = []
    for source_id, source_cases in grouped.items():
        totals = {key: 0 for key in PROVIDER_ORDER}
        for case in source_cases:
            for key in PROVIDER_ORDER:
                totals[key] += case["providers"][key]["top1_count"]
        max_value = max(10, len(source_cases) * 10)
        source = source_cases[0]["source_video"]
        target_label = ", ".join(str(case["target_language"]) for case in source_cases)
        values = [(key, PROVIDER_LABELS[key], totals[key], str(totals[key])) for key in PROVIDER_ORDER]
        title = str(source.get("speaker_context") or source["title"]).split(" - ")[0].split(" – ")[0]
        charts.append(mini_chart(title, f"{target_label} / source video aggregate", values, max_value))
    return "".join(charts)


def build_criteria_chart_wall(summary: dict[str, object]) -> str:
    criteria = list(summary.get("criteria") or [])
    criteria.append({"key": "overall_score", "label": "Overall score"})
    charts = []
    for item in criteria:
        key = item["key"]
        values = []
        for provider_key in PROVIDER_ORDER:
            scores = [
                float(case["providers"][provider_key]["criteria_averages"][key])
                for case in summary["cases"]
                if "criteria_averages" in case["providers"][provider_key]
            ]
            average = sum(scores) / len(scores)
            values.append((provider_key, PROVIDER_LABELS[provider_key], average, f"{average:.1f}"))
        charts.append(mini_chart(str(item["label"]), "Average model score out of 10", values, 10))
    return "".join(charts)


def build_source_rows(cases: list[dict[str, object]]) -> str:
    rows = []
    seen: set[str] = set()
    for case in cases:
        source_id = case["source_video_id"]
        if source_id in seen:
            continue
        seen.add(source_id)
        source = case["source_video"]
        targets = ", ".join(c["target_language"] for c in cases if c["source_video_id"] == source_id)
        rows.append(
            f"""
        <tr>
          <td><a href="{esc(source['url'])}">{esc(source['title'])}</a></td>
          <td>{esc(source.get('uploader', ''))}</td>
          <td>{esc(targets)}</td>
          <td>00:00-01:00</td>
        </tr>"""
        )
    return "".join(rows)


def render() -> str:
    summary = load_summary()
    cases = summary["cases"]
    croon_wins = [case for case in cases if case["winner"]["provider_key"] == "croon"]
    language_cards = build_language_cards(cases)
    win_rows, vote_rows = build_leaderboard(summary)
    language_chart_wall = build_language_chart_wall(cases)
    source_chart_wall = build_source_chart_wall(cases)
    criteria_chart_wall = build_criteria_chart_wall(summary)
    provider_legend = build_provider_legend()
    source_rows = build_source_rows(cases)
    croon_win_languages = ", ".join(case["target_language"] for case in croon_wins)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CROON Dubbing Evaluation</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #171412;
      --muted: #6a645d;
      --line: #e9e0d6;
      --paper: #fffaf4;
      --panel: #ffffff;
      --accent: #ff7a1a;
      --accent-ink: #9c4100;
      --accent-soft: #fff0e5;
      --dark: #241f1a;
      --shadow: 0 22px 70px rgba(40, 27, 13, .10);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ max-width: 100%; overflow-x: hidden; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--paper);
      line-height: 1.5;
    }}
    a {{ color: inherit; text-decoration-color: rgba(255, 122, 26, .55); text-underline-offset: 3px; }}
    .wrap {{ width: min(1180px, calc(100% - 40px)); margin: 0 auto; }}
    header {{ padding: 66px 0 36px; border-bottom: 1px solid var(--line); }}
    .eyebrow {{ font-size: 15px; font-weight: 850; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); margin: 0 0 18px; }}
    h1 {{ font-size: clamp(42px, 7vw, 84px); line-height: .94; letter-spacing: 0; margin: 0; max-width: 1020px; }}
    .lead {{ font-size: clamp(19px, 2.2vw, 28px); max-width: 920px; color: #352f2a; margin: 24px 0 0; }}
    .hero-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 34px; }}
    .stat {{ background: var(--panel); border-radius: 8px; padding: 20px; box-shadow: var(--shadow); border: 1px solid rgba(233,224,214,.72); }}
    .stat strong {{ display: block; font-size: 42px; line-height: 1; }}
    .stat span {{ color: var(--muted); font-size: 13px; font-weight: 780; text-transform: uppercase; letter-spacing: .05em; }}
    main {{ padding: 38px 0 64px; }}
    .section-head {{ display:flex; align-items:flex-end; justify-content:space-between; gap:24px; margin: 34px 0 18px; }}
    h2 {{ font-size: clamp(28px, 4vw, 48px); line-height: 1; margin: 0; }}
    .note {{ color: var(--muted); max-width: 660px; margin: 0; }}
    .panel {{ background: var(--panel); border: 1px solid rgba(233,224,214,.85); border-radius: 8px; padding: 22px; box-shadow: var(--shadow); }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    .leader-title {{ margin: 0 0 14px; font-size: 20px; }}
    .leader-row {{ display:grid; grid-template-columns: 136px 1fr 54px; gap: 12px; align-items:center; padding: 9px 0; }}
    .leader-row > *, .bar-row > * {{ min-width: 0; }}
    .leader-label, .bar-label {{ font-weight: 760; color: #3c3731; }}
    .leader-track, .bar-track {{ background: #f0ece6; border-radius: 999px; overflow: hidden; }}
    .leader-track {{ height: 14px; }}
    .bar-track {{ height: 12px; }}
    .leader-fill, .bar-fill {{ height: 100%; border-radius: 999px; }}
    .leader-value, .bar-value {{ font-variant-numeric: tabular-nums; font-weight: 840; text-align:right; }}
    .provider-legend {{ display:flex; flex-wrap:wrap; gap: 10px; margin: -4px 0 18px; }}
    .legend-item {{ display:flex; align-items:center; gap: 7px; background: var(--panel); border: 1px solid var(--line); border-radius: 999px; padding: 7px 10px; box-shadow: 0 8px 24px rgba(40,27,13,.06); }}
    .legend-item span {{ width: 10px; height: 10px; border-radius: 50%; }}
    .legend-item strong {{ font-size: 12px; }}
    .legend-item em {{ font-style: normal; color: var(--muted); font-size: 12px; }}
    .chart-wall {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }}
    .chart-wall > * {{ min-width: 0; }}
    .chart-wall.source-wall {{ grid-template-columns: repeat(5, minmax(0, 1fr)); }}
    .chart-wall.criteria-wall {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .mini-chart {{ background: #11100f; color: #f8f1e9; border: 1px solid rgba(255,255,255,.10); border-radius: 8px; padding: 15px; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between; }}
    .mini-bars {{ display: flex; justify-content: space-between; gap: 6px; align-items: end; min-height: 130px; min-width: 0; }}
    .mini-bar-cell {{ flex: 0 1 18%; max-width: 18%; min-width: 0; overflow:hidden; display:flex; flex-direction:column; align-items:center; gap: 6px; }}
    .mini-value {{ font-size: 12px; font-weight: 850; font-variant-numeric: tabular-nums; min-height: 18px; }}
    .mini-bar-rail {{ width: 100%; max-width: 28px; height: 88px; border-radius: 5px 5px 0 0; background: rgba(255,255,255,.07); display:flex; align-items:flex-end; overflow:hidden; }}
    .mini-bar-fill {{ width:100%; border-radius: 5px 5px 0 0; }}
    .mini-label {{ font-size: 10px; color: #c9beb2; text-align:center; line-height:1.1; white-space: nowrap; }}
    .mini-caption {{ text-align:center; margin-top: 14px; }}
    .mini-caption h3 {{ font-size: 18px; margin: 0; color: #fff; line-height: 1.08; }}
    .mini-caption p {{ margin: 7px 0 0; color: #bfb4a8; font-size: 12px; line-height:1.25; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .lang-card {{ background: var(--panel); border-radius: 8px; padding: 20px; box-shadow: var(--shadow); border: 1px solid rgba(233,224,214,.82); }}
    .lang-card.croon-win {{ border-color: rgba(255,122,26,.34); }}
    .lang-head {{ display:flex; justify-content:space-between; align-items:flex-start; gap: 14px; margin-bottom: 18px; }}
    .lang-head > div {{ min-width: 0; }}
    h3 {{ font-size: 27px; margin:0; line-height: 1; }}
    .lang-head p {{ margin: 8px 0 0; color: var(--muted); }}
    .winner-pill {{ white-space: nowrap; background: var(--accent-soft); color: var(--accent-ink); border-radius: 999px; padding: 7px 11px; font-weight: 850; font-size: 13px; }}
    .bar-row {{ display:grid; grid-template-columns: 116px 1fr 44px; gap: 12px; align-items:center; padding: 7px 0; }}
    .winner-row .bar-label, .winner-row .bar-value {{ color: var(--accent-ink); }}
    .metrics {{ display:grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; margin: 18px 0 0; padding-top: 16px; border-top: 1px solid var(--line); }}
    .metrics div {{ min-width: 0; }}
    dt {{ font-size: 12px; color: var(--muted); font-weight: 850; text-transform: uppercase; letter-spacing: .05em; }}
    dd {{ margin: 3px 0 0; font-weight: 650; overflow-wrap: anywhere; }}
    .flow {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }}
    .flow-step {{ background: var(--dark); color: #fff6ee; border-radius: 8px; padding: 18px; min-height: 150px; position: relative; }}
    .flow-step strong {{ display: inline-flex; width: 32px; height: 32px; align-items:center; justify-content:center; border-radius: 50%; background: var(--accent); color:#1e1208; margin-bottom: 16px; font-weight: 900; }}
    .flow-step h3 {{ font-size: 20px; margin-bottom: 8px; }}
    .flow-step p {{ color: #e6d8ca; margin: 0; }}
    .guard-grid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
    .guard {{ background: var(--panel); border-radius: 8px; padding: 18px; border: 1px solid var(--line); }}
    .guard h3 {{ font-size: 19px; margin: 0 0 8px; }}
    .guard p {{ margin: 0; color: var(--muted); }}
    .code-panel {{ background: #181512; color: #fff7ef; border-radius: 8px; padding: 20px; overflow: auto; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }}
    pre {{ margin: 0; font-size: 14px; line-height: 1.55; }}
    table {{ width:100%; table-layout: fixed; border-collapse: collapse; background: var(--panel); border-radius: 8px; overflow:hidden; box-shadow: var(--shadow); }}
    th, td {{ text-align:left; padding: 14px 16px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }}
    tr:last-child td {{ border-bottom: 0; }}
    footer {{ color: var(--muted); padding: 30px 0 60px; }}
    @media (max-width: 960px) {{
      .hero-grid, .two-col, .grid, .flow, .guard-grid, .chart-wall, .chart-wall.source-wall, .chart-wall.criteria-wall {{ grid-template-columns: 1fr; }}
      .section-head {{ display:block; }}
      .note {{ margin-top: 10px; }}
      .metrics {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 620px) {{
      .wrap {{ width: min(320px, calc(100vw - 28px)); margin-left: 14px; margin-right: auto; }}
      h1 {{ font-size: 24px; line-height: 1.08; overflow-wrap: anywhere; }}
      h2 {{ font-size: 32px; }}
      .lead, .note {{ max-width: calc(100vw - 72px); }}
      .lead {{ font-size: 14px; overflow-wrap: anywhere; }}
      .stat strong {{ font-size: 36px; }}
      .provider-legend {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
      .legend-item {{ min-width: 0; }}
      .lang-card {{ padding: 16px; }}
      .winner-pill {{ white-space: normal; max-width: 78px; text-align: center; font-size: 11px; }}
      .leader-row {{ grid-template-columns: 82px minmax(0, 1fr) 42px; gap: 8px; }}
      .bar-row {{ grid-template-columns: 76px minmax(0, 1fr) 38px; gap: 8px; }}
      .leader-label, .bar-label {{ font-size: 13px; overflow-wrap: anywhere; }}
      .mini-chart {{ padding: 14px 12px; min-height: auto; }}
      .mini-bars {{ display: grid; grid-template-columns: 1fr; gap: 8px; min-height: 0; }}
      .mini-bar-cell {{ display: grid; grid-template-columns: 26px minmax(0, 1fr) 28px; max-width: none; flex: none; gap: 8px; align-items: center; }}
      .mini-label {{ grid-column: 1; grid-row: 1; text-align: left; }}
      .mini-bar-rail {{ grid-column: 2; grid-row: 1; width: 100%; max-width: none; height: 9px; border-radius: 999px; }}
      .mini-bar-fill {{ width: var(--bar); height: 100% !important; border-radius: 999px; }}
      .mini-value {{ grid-column: 3; grid-row: 1; font-size: 11px; min-height: 0; text-align: right; }}
      .mini-caption h3 {{ font-size: 18px; }}
      .mini-caption p {{ font-size: 11px; }}
      pre {{ font-size: 12px; }}
      table {{ font-size: 14px; }}
      th, td {{ padding: 12px; overflow-wrap: anywhere; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <p class="eyebrow">Dubbing evaluation benchmark</p>
      <h1>CROON ranked #1 in 5 of 10 languages.</h1>
      <p class="lead">A shuffled, anonymous Gemini evaluation compared CROON, ElevenLabs, HeyGen, Rask, and YouTube Auto-dub on the first 60 seconds of public YouTube source videos.</p>
      <div class="hero-grid">
        <div class="stat"><strong>5/10</strong><span>CROON first-place languages</span></div>
        <div class="stat"><strong>34</strong><span>CROON top-1 votes out of 100</span></div>
        <div class="stat"><strong>10</strong><span>shuffled rounds per language</span></div>
        <div class="stat"><strong>500</strong><span>candidate rankings published</span></div>
      </div>
    </div>
  </header>
  <main class="wrap">
    <div class="section-head">
      <h2>Ranking result</h2>
      <p class="note">The headline ranking uses top-1 votes across 10 shuffled rounds per target language. CROON led in {esc(croon_win_languages)}.</p>
    </div>
    <section class="two-col">
      <div class="panel">
        <h3 class="leader-title">Languages won</h3>
        {win_rows}
      </div>
      <div class="panel">
        <h3 class="leader-title">Total top-1 votes</h3>
        {vote_rows}
      </div>
    </section>

    <div class="section-head">
      <h2>Benchmark chart wall</h2>
      <p class="note">Small multiples show the same provider comparison for every target language, similar to public model benchmark releases.</p>
    </div>
    {provider_legend}
    <section class="chart-wall">{language_chart_wall}</section>

    <div class="section-head">
      <h2>Video-level view</h2>
      <p class="note">When one source video has multiple target languages, scores are aggregated across those language runs.</p>
    </div>
    <section class="chart-wall source-wall">{source_chart_wall}</section>

    <div class="section-head">
      <h2>Quality dimensions</h2>
      <p class="note">Gemini scored each candidate on translation, naturalness, voice match, speaker separation, timing alignment, and overall quality.</p>
    </div>
    <section class="chart-wall criteria-wall">{criteria_chart_wall}</section>

    <div class="section-head">
      <h2>Evidence by language</h2>
      <p class="note">Each card shows the number of first-place votes out of 10. Raw per-round ranking rows are published in <a href="data/rounds/">data/rounds</a>.</p>
    </div>
    <div class="grid">{language_cards}</div>

    <div class="section-head">
      <h2>How the benchmark works</h2>
      <p class="note">The setup is designed to compare dubbing quality, not file quality or provider branding.</p>
    </div>
    <section class="flow">
      <div class="flow-step"><strong>1</strong><h3>Clip</h3><p>Use the same 00:00-01:00 source range for every provider.</p></div>
      <div class="flow-step"><strong>2</strong><h3>Anonymize</h3><p>Map provider outputs to Candidate A through E.</p></div>
      <div class="flow-step"><strong>3</strong><h3>Shuffle</h3><p>Randomize candidate order for every round.</p></div>
      <div class="flow-step"><strong>4</strong><h3>Rank</h3><p>Gemini ranks all five candidates against the source video.</p></div>
      <div class="flow-step"><strong>5</strong><h3>Aggregate</h3><p>Count top-1 votes and publish raw ranking rows.</p></div>
    </section>

    <div class="section-head">
      <h2>Validity controls</h2>
      <p class="note">These controls reduce obvious bias and make the result inspectable.</p>
    </div>
    <section class="guard-grid">
      <div class="guard"><h3>Anonymous candidates</h3><p>The model receives Candidate A-E labels, not provider names.</p></div>
      <div class="guard"><h3>Order randomization</h3><p>Every round uses a fresh shuffled order to reduce position effects.</p></div>
      <div class="guard"><h3>Source included</h3><p>The original clip is included so translation, timing, and voice matching can be judged against the source.</p></div>
      <div class="guard"><h3>Fixed clip range</h3><p>All providers are evaluated on the same first 60 seconds.</p></div>
      <div class="guard"><h3>No bitrate reward</h3><p>The prompt explicitly tells the model to ignore video resolution and bitrate.</p></div>
      <div class="guard"><h3>Raw rows published</h3><p>Aggregate scores and per-round rankings are available as JSON.</p></div>
    </section>

    <div class="section-head">
      <h2>Reproduce the run</h2>
      <p class="note">The media files are not redistributed, but the ranking script and manifest format are included so the same method can be rerun with local clips.</p>
    </div>
    <section class="code-panel">
<pre>python3 -m venv .venv
. .venv/bin/activate
pip install google-genai

# Fill examples/manifest.example.json with local source and candidate media paths.
python3 scripts/evaluate_relative_ranking.py \\
  --manifest examples/manifest.example.json \\
  --out runs/example \\
  --rounds 10 \\
  --seed 760

python3 scripts/build_report.py</pre>
    </section>

    <div class="section-head">
      <h2>Source videos</h2>
      <p class="note">No source or dubbed media files are redistributed in this repository. The report links to public source videos and states the evaluated clip range.</p>
    </div>
    <table>
      <thead><tr><th>Source</th><th>Channel</th><th>Targets</th><th>Clip</th></tr></thead>
      <tbody>{source_rows}</tbody>
    </table>
  </main>
  <footer class="wrap">
    Data: <a href="data/summary.json">summary.json</a>. Method: <a href="methodology.md">methodology.md</a>. Reproduction script: <a href="scripts/evaluate_relative_ranking.py">scripts/evaluate_relative_ranking.py</a>.
  </footer>
</body>
</html>
"""


def render_rounds_index(summary: dict[str, object]) -> str:
    rows = []
    for case in summary["cases"]:
        href = f"{case['case_id']}.json"
        rows.append(
            f"""
        <tr>
          <td><a href="{esc(href)}">{esc(case['target_language'])}</a></td>
          <td>{esc(case['source_language'])} to {esc(case['target_language'])}</td>
          <td>{esc(case['winner']['provider_name'])}</td>
          <td>{esc(case['winner']['top1_count'])}/10</td>
        </tr>"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Raw ranking rows</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 40px; color: #171412; background: #fffaf4; }}
    main {{ max-width: 960px; margin: 0 auto; }}
    a {{ color: inherit; text-decoration-color: #ff7a1a; text-underline-offset: 3px; }}
    h1 {{ font-size: clamp(34px, 5vw, 56px); line-height: 1; margin: 0 0 14px; }}
    p {{ color: #6a645d; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 18px 50px rgba(40, 27, 13, .10); }}
    th, td {{ text-align: left; padding: 14px 16px; border-bottom: 1px solid #e9e0d6; }}
    th {{ color: #6a645d; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; }}
  </style>
</head>
<body>
  <main>
    <p><a href="../../">Back to report</a></p>
    <h1>Raw ranking rows</h1>
    <p>Each file contains normalized case metadata plus the 50 per-candidate ranking rows for one language.</p>
    <table>
      <thead><tr><th>Language</th><th>Direction</th><th>Winner</th><th>Top-1 votes</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </main>
</body>
</html>
"""


def main() -> None:
    summary = load_summary()
    OUT_PATH.write_text(render(), encoding="utf-8")
    ROUNDS_INDEX_PATH.write_text(render_rounds_index(summary), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {ROUNDS_INDEX_PATH}")


if __name__ == "__main__":
    main()

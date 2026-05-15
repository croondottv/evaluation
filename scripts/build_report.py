#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data" / "summary.json"
OUT_PATH = ROOT / "index.html"
ROUNDS_INDEX_PATH = ROOT / "data" / "rounds" / "index.html"
ASSETS_DIR = ROOT / "assets"
BENCHMARK_SVG_PATH = ASSETS_DIR / "benchmark-chart-wall.svg"

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


def svg_text(value: object) -> str:
    return html.escape(str(value), quote=False)


def load_summary() -> dict[str, object]:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def render_benchmark_svg(summary: dict[str, object]) -> str:
    cases = summary["cases"]
    width = 1200
    height = 760
    margin_x = 44
    top = 118
    card_w = 206
    card_h = 256
    gap_x = 24
    gap_y = 28
    chart_h = 124
    bar_w = 22
    bar_gap = 14

    legend_items = []
    legend_x = 66
    for key in PROVIDER_ORDER:
        legend_items.append(
            f'<g transform="translate({legend_x},40)">'
            f'<rect width="18" height="18" rx="4" fill="{COLORS[key]}"/>'
            f'<text x="28" y="14" fill="#f5efe8" font-size="17" font-weight="700">{svg_text(PROVIDER_LABELS[key])}</text>'
            f"</g>"
        )
        legend_x += 210

    chart_groups = []
    for index, case in enumerate(cases):
        col = index % 5
        row = index // 5
        x = margin_x + col * (card_w + gap_x)
        y = top + row * (card_h + gap_y)
        bars = []
        start_x = 28
        baseline = 164
        for provider_index, key in enumerate(PROVIDER_ORDER):
            value = int(case["providers"][key]["top1_count"])
            bar_h = max(3, round((value / 10) * chart_h))
            bx = start_x + provider_index * (bar_w + bar_gap)
            by = baseline - bar_h
            bars.append(
                f'<text x="{bx + bar_w / 2}" y="24" text-anchor="middle" fill="#f5efe8" font-size="14" font-weight="800">{value}</text>'
                f'<rect x="{bx}" y="{baseline - chart_h}" width="{bar_w}" height="{chart_h}" rx="5" fill="#242424"/>'
                f'<rect x="{bx}" y="{by}" width="{bar_w}" height="{bar_h}" rx="5" fill="{COLORS[key]}"/>'
                f'<text x="{bx + bar_w / 2}" y="{baseline + 20}" text-anchor="middle" fill="#b9b2aa" font-size="10" font-weight="700">{svg_text(PROVIDER_SHORT_LABELS[key])}</text>'
            )
        chart_groups.append(
            f"""
    <g transform="translate({x},{y})">
      <rect width="{card_w}" height="{card_h}" rx="8" fill="#0e0e0f" stroke="#29313b"/>
      {''.join(bars)}
      <text x="{card_w / 2}" y="206" text-anchor="middle" fill="#ffffff" font-size="21" font-weight="850">{svg_text(case['target_language'])}</text>
      <text x="{card_w / 2}" y="232" text-anchor="middle" fill="#a99f96" font-size="13">{svg_text(case['source_language'])} to {svg_text(case['target_language'])} / top-1 votes</text>
    </g>"""
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="CROON dubbing benchmark chart wall">
  <rect width="100%" height="100%" fill="#050506"/>
  <text x="44" y="34" fill="#ff7a1a" font-size="15" font-weight="850" letter-spacing="2">DUBBING EVALUATION BENCHMARK</text>
  {''.join(legend_items)}
  <text x="44" y="96" fill="#f5efe8" font-size="22" font-weight="800">Benchmark chart wall</text>
  <text x="308" y="96" fill="#a99f96" font-size="16">Top-1 votes across 10 shuffled anonymous rounds per target language</text>
  {''.join(chart_groups)}
</svg>
"""


def render_index(summary: dict[str, object]) -> str:
    wins = ", ".join(summary["headline_result"]["croon_first_place_languages"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CROON Dubbing Evaluation</title>
  <style>
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #171412;
      background: #fffaf4;
      line-height: 1.5;
    }}
    main {{ width: min(980px, calc(100% - 32px)); margin: 48px auto 72px; }}
    h1 {{ font-size: clamp(34px, 6vw, 68px); line-height: .98; margin: 0 0 16px; }}
    p {{ color: #5f5851; font-size: 18px; max-width: 760px; }}
    img {{ width: 100%; height: auto; border-radius: 8px; margin: 24px 0; box-shadow: 0 18px 60px rgba(40, 27, 13, .16); background: #050506; }}
    ul {{ padding-left: 22px; }}
    li {{ margin: 7px 0; }}
    a {{ color: inherit; text-decoration-color: rgba(255, 122, 26, .65); text-underline-offset: 3px; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 20px; }}
    .links a {{ border: 1px solid #e9e0d6; border-radius: 999px; padding: 9px 13px; background: #fff; font-weight: 700; text-decoration: none; }}
  </style>
</head>
<body>
  <main>
    <h1>CROON ranked #1 in 5 of 10 languages.</h1>
    <p>Shuffled anonymous Gemini benchmark. Primary metric: top-1 votes across 10 rounds per target language.</p>
    <img src="assets/benchmark-chart-wall.svg" alt="Benchmark chart wall showing top-1 votes by provider and target language">
    <ul>
      <li>CROON won: {esc(wins)}</li>
      <li>Compared against: ElevenLabs, HeyGen, Rask, YouTube Auto-dub</li>
      <li>Clip range: first 60 seconds of each source video</li>
      <li>Raw data and reproduction scripts are kept in this repository.</li>
    </ul>
    <div class="links">
      <a href="data/summary.json">summary.json</a>
      <a href="data/rounds/">raw ranking rows</a>
      <a href="methodology.md">methodology</a>
      <a href="scripts/evaluate_relative_ranking.py">evaluation script</a>
    </div>
  </main>
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
    <p><a href="../../">Back</a></p>
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
    ASSETS_DIR.mkdir(exist_ok=True)
    BENCHMARK_SVG_PATH.write_text(render_benchmark_svg(summary), encoding="utf-8")
    OUT_PATH.write_text(render_index(summary), encoding="utf-8")
    ROUNDS_INDEX_PATH.write_text(render_rounds_index(summary), encoding="utf-8")
    print(f"Wrote {BENCHMARK_SVG_PATH}")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {ROUNDS_INDEX_PATH}")


if __name__ == "__main__":
    main()

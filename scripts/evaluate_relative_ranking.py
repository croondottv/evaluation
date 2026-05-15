#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import random
from pathlib import Path
from statistics import mean
from typing import Any

from google import genai
from google.genai import types


DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
DEFAULT_LOCATION = "global"

SCHEMA = {
    "type": "object",
    "properties": {
        "source_summary": {"type": "string"},
        "ranking": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer"},
                    "candidate": {"type": "string"},
                    "overall_score": {"type": "number"},
                    "translation_accuracy": {"type": "number"},
                    "spoken_naturalness": {"type": "number"},
                    "voice_similarity": {"type": "number"},
                    "speaker_separation": {"type": "number"},
                    "timing_alignment": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": [
                    "rank",
                    "candidate",
                    "overall_score",
                    "translation_accuracy",
                    "spoken_naturalness",
                    "voice_similarity",
                    "speaker_separation",
                    "timing_alignment",
                    "reason",
                ],
            },
        },
        "decision_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["source_summary", "ranking", "decision_notes"],
}

PROMPT_TEMPLATE = """\
You are comparing five anonymous {target_language} dubbed versions of the same {source_language} source video.

Input 1 is the original {source_language} source video.
Inputs 2-6 are five anonymous {target_language} dubbed candidates for the same time range.

Rank the five candidates from best to worst for overall dubbing quality.
Use the following criteria:
- translation_accuracy: preserves source meaning, details, humor, and conversational intent
- spoken_naturalness: {target_language} sounds fluent, idiomatic, and pleasant
- voice_similarity: dubbed voices resemble the original speakers' tone, identity, age/gender impression, and energy
- speaker_separation: speakers are distinguishable and mapped consistently
- timing_alignment: speech timing, pauses, laughter, turn-taking, and visual rhythm match the source

Important:
- Do not reward video resolution or bitrate.
- Judge only dubbing quality.
- The candidates are anonymized. Do not infer provider names.
- Prefer the candidate that would be most convincing as a production dub.
- Return JSON only. Do not include markdown.
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def media_part(path: Path) -> types.Part:
    mime_type = mimetypes.guess_type(path.name)[0]
    if path.suffix == ".webm":
        mime_type = "audio/webm"
    if path.suffix == ".mp4":
        mime_type = "video/mp4"
    if not mime_type:
        raise ValueError(f"Could not infer MIME type for {path}")
    return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_type)


def validate_manifest(manifest: dict[str, Any], base_dir: Path) -> None:
    if not manifest.get("cases"):
        raise ValueError("Manifest must include at least one case.")
    for case in manifest["cases"]:
        candidates = case.get("candidates") or []
        if len(candidates) != 5:
            raise ValueError(f"{case.get('case_id')}: expected exactly five candidates.")
        source_path = base_dir / case["source_path"]
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        keys = set()
        for candidate in candidates:
            if candidate["provider_key"] in keys:
                raise ValueError(f"{case.get('case_id')}: duplicate provider_key {candidate['provider_key']}")
            keys.add(candidate["provider_key"])
            candidate_path = base_dir / candidate["path"]
            if not candidate_path.exists():
                raise FileNotFoundError(candidate_path)


def build_orders(case: dict[str, Any], rounds: int, seed: int) -> list[list[dict[str, Any]]]:
    rng = random.Random(f"{seed}:{case['case_id']}")
    orders = []
    for _ in range(rounds):
        order = list(case["candidates"])
        rng.shuffle(order)
        orders.append(order)
    return orders


def evaluate_round(
    client: genai.Client,
    model: str,
    case: dict[str, Any],
    order: list[dict[str, Any]],
    base_dir: Path,
    out_dir: Path,
    round_index: int,
    overwrite: bool,
) -> dict[str, Any]:
    out_path = out_dir / f"round-{round_index:02d}.json"
    if out_path.exists() and not overwrite:
        return read_json(out_path)

    parts: list[types.Part] = [
        types.Part.from_text(
            text=PROMPT_TEMPLATE.format(
                source_language=case["source_language"],
                target_language=case["target_language"],
            )
        ),
        types.Part.from_text(text="SOURCE"),
        media_part(base_dir / case["source_path"]),
    ]

    mapping = []
    for index, item in enumerate(order):
        label = f"Candidate {chr(ord('A') + index)}"
        parts.append(types.Part.from_text(text=label))
        parts.append(media_part(base_dir / item["path"]))
        mapping.append(
            {
                "candidate": label,
                "provider_key": item["provider_key"],
                "provider_name": item["provider_name"],
            }
        )

    response = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=SCHEMA,
            max_output_tokens=8192,
        ),
    )

    payload: dict[str, Any] = {
        "model": model,
        "case_id": case["case_id"],
        "round": round_index,
        "mapping": mapping,
        "raw_text": response.text,
        "usage_metadata": response.usage_metadata.to_json_dict() if response.usage_metadata else None,
    }
    try:
        payload["json"] = json.loads(response.text or "{}")
    except json.JSONDecodeError:
        payload["json_parse_error"] = True
    write_json(out_path, payload)
    return payload


def aggregate_case(case: dict[str, Any], model: str, out_dir: Path, rounds: int) -> dict[str, Any]:
    stats: dict[str, dict[str, Any]] = {
        candidate["provider_key"]: {
            "provider_name": candidate["provider_name"],
            "top1_count": 0,
            "ranks": [],
            "borda_score": 0,
            "overall_scores": [],
        }
        for candidate in case["candidates"]
    }
    rows = []
    for round_index in range(1, rounds + 1):
        payload = read_json(out_dir / f"round-{round_index:02d}.json")
        mapping = {item["candidate"]: item for item in payload["mapping"]}
        for rank_item in (payload.get("json") or {}).get("ranking", []):
            mapped = mapping[rank_item["candidate"]]
            provider_key = mapped["provider_key"]
            rank = int(rank_item["rank"])
            stats[provider_key]["ranks"].append(rank)
            stats[provider_key]["borda_score"] += 6 - rank
            stats[provider_key]["overall_scores"].append(float(rank_item["overall_score"]))
            if rank == 1:
                stats[provider_key]["top1_count"] += 1
            rows.append(
                {
                    "case_id": case["case_id"],
                    "round": round_index,
                    "candidate": rank_item["candidate"],
                    "rank": rank,
                    "provider_key": provider_key,
                    "provider_name": mapped["provider_name"],
                    "overall_score": rank_item["overall_score"],
                    "translation_accuracy": rank_item["translation_accuracy"],
                    "spoken_naturalness": rank_item["spoken_naturalness"],
                    "voice_similarity": rank_item["voice_similarity"],
                    "speaker_separation": rank_item["speaker_separation"],
                    "timing_alignment": rank_item["timing_alignment"],
                    "reason": rank_item["reason"],
                }
            )

    providers = {}
    for provider_key, item in stats.items():
        providers[provider_key] = {
            "provider_name": item["provider_name"],
            "top1_count": item["top1_count"],
            "average_rank": round(mean(item["ranks"]), 3),
            "borda_score": item["borda_score"],
            "average_overall_score": round(mean(item["overall_scores"]), 3),
        }
    providers = dict(
        sorted(
            providers.items(),
            key=lambda kv: (-kv[1]["top1_count"], kv[1]["average_rank"], -kv[1]["borda_score"]),
        )
    )
    summary = {
        "model": model,
        "case_id": case["case_id"],
        "source_language": case["source_language"],
        "target_language": case["target_language"],
        "clip_range": case.get("clip_range", "00:00-01:00"),
        "evaluation_mode": "relative shuffled ranking; source + five anonymous candidates per request",
        "rounds": rounds,
        "providers": providers,
    }
    write_json(out_dir / "ranking-rows.json", rows)
    write_json(out_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run shuffled, anonymous relative dubbing evaluation.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model", default=os.getenv("GEMINI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=760)
    parser.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT"))
    parser.add_argument("--location", default=os.getenv("GOOGLE_CLOUD_LOCATION", DEFAULT_LOCATION))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Validate files and print shuffled orders without calling Gemini.")
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    base_dir = args.manifest.resolve().parent
    validate_manifest(manifest, base_dir)

    planned = {
        case["case_id"]: [
            [candidate["provider_key"] for candidate in order]
            for order in build_orders(case, args.rounds, args.seed)
        ]
        for case in manifest["cases"]
    }
    if args.dry_run:
        print(json.dumps(planned, ensure_ascii=False, indent=2))
        return

    if not args.project:
        raise SystemExit("Set --project or GOOGLE_CLOUD_PROJECT for Vertex AI Gemini access.")

    client = genai.Client(vertexai=True, project=args.project, location=args.location)
    summaries = []
    for case in manifest["cases"]:
        case_out_dir = args.out / case["case_id"] / args.model
        orders = build_orders(case, args.rounds, args.seed)
        for round_index, order in enumerate(orders, start=1):
            print(f"[{case['case_id']} {round_index:02d}/{args.rounds}] {args.model}", flush=True)
            evaluate_round(client, args.model, case, order, base_dir, case_out_dir, round_index, args.overwrite)
        summaries.append(aggregate_case(case, args.model, case_out_dir, args.rounds))
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

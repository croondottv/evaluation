# CROON Dubbing Evaluation

Public benchmark report for AI video dubbing quality.

CROON ranked #1 by top-1 votes in 5 of 10 target languages: Japanese, French, Portuguese, Chinese, Spanish.

Visual report: https://croondottv.github.io/evaluation/

## What this repository shows

This repository is intended to make the benchmark understandable and inspectable:

- what ranking was measured
- which providers and languages were compared
- what the result was
- how the evaluation avoided obvious provider bias
- which raw result rows support the charts
- how to rerun the same method with local media files

## Headline result

| Provider | Languages won | Top-1 votes |
| --- | ---: | ---: |
| CROON | 5 / 10 | 34 / 100 |
| Rask | 2 / 10 | 25 / 100 |
| ElevenLabs | 2 / 10 | 17 / 100 |
| HeyGen | 1 / 10 | 21 / 100 |
| YouTube Auto-dub | 0 / 10 | 3 / 100 |

`Languages won` counts the target languages where a provider received the most #1 rankings. `Top-1 votes` counts all first-place rankings across the 10 languages and 10 shuffled rounds per language.

## Language winners

| Target language | Winner | Top-1 votes |
| --- | --- | ---: |
| Japanese | CROON | 7 / 10 |
| French | CROON | 5 / 10 |
| Portuguese | CROON | 5 / 10 |
| Chinese | CROON | 5 / 10 |
| Spanish | CROON | 4 / 10 |
| German | Rask | 4 / 10 |
| Italian | HeyGen | 3 / 10 |
| Russian | ElevenLabs | 5 / 10 |
| Korean | ElevenLabs | 6 / 10 |
| English | Rask | 5 / 10 |

## Method summary

- Model: `gemini-3.1-flash-lite-preview`
- Providers: CROON, ElevenLabs, HeyGen, Rask, YouTube Auto-dub
- Target languages: 10
- Clip range: first 60 seconds, `00:00-01:00`
- Rounds: 10 shuffled rounds per language
- Input per round: source clip plus five anonymous dubbed candidates
- Primary metric: top-1 votes

The model was asked to rank the five anonymous candidates for dubbing quality only. The prompt explicitly says not to reward video resolution or bitrate.

## Why the comparison is reasonably fair

The benchmark is not a human listening study, but it includes controls that make the result more reliable than a single absolute score:

- Candidate labels were anonymous: Candidate A through Candidate E.
- Candidate order was shuffled every round.
- The source video was included in every request.
- Every provider was evaluated on the same `00:00-01:00` range.
- Provider names and original filenames were not included in prompts.
- The scoring prompt excludes video resolution and bitrate.
- Raw per-round ranking rows are published in `data/rounds/`.

## Repository structure

```text
index.html                         Static visual report
methodology.md                     Full method, prompt, controls, limitations
data/summary.json                  Normalized aggregate data
data/rounds/*.json                 Per-language raw ranking rows
data/README.md                     Data dictionary
scripts/build_report.py            Regenerates index.html from data/summary.json
scripts/evaluate_relative_ranking.py
                                   Runs the shuffled Gemini ranking method
examples/manifest.example.json     Example manifest for local reproduction
```

## Reproduce with local media

The source and dubbed media files are not committed. To rerun the benchmark, prepare local 60-second clips for the source and five candidates, then fill a manifest using `examples/manifest.example.json`.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install google-genai

export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=global

python3 scripts/evaluate_relative_ranking.py \
  --manifest examples/manifest.example.json \
  --out runs/example \
  --rounds 10 \
  --seed 760
```

To rebuild the static report after editing `data/summary.json`:

```bash
python3 scripts/build_report.py
```

## What is not included

Video files are not redistributed. The report links to the public YouTube source videos and states that only the first 60 seconds were evaluated.

## Limitations

- This is a model-based evaluation, not a substitute for a blinded human panel.
- It covers the selected first-minute clips, not all genres and accents.
- It compares the providers' generated outputs available for this run.
- The primary claim is based on top-1 vote count, with average rank and Borda score included as secondary evidence.

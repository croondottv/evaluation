# Methodology

This repository publishes the aggregate results and raw ranking rows from a relative dubbing-quality benchmark.

## Goal

The benchmark asks a narrow question:

> Given the same source clip and five anonymous dubbed versions, which candidate is the most convincing production dub?

It does not measure UI quality, upload speed, provider pricing, or video resolution.

## Model

- `gemini-3.1-flash-lite-preview`

## Providers

- CROON
- ElevenLabs
- HeyGen
- Rask
- YouTube Auto-dub

## Inputs

For each target language, the model received:

- the original source video clip
- five anonymous dubbed candidates for the same clip range
- only the first 60 seconds of each video, `00:00-01:00`

The source videos are listed in the visual report. The media files themselves are not redistributed in this repository.

## Evaluation flow

1. Prepare a 60-second source clip.
2. Prepare one dubbed output from each provider for the same source range.
3. Assign the five provider outputs to anonymous candidate labels.
4. Shuffle candidate order for each round.
5. Send the source clip and five candidates to Gemini.
6. Ask Gemini to rank the candidates from best to worst.
7. Repeat for 10 rounds per language.
8. Aggregate top-1 votes, average rank, Borda score, and average overall score.
9. Publish aggregate results and raw ranking rows.

## Primary metric

The primary metric is `top1_count`: how many of the 10 shuffled rounds ranked a provider first for that language.

The public headline uses target-language wins. A provider wins a target language when it receives the highest `top1_count` for that language.

## Secondary metrics

- `average_rank`: lower is better.
- `borda_score`: higher is better. Rank 1 receives 5 points, rank 2 receives 4 points, rank 5 receives 1 point.
- `average_overall_score`: Gemini's per-candidate overall quality score averaged across rounds.

These are included to make close races easier to inspect.

## Prompt

```text
You are comparing five anonymous target-language dubbed versions of the same source-language source video.

Input 1 is the original source-language source video.
Inputs 2-6 are five anonymous target-language dubbed candidates for the same time range.

Rank the five candidates from best to worst for overall dubbing quality.
Use the following criteria:
- translation_accuracy: preserves source meaning, details, humor, and conversational intent
- spoken_naturalness: target language sounds fluent, idiomatic, and pleasant
- voice_similarity: dubbed voices resemble the original speakers' tone, identity, age/gender impression, and energy
- speaker_separation: speakers are distinguishable and mapped consistently
- timing_alignment: speech timing, pauses, laughter, turn-taking, and visual rhythm match the source

Important:
- Do not reward video resolution or bitrate.
- Judge only dubbing quality.
- The candidates are anonymized. Do not infer provider names.
- Prefer the candidate that would be most convincing as a production dub.
- Return JSON only. Do not include markdown.
```

The actual script fills `source-language` and `target-language` for each case.

## Bias controls

The benchmark includes the following controls:

- Provider names are not included in the prompt.
- Candidate filenames are not included in the prompt.
- Candidates are presented as Candidate A through Candidate E.
- Candidate order is shuffled every round.
- The source clip is included in every request.
- Every provider is evaluated on the same 60-second range.
- The prompt explicitly excludes video resolution and bitrate from scoring.
- Raw ranking rows are published for inspection.

## Reproduction

Use `scripts/evaluate_relative_ranking.py` with a manifest that points to local media files.

```bash
python3 scripts/evaluate_relative_ranking.py \
  --manifest examples/manifest.example.json \
  --out runs/example \
  --rounds 10 \
  --seed 760
```

Use `--dry-run` to validate local paths and inspect the shuffled order without calling Gemini.

```bash
python3 scripts/evaluate_relative_ranking.py \
  --manifest examples/manifest.example.json \
  --out runs/example \
  --dry-run
```

## Data policy

This repository does not redistribute source videos or generated dubbed media. It publishes:

- YouTube source links
- the evaluated clip range
- aggregate scores
- raw ranking rows
- the prompt and reproduction script

## Limitations

The result should be read as an inspectable model-based benchmark, not a final scientific listening study. A stronger next step would add:

- more source videos per language
- multiple source domains, such as interviews, lectures, product demos, and entertainment clips
- multiple judges, including human bilingual listeners
- confidence intervals or bootstrap analysis over rounds and videos
- a pre-registered manifest before provider outputs are generated

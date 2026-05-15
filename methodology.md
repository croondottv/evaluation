# Methodology

This repository publishes the aggregate results and raw ranking rows from a relative dubbing-quality benchmark.

## Model

- `gemini-3.1-flash-lite-preview`

## Inputs

For each language, the model received:

- the original source video clip
- five anonymous dubbed candidates for the same clip range
- only the first 60 seconds of each video (`00:00-01:00`)

The evaluated providers were CROON, ElevenLabs, HeyGen, Rask, and YouTube Auto-dub. Provider names were not included in prompts, and candidate order was shuffled for each round.

## Scoring

Each language was evaluated for 10 shuffled rounds. The primary metric is top-1 votes: how many rounds each provider was ranked first. Secondary metrics are average rank, Borda score, and average overall score.

## Prompt

```text
You are comparing five anonymous dubbed versions of the same source video.

Input 1 is the original source video.
Inputs 2-6 are five anonymous dubbed candidates for the same time range.

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

## Data policy

This repository does not redistribute the source videos or the generated dubbed media. It publishes YouTube source links, the evaluated clip range, aggregate scores, and raw ranking rows.

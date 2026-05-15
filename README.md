# CROON Dubbing Evaluation

Public report for a 10-language dubbing benchmark using shuffled, anonymous relative ranking.

CROON ranked #1 by top-1 votes in 5 of 10 target languages: Japanese, French, Portuguese, Chinese, Spanish.

## What is included

- `index.html`: static visual report
- `data/summary.json`: normalized aggregate results
- `data/rounds/*.json`: per-language raw ranking rows
- `methodology.md`: evaluation prompt, scoring method, and data policy

## What is not included

Video files are not committed. The report links to source YouTube videos and states that only the first 60 seconds were evaluated.

## Headline method

- Model: `gemini-3.1-flash-lite-preview`
- Providers: CROON, ElevenLabs, HeyGen, Rask, YouTube Auto-dub
- 10 target languages
- 10 shuffled ranking rounds per language
- Source clip plus five anonymous candidates per request
- Primary metric: top-1 votes

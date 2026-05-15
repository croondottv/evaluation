# Data files

This directory contains the published data for the CROON dubbing evaluation.

## Files

- `summary.json`: normalized aggregate results used by the visual report.
- `rounds/*.json`: per-language raw ranking rows and the normalized case metadata.

## Primary ranking metric

The primary metric is `top1_count`: the number of shuffled rounds where a provider was ranked first for a target language.

Each language has 10 rounds. Each round ranks five anonymous candidates, so every language contributes 50 ranking rows.

## Secondary metrics

- `average_rank`: lower is better.
- `borda_score`: higher is better. For each round, rank 1 receives 5 points, rank 2 receives 4 points, and rank 5 receives 1 point.
- `average_overall_score`: the model's per-candidate overall score averaged across rounds.

## Media policy

The source and dubbed media files are not redistributed here. The public report lists the source YouTube URLs and the evaluated range, `00:00-01:00`.

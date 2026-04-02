# Fashion Image Search

A lightweight Streamlit app for uploading, classifying, organizing, and searching fashion inspiration photos with AI-assisted metadata.

## Overview

This prototype is designed for fashion designers who collect inspiration imagery in the field and need a fast way to turn scattered photos into a reusable library. The app supports local upload, AI-assisted classification, search and filtering across structured metadata, and designer-authored annotations.

## What Works

- a Streamlit entrypoint
- SQLite storage setup
- image upload and local asset persistence
- AI classification orchestration with OpenAI-first behavior and local fallback metadata generation
- searchable library grid with dynamically generated filters
- designer annotations stored separately from AI-generated metadata
- evaluation script and starter labeled dataset format under `eval/`
- pytest test layout

## Tech Stack

- Python 3.9+
- Streamlit
- SQLite
- OpenAI API
- pytest

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies into the environment:

```bash
./.venv/bin/pip install -e '.[dev]'
```

3. Copy environment variables:

```bash
cp .env.example .env
```
4. Add your api key

5. Run the app:

```bash
./.venv/bin/streamlit run app/main.py
```

6. Run tests:

```bash
./.venv/bin/python -m pytest
```

## Repository Structure

```text
app/       Streamlit app, data access, and service code
eval/      Evaluation scripts and labeled test set
tests/     Unit, integration, and end-to-end style tests
data/      Local runtime storage for uploaded assets
```

## Architecture Notes

- The app will store uploaded images on disk and structured metadata in SQLite.
- AI-generated descriptions and parsed attributes will be stored separately from designer-authored annotations.
- Filters will be generated dynamically from the stored metadata to avoid hardcoded facets.
- The evaluation workflow uses a JSONL labeled dataset and regenerates a structured report with per-attribute accuracy and sample failure cases.

## Product Trade-Offs

- Streamlit keeps the UI lightweight and fast to iterate on, which fits the one-day constraint better than a heavier frontend stack.
- SQLite and local file storage keep setup minimal and make the prototype easy to run locally without cloud infrastructure.
- The app uses an OpenAI-first classification path when an API key is available, but falls back to heuristics so the full workflow can still be demoed offline.
- Search is currently substring-based over AI descriptions and annotations rather than true semantic retrieval. This keeps implementation simple but limits natural-language flexibility.

## Evaluation Summary

The starter evaluation run was generated with:

```bash
./.venv/bin/python -m eval.evaluate --dataset eval/dataset/starter_labels.jsonl --output eval/results/latest_report.json
```

Starter-set results on 3 labeled samples:

- `garment_type`, `style`, `material`, `pattern`, `season`, `occasion`, `consumer_profile`, `city`, and `trend_notes` scored `1.0` on the labeled rows where those attributes were present.
- `color_palette` scored `0.0` on `3/3` measured rows.
- `continent` and `country` were not measured in the starter set because no labeled expectations were provided yet.

Interpretation:

- The current fallback classifier performs well when filename cues are strong, which is why garment type, city, and occasion look good in the starter run.
- Color palette is the weakest area right now. The heuristic color extraction is intentionally simple and does not yet align well with the labeled expectations.
- This starter report is useful as a plumbing check, but it is not a meaningful model benchmark yet. A real submission should expand the labeled set to 50-100 diverse images.

## Assumptions

- This is a local-first proof of concept optimized for fast setup and demoability.
- SQLite is sufficient for the expected one-day prototype scope.
- If no OpenAI API key is configured, the app falls back to heuristic metadata generation so the local workflow remains usable.
- The committed starter evaluation set is a workflow example, not the final 50-100 image benchmark requested in the prompt.

## Evaluation Workflow

1. Add evaluation images under `eval/dataset/images/`.
2. Label expected metadata in `eval/dataset/starter_labels.jsonl` or another JSONL file with the same schema.
3. Run:

```bash
./.venv/bin/python -m eval.evaluate --dataset eval/dataset/starter_labels.jsonl
```

4. Inspect the generated report in `eval/results/latest_report.json`.

## Testing

The current automated coverage includes:

- unit parsing coverage for model output normalization
- integration tests for upload persistence and location/time filter behavior
- annotation search coverage
- an end-to-end style upload -> classify -> filter flow

Run the suite with:

```bash
./.venv/bin/python -m pytest
```

Current status: `7 passed`

## Known Limitations

- Search is lexical rather than embedding-based, so natural-language matching is still shallow.
- The fallback classifier relies heavily on filename cues and lightweight color heuristics, which is useful for demoing but not production quality.
- Location inference is only as strong as the model response or filename hints; there is no geocoding or EXIF enrichment yet.
- The evaluation starter set is intentionally tiny and should be replaced with a 50-100 image labeled benchmark for a proper submission.
- There are two non-blocking dependency warnings still visible in test runs: `imghdr` deprecation and a Pillow `getdata()` deprecation path.

## Next Steps

- replace the starter eval set with a real 50-100 image benchmark
- improve color palette extraction and list-field scoring
- upgrade search from substring matching to semantic retrieval
- add richer model prompting and stronger structured validation for OpenAI responses

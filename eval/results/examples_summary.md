# Examples Evaluation Summary

## Dataset

- Source: `data/examples/`
- Labeled set: `eval/dataset/examples_labels.jsonl`
- Sample count: `56`

## Runtime Context

This run evaluated the current fallback classifier rather than a live OpenAI model response.

Reason:

- the evaluation command was executed in an environment where outbound API calls were not available
- the classifier therefore fell back to the local heuristic path for every image

## Per-Attribute Accuracy

Measured attributes from the manual labels:

- `garment_type`: `0 / 56` = `0.00`
- `style`: `0 / 56` = `0.00`
- `material`: `0 / 47` = `0.00`
- `occasion`: `0 / 56` = `0.00`

Not meaningfully measured in this image-only labeling pass:

- `continent`
- `country`
- `city`

Those fields were left unlabeled because city/country ground truth is not reliably recoverable from the images alone.

## What The Classifier Did

The fallback classifier depends mostly on filename keywords plus a basic color heuristic.

Across this dataset it predicted:

- `garment_type`: always `null`
- `style`: always `null`
- `occasion`: always `null`
- `city`: always `null`
- `material`: `cotton` for `7` images and `null` otherwise

Because the Pexels filenames do not usually contain garment or style terms like `dress`, `jacket`, `tailored`, or city names, the heuristic path produced almost no structured fashion metadata.

## Where It Performs Well

- The evaluation pipeline itself is working end to end: manual labels, classifier run, report generation, and error analysis all completed successfully.
- The fallback color extraction still gives some usable palette hints, even though palette accuracy was not part of this specific labeled pass.
- The current approach can work better on datasets where filenames contain strong fashion keywords such as `denim_jacket_tokyo.jpg`.

## Where It Struggles

- Garment recognition from image pixels is effectively absent in fallback mode.
- Style and occasion classification are also absent unless those words appear in the filename.
- Location context cannot be inferred without either model reasoning or external metadata.
- Material inference is too weak and currently biased toward occasional filename matches like `cottonbro`.

## How To Improve With More Time

- Restore live multimodal model evaluation with an API-enabled environment and sufficient quota.
- Expand the prompt and parser to encourage more consistent structured outputs across garment, material, occasion, and contextual fields.
- Replace the fallback heuristic with a vision-based local model or a richer CV pipeline instead of filename-only rules.
- Add a separate evaluation pass for color palette and pattern, where image-derived heuristics may be more competitive.
- Add source metadata or manual annotations for location context if city/country evaluation is a requirement.

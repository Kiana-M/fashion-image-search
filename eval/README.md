# Evaluation

This directory contains the dataset and runner used for model evaluation.

## Evaluated Attribute Groups

- `core_fashion`: `garment_type`, `style`, `material`, `occasion`
- `context`: `continent`, `country`, `city`
- `visual_detail`: `pattern`, `season`, `color_palette`, `trend_notes`

## Metrics

- `accuracy`: exact-match accuracy for scalar attributes and exact-set match for list attributes
- `prediction_coverage`: percentage of samples where the classifier returned a non-empty value
- `macro_accuracy`: unweighted average of measured attribute accuracies
- `micro_accuracy`: total correct predictions divided by total measured labels

## Commands

Run the default evaluation:

```bash
./.venv/bin/python fashion_eval.py
```

Run a specific dataset and report target:

```bash
./.venv/bin/python fashion_eval.py --dataset eval/dataset/examples_labels.jsonl --output eval/results/examples_report.json
```

If you want to force a fallback-only evaluation without attempting OpenAI:

```bash
OPENAI_API_KEY='' ./.venv/bin/python fashion_eval.py --dataset eval/dataset/examples_labels.jsonl --output eval/results/examples_report.json
```

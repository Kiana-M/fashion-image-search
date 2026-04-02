import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.models import ClassificationResult
from app.services import classify_image


SCALAR_ATTRIBUTES = [
    "garment_type",
    "style",
    "material",
    "pattern",
    "season",
    "occasion",
    "consumer_profile",
    "continent",
    "country",
    "city",
]

LIST_ATTRIBUTES = [
    "color_palette",
    "trend_notes",
]


@dataclass
class EvaluationRow:
    image_path: str
    description: str
    garment_type: str | None = None
    style: str | None = None
    material: str | None = None
    color_palette: list[str] | None = None
    pattern: str | None = None
    season: str | None = None
    occasion: str | None = None
    consumer_profile: str | None = None
    trend_notes: list[str] | None = None
    continent: str | None = None
    country: str | None = None
    city: str | None = None
    notes: str | None = None


def load_dataset(dataset_path: Path) -> list[EvaluationRow]:
    rows: list[EvaluationRow] = []
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            try:
                rows.append(EvaluationRow(**payload))
            except TypeError as exc:
                raise ValueError(
                    f"Invalid dataset row on line {line_number} in {dataset_path}: {exc}"
                ) from exc
    return rows


def _normalize_scalar(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return sorted({_normalize_scalar(item) for item in value if _normalize_scalar(item)})
    return [_normalize_scalar(value)] if _normalize_scalar(value) else []


def evaluate_prediction(expected: EvaluationRow, predicted: ClassificationResult) -> dict[str, bool | None]:
    results: dict[str, bool | None] = {}
    attributes = predicted.attributes

    for field_name in SCALAR_ATTRIBUTES:
        expected_value = _normalize_scalar(getattr(expected, field_name))
        if expected_value is None:
            results[field_name] = None
            continue
        predicted_value = _normalize_scalar(getattr(attributes, field_name))
        results[field_name] = predicted_value == expected_value

    for field_name in LIST_ATTRIBUTES:
        expected_values = _normalize_list(getattr(expected, field_name))
        if not expected_values:
            results[field_name] = None
            continue
        predicted_values = _normalize_list(getattr(attributes, field_name))
        results[field_name] = predicted_values == expected_values

    return results


def summarize_scores(score_rows: list[dict[str, bool | None]]) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for field_name in [*SCALAR_ATTRIBUTES, *LIST_ATTRIBUTES]:
        measured = [row[field_name] for row in score_rows if row[field_name] is not None]
        correct = [value for value in measured if value is True]
        total = len(measured)
        summary[field_name] = {
            "correct": len(correct),
            "total": total,
            "accuracy": round(len(correct) / total, 4) if total else 0.0,
        }
    return summary


def build_error_analysis(
    dataset: list[EvaluationRow],
    predictions: list[ClassificationResult],
    score_rows: list[dict[str, bool | None]],
) -> dict[str, Any]:
    misses_by_attribute: dict[str, list[dict[str, Any]]] = defaultdict(list)
    failure_counter = Counter()

    for row, prediction, scores in zip(dataset, predictions, score_rows):
        for field_name, value in scores.items():
            if value is False:
                failure_counter[field_name] += 1
                misses_by_attribute[field_name].append(
                    {
                        "image_path": row.image_path,
                        "expected": getattr(row, field_name),
                        "predicted": getattr(prediction.attributes, field_name),
                    }
                )

    weakest_attributes = [name for name, _count in failure_counter.most_common(3)]
    return {
        "weakest_attributes": weakest_attributes,
        "sample_errors": {name: misses_by_attribute[name][:5] for name in weakest_attributes},
    }


def run_evaluation(dataset_path: Path) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    predictions: list[ClassificationResult] = []
    score_rows: list[dict[str, bool | None]] = []

    for row in dataset:
        prediction = classify_image(Path(row.image_path), Path(row.image_path).name)
        predictions.append(prediction)
        score_rows.append(evaluate_prediction(row, prediction))

    return {
        "dataset_path": str(dataset_path),
        "sample_count": len(dataset),
        "per_attribute_accuracy": summarize_scores(score_rows),
        "error_analysis": build_error_analysis(dataset, predictions, score_rows),
        "predictions": [
            {
                "image_path": row.image_path,
                "expected": asdict(row),
                "predicted": prediction.model_dump(),
                "scores": scores,
            }
            for row, prediction, scores in zip(dataset, predictions, score_rows)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the fashion image classifier.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("eval/dataset/starter_labels.jsonl"),
        help="Path to a JSONL dataset with expected labels.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eval/results/latest_report.json"),
        help="Path for the generated evaluation report.",
    )
    args = parser.parse_args()

    report = run_evaluation(args.dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote evaluation report to {args.output}")
    print(json.dumps(report["per_attribute_accuracy"], indent=2))


if __name__ == "__main__":
    main()

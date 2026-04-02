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

ATTRIBUTE_GROUPS = {
    "core_fashion": ["garment_type", "style", "material", "occasion"],
    "context": ["continent", "country", "city"],
    "visual_detail": ["pattern", "season", "color_palette", "trend_notes"],
}

CANONICAL_ALIASES = {
    "garment_type": {
        "set": ["set", "matching set", "co-ord", "co ord", "coord", "two-piece", "two piece"],
        "blazer": ["blazer"],
        "dress": ["dress", "evening dress", "gown"],
        "coat": ["coat", "outerwear"],
        "jacket": ["jacket", "hooded jacket"],
        "jeans": ["jeans", "denim jeans"],
        "shirt": ["shirt", "button-up shirt", "button up shirt"],
        "pants": ["pants", "trousers", "wide-leg pants", "wide leg pants"],
        "tank top": ["tank top", "tank"],
        "top": ["top", "crop top", "cropped top"],
        "suit": ["suit"],
        "skirt": ["skirt", "long skirt"],
        "hoodie": ["hoodie"],
        "sweatshirt": ["sweatshirt"],
        "jumpsuit": ["jumpsuit"],
        "blazer dress": ["blazer dress"],
    },
    "style": {
        "tailored": ["tailored", "minimal tailored", "modern tailored"],
        "minimal": ["minimal", "minimalist"],
        "streetwear": ["streetwear", "street style", "urban streetwear", "casual streetwear"],
        "casual": ["casual", "everyday wear"],
        "editorial": ["editorial", "fashion editorial", "fashion-forward streetwear"],
        "formal": ["formal", "formalwear"],
        "evening": ["evening", "eveningwear"],
        "resort": ["resort"],
        "utility": ["utility", "utilitarian"],
        "traditional": ["traditional"],
        "bridal": ["bridal"],
        "bohemian": ["bohemian"],
        "maximalist": ["maximalist", "opulent"],
        "fashion street": ["fashion street", "street style"],
        "loungewear": ["loungewear", "lounge"],
    },
    "material": {
        "woven": ["woven", "wool", "polyester blend", "cotton blend", "blend"],
        "denim": ["denim", "denim jeans", "denim coat"],
        "cotton": ["cotton", "cotton-blend", "cotton blend"],
        "wool": ["wool"],
        "knit": ["knit", "knitted"],
        "tulle": ["tulle"],
        "sheer": ["sheer"],
        "satin": ["satin"],
        "metallic": ["metallic"],
        "nylon": ["nylon"],
    },
    "occasion": {
        "casual": ["casual", "everyday wear"],
        "formal": ["formal", "professional"],
        "editorial": ["editorial", "fashion editorial"],
        "occasionwear": ["occasionwear", "special occasion", "formal events", "evening occasions"],
        "eveningwear": ["eveningwear", "evening occasions"],
        "daywear": ["daywear", "daytime", "daytime casual"],
        "workwear": ["workwear", "business casual", "work", "professional"],
        "party": ["party"],
        "fashion street": ["streetwear", "street style", "fashion-forward streetwear"],
    },
}


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


def _canonicalize_scalar(field_name: str, value: Any) -> str | None:
    normalized = _normalize_scalar(value)
    if normalized is None:
        return None
    aliases = CANONICAL_ALIASES.get(field_name)
    if not aliases:
        return normalized
    for canonical, variants in aliases.items():
        if canonical == normalized:
            return canonical
        if any(variant in normalized for variant in variants):
            return canonical
    return normalized


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
        expected_value = _canonicalize_scalar(field_name, getattr(expected, field_name))
        if expected_value is None:
            results[field_name] = None
            continue
        predicted_value = _canonicalize_scalar(field_name, getattr(attributes, field_name))
        results[field_name] = predicted_value == expected_value

    for field_name in LIST_ATTRIBUTES:
        expected_values = _normalize_list(getattr(expected, field_name))
        if not expected_values:
            results[field_name] = None
            continue
        predicted_values = _normalize_list(getattr(attributes, field_name))
        results[field_name] = predicted_values == expected_values

    return results


def summarize_scores(
    dataset: list[EvaluationRow],
    predictions: list[ClassificationResult],
    score_rows: list[dict[str, bool | None]],
) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for field_name in [*SCALAR_ATTRIBUTES, *LIST_ATTRIBUTES]:
        measured = [row[field_name] for row in score_rows if row[field_name] is not None]
        correct = [value for value in measured if value is True]
        total = len(measured)
        predicted_non_empty = 0
        for prediction in predictions:
            predicted_value = getattr(prediction.attributes, field_name)
            if field_name in LIST_ATTRIBUTES:
                if _normalize_list(predicted_value):
                    predicted_non_empty += 1
            elif _canonicalize_scalar(field_name, predicted_value) is not None:
                predicted_non_empty += 1
        summary[field_name] = {
            "correct": len(correct),
            "total": total,
            "accuracy": round(len(correct) / total, 4) if total else 0.0,
            "prediction_coverage": round(predicted_non_empty / len(dataset), 4) if dataset else 0.0,
        }
    return summary


def summarize_groups(per_attribute_accuracy: dict[str, dict[str, float | int]]) -> dict[str, dict[str, float | int]]:
    group_summary: dict[str, dict[str, float | int]] = {}
    for group_name, attributes in ATTRIBUTE_GROUPS.items():
        measured = [per_attribute_accuracy[name]["total"] for name in attributes]
        total = sum(int(value) for value in measured)
        correct = sum(int(per_attribute_accuracy[name]["correct"]) for name in attributes)
        macro_values = [
            float(per_attribute_accuracy[name]["accuracy"])
            for name in attributes
            if int(per_attribute_accuracy[name]["total"]) > 0
        ]
        group_summary[group_name] = {
            "correct": correct,
            "total": total,
            "micro_accuracy": round(correct / total, 4) if total else 0.0,
            "macro_accuracy": round(sum(macro_values) / len(macro_values), 4) if macro_values else 0.0,
        }
    return group_summary


def summarize_overall(per_attribute_accuracy: dict[str, dict[str, float | int]]) -> dict[str, float | int]:
    measured_attributes = [
        metrics for metrics in per_attribute_accuracy.values() if int(metrics["total"]) > 0
    ]
    total = sum(int(metrics["total"]) for metrics in measured_attributes)
    correct = sum(int(metrics["correct"]) for metrics in measured_attributes)
    macro_values = [float(metrics["accuracy"]) for metrics in measured_attributes]
    return {
        "correct": correct,
        "total": total,
        "micro_accuracy": round(correct / total, 4) if total else 0.0,
        "macro_accuracy": round(sum(macro_values) / len(macro_values), 4) if macro_values else 0.0,
    }


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


def run_evaluation(dataset_path: Path, *, require_openai: bool = False) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    predictions: list[ClassificationResult] = []
    score_rows: list[dict[str, bool | None]] = []

    for row in dataset:
        prediction = classify_image(
            Path(row.image_path),
            Path(row.image_path).name,
            allow_fallback=not require_openai,
        )
        predictions.append(prediction)
        score_rows.append(evaluate_prediction(row, prediction))

    per_attribute_accuracy = summarize_scores(dataset, predictions, score_rows)

    return {
        "dataset_path": str(dataset_path),
        "sample_count": len(dataset),
        "attribute_groups": ATTRIBUTE_GROUPS,
        "metrics_definition": {
            "accuracy": "Exact-match accuracy for scalar attributes and full-set exact match for list attributes.",
            "prediction_coverage": "Share of samples where the classifier returned a non-empty value for the attribute.",
            "macro_accuracy": "Unweighted mean of per-attribute accuracies across measured attributes.",
            "micro_accuracy": "Total correct predictions divided by total measured labels.",
        },
        "per_attribute_accuracy": per_attribute_accuracy,
        "group_accuracy": summarize_groups(per_attribute_accuracy),
        "overall_accuracy": summarize_overall(per_attribute_accuracy),
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
    parser.add_argument(
        "--require-openai",
        action="store_true",
        help="Fail the evaluation if any sample cannot be classified by the OpenAI model.",
    )
    args = parser.parse_args()

    report = run_evaluation(args.dataset, require_openai=args.require_openai)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote evaluation report to {args.output}")
    print(json.dumps(report["overall_accuracy"], indent=2))
    print(json.dumps(report["group_accuracy"], indent=2))
    print(json.dumps(report["per_attribute_accuracy"], indent=2))


if __name__ == "__main__":
    main()

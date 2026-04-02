import json
from typing import Any, Dict, Iterable, Optional

from pydantic import ValidationError

from app.logging_utils import get_logger
from app.models import ClassificationResult, GarmentAttributes


LIST_FIELDS = {"color_palette", "trend_notes"}
logger = get_logger(__name__)


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _coerce_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    attributes = payload.get("attributes") or {}
    normalized_attributes: Dict[str, Any] = {}

    for field_name in GarmentAttributes.model_fields:
        value = attributes.get(field_name)
        if field_name in LIST_FIELDS:
            normalized_attributes[field_name] = _normalize_list(value)
        elif value in ("", [], {}):
            normalized_attributes[field_name] = None
        else:
            normalized_attributes[field_name] = value

    return {
        "description": str(payload.get("description", "")).strip(),
        "attributes": normalized_attributes,
    }


def extract_json_object(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        logger.error("Model output was empty during JSON extraction.")
        raise ValueError("Model output was empty.")

    try:
        logger.debug("Attempting direct JSON parse of model output.")
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            logger.error("Model output did not contain a valid JSON object.")
            raise ValueError("Model output did not contain a JSON object.")
        logger.debug("Recovered JSON object from surrounding text in model output.")
        return json.loads(stripped[start : end + 1])


def parse_classification_output(
    payload: Any,
    *,
    source: str,
    model_name: Optional[str] = None,
    raw_response: Optional[str] = None,
) -> ClassificationResult:
    logger.info("Parsing classification output from source=%s model=%s", source, model_name)
    if isinstance(payload, str):
        raw_text = payload
        payload_dict = extract_json_object(payload)
    else:
        payload_dict = payload
        raw_text = raw_response or json.dumps(payload, ensure_ascii=True)

    normalized = _coerce_payload(payload_dict)
    if not normalized["description"]:
        logger.error("Parsed model payload is missing a description.")
        raise ValueError("Model output must include a description.")

    try:
        result = ClassificationResult.model_validate(
            {
                **normalized,
                "source": source,
                "model_name": model_name,
                "raw_response": raw_response or raw_text,
            }
        )
    except ValidationError as exc:
        logger.exception("Failed to validate parsed classification payload.")
        raise ValueError(f"Failed to parse classification output: {exc}") from exc

    logger.info("Successfully parsed classification output from source=%s model=%s", source, model_name)
    return result

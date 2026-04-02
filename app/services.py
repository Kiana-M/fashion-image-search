import base64
import imghdr
import json
import uuid
from collections import Counter
from pathlib import Path
from typing import Optional

from PIL import Image

from app.config import OPENAI_API_KEY, OPENAI_MODEL, UPLOAD_DIR
from app.library import LibraryFilters, build_filter_options, filter_records
from app.models import Annotation, ClassificationResult, GarmentAttributes, ImageRecord
from app.parsing import parse_classification_output
from app.repository import create_image_record, list_image_records, save_annotation, save_classification

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


CLASSIFICATION_PROMPT = """
You are classifying a fashion inspiration image for a design team.
Return a single JSON object with this exact shape:
{
  "description": "rich natural-language description",
  "attributes": {
    "garment_type": "string or null",
    "style": "string or null",
    "material": "string or null",
    "color_palette": ["string"],
    "pattern": "string or null",
    "season": "string or null",
    "occasion": "string or null",
    "consumer_profile": "string or null",
    "trend_notes": ["string"],
    "continent": "string or null",
    "country": "string or null",
    "city": "string or null"
  }
}
Use null for unknown scalar values and [] for unknown list values.
Do not include markdown fences or extra commentary.
""".strip()


def _guess_extension(file_bytes: bytes, original_name: str) -> str:
    original_extension = Path(original_name).suffix.lower()
    if original_extension in {".jpg", ".jpeg", ".png", ".webp"}:
        return original_extension

    detected = imghdr.what(None, h=file_bytes)
    mapping = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}
    return mapping.get(detected or "", ".jpg")


def persist_upload(file_name: str, file_bytes: bytes, upload_dir: Path = UPLOAD_DIR) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    extension = _guess_extension(file_bytes, file_name)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    destination = upload_dir / stored_name
    destination.write_bytes(file_bytes)
    return destination


def _closest_color_name(rgb: tuple[int, int, int]) -> str:
    palette = {
        "black": (20, 20, 20),
        "white": (235, 235, 235),
        "gray": (140, 140, 140),
        "beige": (210, 190, 150),
        "brown": (120, 80, 50),
        "red": (190, 55, 50),
        "orange": (225, 135, 55),
        "yellow": (220, 200, 70),
        "green": (70, 140, 90),
        "blue": (60, 100, 175),
        "purple": (120, 90, 150),
        "pink": (210, 140, 170),
    }
    best_name = "mixed"
    best_distance = float("inf")
    for name, target in palette.items():
        distance = sum((component - baseline) ** 2 for component, baseline in zip(rgb, target))
        if distance < best_distance:
            best_name = name
            best_distance = distance
    return best_name


def _extract_palette(image_path: Path) -> list[str]:
    try:
        with Image.open(image_path) as image:
            reduced = image.convert("RGB").resize((100, 100))
            colors = reduced.getdata()
    except OSError:
        return []

    counts = Counter(_closest_color_name(pixel) for pixel in colors)
    return [name for name, _count in counts.most_common(3)]


def _attribute_from_keywords(name: str, mapping: dict[str, str]) -> Optional[str]:
    lowered = name.lower()
    for keyword, value in mapping.items():
        if keyword in lowered:
            return value
    return None


def build_fallback_classification(image_path: Path, file_name: str) -> ClassificationResult:
    lowered = file_name.lower()
    garment_type = _attribute_from_keywords(
        lowered,
        {
            "dress": "dress",
            "jacket": "jacket",
            "coat": "coat",
            "skirt": "skirt",
            "pant": "pants",
            "trouser": "pants",
            "shirt": "shirt",
            "tee": "t-shirt",
            "sneaker": "footwear",
            "boot": "footwear",
            "bag": "accessory",
        },
    )
    style = _attribute_from_keywords(
        lowered,
        {
            "street": "streetwear",
            "tailored": "tailored",
            "sport": "sport",
            "market": "artisan market",
            "vintage": "vintage",
            "denim": "casual denim",
        },
    )
    material = _attribute_from_keywords(
        lowered,
        {
            "denim": "denim",
            "leather": "leather",
            "knit": "knit",
            "linen": "linen",
            "wool": "wool",
            "cotton": "cotton",
            "silk": "silk",
        },
    )
    pattern = _attribute_from_keywords(
        lowered,
        {
            "stripe": "striped",
            "floral": "floral",
            "plaid": "plaid",
            "check": "checked",
            "embroider": "embroidered",
        },
    )
    occasion = _attribute_from_keywords(
        lowered,
        {
            "evening": "eveningwear",
            "formal": "formal",
            "work": "workwear",
            "sport": "active",
            "market": "travel/shopping",
        },
    )
    city = _attribute_from_keywords(
        lowered,
        {
            "tokyo": "Tokyo",
            "seoul": "Seoul",
            "milan": "Milan",
            "paris": "Paris",
            "lagos": "Lagos",
            "nyc": "New York",
            "newyork": "New York",
        },
    )
    color_palette = _extract_palette(image_path)
    description = (
        f"Fallback classification for {file_name}. "
        f"The image appears to emphasize a {garment_type or 'fashion item'} with "
        f"{pattern or 'minimal'} surface detail and a palette dominated by "
        f"{', '.join(color_palette) if color_palette else 'mixed tones'}."
    )

    return ClassificationResult(
        description=description,
        attributes=GarmentAttributes(
            garment_type=garment_type,
            style=style,
            material=material,
            color_palette=color_palette,
            pattern=pattern,
            season="transitional" if "coat" in lowered or "jacket" in lowered else None,
            occasion=occasion,
            consumer_profile="fashion-forward urban consumer",
            trend_notes=[note for note in [style, pattern] if note],
            continent=None,
            country=None,
            city=city,
        ),
        source="fallback",
        model_name=None,
        raw_response=json.dumps({"fallback": True, "file_name": file_name}, ensure_ascii=True),
    )


def classify_with_openai(image_path: Path) -> ClassificationResult:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    if OpenAI is None:
        raise RuntimeError("openai package is not installed.")

    encoded_image = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    image_format = image_path.suffix.lstrip(".") or "jpeg"
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": CLASSIFICATION_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Classify this fashion inspiration image.",
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/{image_format};base64,{encoded_image}",
                    },
                ],
            },
        ],
    )
    raw_text = getattr(response, "output_text", "") or ""
    return parse_classification_output(
        raw_text,
        source="openai",
        model_name=OPENAI_MODEL,
        raw_response=raw_text,
    )


def classify_image(image_path: Path, file_name: str) -> ClassificationResult:
    try:
        return classify_with_openai(image_path)
    except Exception:
        return build_fallback_classification(image_path, file_name)


def process_upload(
    *,
    file_name: str,
    file_bytes: bytes,
    designer: Optional[str] = None,
    captured_at: Optional[str] = None,
    db_path: Optional[Path] = None,
    upload_dir: Path = UPLOAD_DIR,
) -> tuple[ImageRecord, ClassificationResult]:
    saved_path = persist_upload(file_name, file_bytes, upload_dir=upload_dir)
    image_id = create_image_record(
        file_name=file_name,
        file_path=str(saved_path),
        designer=designer,
        captured_at=captured_at,
        db_path=db_path,
    )
    result = classify_image(saved_path, file_name)
    save_classification(image_id, result, db_path=db_path)
    image_record = list_image_records(db_path=db_path)[0]
    return image_record, result


def load_recent_images(*, db_path: Optional[Path] = None) -> list[ImageRecord]:
    return list_image_records(db_path=db_path)


def save_designer_annotation(
    image_id: int,
    *,
    tags_text: str,
    notes: str,
    db_path: Optional[Path] = None,
) -> None:
    tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    save_annotation(image_id, Annotation(tags=tags, notes=notes.strip()), db_path=db_path)


def search_library(
    filters: LibraryFilters,
    *,
    db_path: Optional[Path] = None,
) -> list[ImageRecord]:
    records = list_image_records(db_path=db_path)
    return filter_records(records, filters)


def get_filter_options(*, db_path: Optional[Path] = None) -> dict[str, list[str]]:
    records = list_image_records(db_path=db_path)
    return build_filter_options(records)

import json
from pathlib import Path
from typing import Optional

from app.db import get_connection
from app.models import ClassificationResult, ImageRecord


def create_image_record(
    *,
    file_name: str,
    file_path: str,
    designer: Optional[str],
    captured_at: Optional[str],
    db_path: Optional[Path] = None,
) -> int:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO images (file_name, file_path, designer, captured_at)
            VALUES (?, ?, ?, ?)
            """,
            (file_name, file_path, designer, captured_at),
        )
        return int(cursor.lastrowid)


def save_classification(
    image_id: int,
    result: ClassificationResult,
    *,
    db_path: Optional[Path] = None,
) -> None:
    attributes = result.attributes
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO ai_classifications (
                image_id,
                description,
                garment_type,
                style,
                material,
                color_palette,
                pattern,
                season,
                occasion,
                consumer_profile,
                trend_notes,
                continent,
                country,
                city,
                source,
                model_name,
                raw_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(image_id) DO UPDATE SET
                description = excluded.description,
                garment_type = excluded.garment_type,
                style = excluded.style,
                material = excluded.material,
                color_palette = excluded.color_palette,
                pattern = excluded.pattern,
                season = excluded.season,
                occasion = excluded.occasion,
                consumer_profile = excluded.consumer_profile,
                trend_notes = excluded.trend_notes,
                continent = excluded.continent,
                country = excluded.country,
                city = excluded.city,
                source = excluded.source,
                model_name = excluded.model_name,
                raw_response = excluded.raw_response,
                classified_at = CURRENT_TIMESTAMP
            """,
            (
                image_id,
                result.description,
                attributes.garment_type,
                attributes.style,
                attributes.material,
                json.dumps(attributes.color_palette),
                attributes.pattern,
                attributes.season,
                attributes.occasion,
                attributes.consumer_profile,
                json.dumps(attributes.trend_notes),
                attributes.continent,
                attributes.country,
                attributes.city,
                result.source,
                result.model_name,
                result.raw_response,
            ),
        )


def list_image_records(*, db_path: Optional[Path] = None) -> list[ImageRecord]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                images.id,
                images.file_name,
                images.file_path,
                images.designer,
                images.captured_at,
                images.created_at,
                ai_classifications.description,
                ai_classifications.garment_type,
                ai_classifications.style,
                ai_classifications.material,
                ai_classifications.color_palette,
                ai_classifications.pattern,
                ai_classifications.season,
                ai_classifications.occasion,
                ai_classifications.consumer_profile,
                ai_classifications.trend_notes,
                ai_classifications.continent,
                ai_classifications.country,
                ai_classifications.city,
                ai_classifications.source AS classification_source,
                ai_classifications.model_name
            FROM images
            LEFT JOIN ai_classifications
                ON ai_classifications.image_id = images.id
            ORDER BY images.created_at DESC, images.id DESC
            """
        ).fetchall()

    records: list[ImageRecord] = []
    for row in rows:
        records.append(
            ImageRecord(
                id=row["id"],
                file_name=row["file_name"],
                file_path=row["file_path"],
                designer=row["designer"],
                captured_at=row["captured_at"],
                created_at=row["created_at"],
                description=row["description"],
                garment_type=row["garment_type"],
                style=row["style"],
                material=row["material"],
                color_palette=json.loads(row["color_palette"]) if row["color_palette"] else [],
                pattern=row["pattern"],
                season=row["season"],
                occasion=row["occasion"],
                consumer_profile=row["consumer_profile"],
                trend_notes=json.loads(row["trend_notes"]) if row["trend_notes"] else [],
                continent=row["continent"],
                country=row["country"],
                city=row["city"],
                classification_source=row["classification_source"],
                model_name=row["model_name"],
            )
        )
    return records

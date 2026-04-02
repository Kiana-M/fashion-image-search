from app.library import LibraryFilters
from app.services import process_upload, save_designer_annotation, search_library

from tests.conftest import PNG_BYTES


def test_location_and_time_filters_use_stored_metadata(temp_db, tmp_path) -> None:
    upload_dir = tmp_path / "uploads"
    process_upload(
        file_name="tokyo_denim_jacket.png",
        file_bytes=PNG_BYTES,
        designer="Alex",
        captured_at="2026-04-01",
        db_path=temp_db,
        upload_dir=upload_dir,
    )
    process_upload(
        file_name="paris_evening_dress.png",
        file_bytes=PNG_BYTES,
        designer="Mina",
        captured_at="2025-09-12",
        db_path=temp_db,
        upload_dir=upload_dir,
    )

    tokyo_results = search_library(
        LibraryFilters(cities=("Tokyo",), years=("2026",)),
        db_path=temp_db,
    )
    paris_results = search_library(
        LibraryFilters(cities=("Paris",), months=("2025-09",)),
        db_path=temp_db,
    )

    assert len(tokyo_results) == 1
    assert tokyo_results[0].file_name == "tokyo_denim_jacket.png"
    assert len(paris_results) == 1
    assert paris_results[0].file_name == "paris_evening_dress.png"


def test_search_includes_designer_annotations(temp_db, tmp_path) -> None:
    upload_dir = tmp_path / "uploads"
    record, _result = process_upload(
        file_name="market_top.png",
        file_bytes=PNG_BYTES,
        designer="Alex",
        captured_at="2026-04-01",
        db_path=temp_db,
        upload_dir=upload_dir,
    )

    save_designer_annotation(
        record.id,
        tags_text="embroidery, neckline",
        notes="Strong artisan market reference and embellished neckline.",
        db_path=temp_db,
    )

    results = search_library(LibraryFilters(query="artisan market"), db_path=temp_db)
    tag_results = search_library(LibraryFilters(annotation_tags=("neckline",)), db_path=temp_db)

    assert len(results) == 1
    assert len(tag_results) == 1
    assert results[0].annotation_tags == ["embroidery", "neckline"]
    assert "embellished neckline" in results[0].annotation_notes

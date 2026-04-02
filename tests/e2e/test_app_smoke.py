from app.library import LibraryFilters
from app.services import process_upload, search_library

from tests.conftest import PNG_BYTES


def test_upload_classify_and_filter_flow(temp_db, tmp_path) -> None:
    upload_dir = tmp_path / "uploads"
    record, result = process_upload(
        file_name="tokyo_denim_jacket.png",
        file_bytes=PNG_BYTES,
        designer="Alex",
        captured_at="2026-04-01",
        db_path=temp_db,
        upload_dir=upload_dir,
    )

    results = search_library(
        LibraryFilters(
            query="jacket",
            cities=("Tokyo",),
            years=("2026",),
            designers=("Alex",),
            materials=("denim",),
        ),
        db_path=temp_db,
    )

    assert result.description
    assert record.id == results[0].id
    assert len(results) == 1

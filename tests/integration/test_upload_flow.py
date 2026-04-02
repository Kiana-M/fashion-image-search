from pathlib import Path

from app.services import process_upload

from tests.conftest import PNG_BYTES


def test_process_upload_persists_image_and_metadata(temp_db, tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    image_record, result = process_upload(
        file_name="tokyo_denim_jacket.png",
        file_bytes=PNG_BYTES,
        designer="Alex",
        captured_at="2026-04-01",
        db_path=temp_db,
        upload_dir=upload_dir,
    )

    assert image_record.file_name == "tokyo_denim_jacket.png"
    assert image_record.designer == "Alex"
    assert image_record.description
    assert Path(image_record.file_path).exists()
    assert result.attributes.garment_type == "jacket"
    assert result.attributes.material == "denim"
    assert result.source in {"openai", "fallback"}

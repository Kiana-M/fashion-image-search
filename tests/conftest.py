from io import BytesIO
from pathlib import Path
import sqlite3

import pytest
from PIL import Image

from app.db import SCHEMA


buffer = BytesIO()
Image.new("RGB", (4, 4), color=(44, 82, 160)).save(buffer, format="PNG")
PNG_BYTES = buffer.getvalue()


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA)
        connection.commit()
    return db_path

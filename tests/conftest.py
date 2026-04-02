from pathlib import Path
import sqlite3

import pytest

from app.db import SCHEMA


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA)
        connection.commit()
    return db_path

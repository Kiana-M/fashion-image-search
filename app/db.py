import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import DB_PATH, UPLOAD_DIR


SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    designer TEXT,
    captured_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_classifications (
    image_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    garment_type TEXT,
    style TEXT,
    material TEXT,
    color_palette TEXT,
    pattern TEXT,
    season TEXT,
    occasion TEXT,
    consumer_profile TEXT,
    trend_notes TEXT,
    continent TEXT,
    country TEXT,
    city TEXT,
    source TEXT,
    model_name TEXT,
    classified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_response TEXT,
    FOREIGN KEY(image_id) REFERENCES images(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS annotations (
    image_id INTEGER PRIMARY KEY,
    tags TEXT,
    notes TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(image_id) REFERENCES images(id) ON DELETE CASCADE
);
"""


def ensure_directories() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def init_db(db_path: Path = DB_PATH) -> None:
    ensure_directories()
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA)
        connection.commit()


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()

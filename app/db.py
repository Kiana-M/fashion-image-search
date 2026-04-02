import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import DB_PATH, UPLOAD_DIR
from app.logging_utils import get_logger


logger = get_logger(__name__)


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
    logger.info("Ensured upload directory exists at %s", UPLOAD_DIR)


def resolve_db_path(db_path: Path | None = None) -> Path:
    return db_path or DB_PATH


def init_db(db_path: Path | None = None) -> None:
    resolved_db_path = resolve_db_path(db_path)
    ensure_directories()
    logger.info("Initializing SQLite database at %s", resolved_db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.executescript(SCHEMA)
        connection.commit()
    logger.info("Database initialization complete at %s", resolved_db_path)


@contextmanager
def get_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    resolved_db_path = resolve_db_path(db_path)
    logger.debug("Opening SQLite connection to %s", resolved_db_path)
    connection = sqlite3.connect(resolved_db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
        logger.debug("Committed SQLite transaction to %s", resolved_db_path)
    finally:
        connection.close()
        logger.debug("Closed SQLite connection to %s", resolved_db_path)

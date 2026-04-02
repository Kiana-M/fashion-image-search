import sqlite3

from app.db import init_db


def test_init_db_creates_expected_tables(temp_db) -> None:
    init_db(temp_db)

    with sqlite3.connect(temp_db) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row[0] for row in rows}
    assert {"images", "ai_classifications", "annotations"}.issubset(table_names)

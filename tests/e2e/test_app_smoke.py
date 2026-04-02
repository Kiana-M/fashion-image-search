from app.library import LibraryFilters
from app.services import search_library


def test_empty_library_search_returns_no_results(temp_db) -> None:
    results = search_library(LibraryFilters(query="embroidered neckline"), db_path=temp_db)
    assert results == []

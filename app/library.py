from dataclasses import dataclass
from typing import Iterable

from app.models import ImageRecord


@dataclass
class LibraryFilters:
    query: str = ""
    garment_types: tuple[str, ...] = ()
    styles: tuple[str, ...] = ()
    materials: tuple[str, ...] = ()
    color_palette: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()
    occasions: tuple[str, ...] = ()
    consumer_profiles: tuple[str, ...] = ()
    trend_notes: tuple[str, ...] = ()
    continents: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    cities: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    years: tuple[str, ...] = ()
    months: tuple[str, ...] = ()
    designers: tuple[str, ...] = ()
    annotation_tags: tuple[str, ...] = ()


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _matches_scalar(value: str | None, selected: tuple[str, ...]) -> bool:
    if not selected:
        return True
    return _normalize(value) in {_normalize(item) for item in selected}


def _matches_list(values: list[str], selected: tuple[str, ...]) -> bool:
    if not selected:
        return True
    normalized_values = {_normalize(item) for item in values}
    normalized_selected = {_normalize(item) for item in selected}
    return bool(normalized_values & normalized_selected)


def _captured_year(record: ImageRecord) -> str | None:
    if not record.captured_at:
        return None
    return record.captured_at[:4]


def _captured_month(record: ImageRecord) -> str | None:
    if not record.captured_at or len(record.captured_at) < 7:
        return None
    return record.captured_at[:7]


def _matches_query(record: ImageRecord, query: str) -> bool:
    if not query.strip():
        return True
    haystack = " ".join(
        [
            record.file_name,
            record.description or "",
            record.garment_type or "",
            record.style or "",
            record.material or "",
            record.pattern or "",
            record.occasion or "",
            record.consumer_profile or "",
            record.continent or "",
            record.country or "",
            record.city or "",
            " ".join(record.color_palette),
            " ".join(record.trend_notes),
            " ".join(record.annotation_tags),
            record.annotation_notes,
        ]
    ).lower()
    return query.lower() in haystack


def filter_records(records: Iterable[ImageRecord], filters: LibraryFilters) -> list[ImageRecord]:
    results: list[ImageRecord] = []
    for record in records:
        if not _matches_query(record, filters.query):
            continue
        if not _matches_scalar(record.garment_type, filters.garment_types):
            continue
        if not _matches_scalar(record.style, filters.styles):
            continue
        if not _matches_scalar(record.material, filters.materials):
            continue
        if not _matches_list(record.color_palette, filters.color_palette):
            continue
        if not _matches_scalar(record.pattern, filters.patterns):
            continue
        if not _matches_scalar(record.occasion, filters.occasions):
            continue
        if not _matches_scalar(record.consumer_profile, filters.consumer_profiles):
            continue
        if not _matches_list(record.trend_notes, filters.trend_notes):
            continue
        if not _matches_scalar(record.continent, filters.continents):
            continue
        if not _matches_scalar(record.country, filters.countries):
            continue
        if not _matches_scalar(record.city, filters.cities):
            continue
        if not _matches_scalar(record.season, filters.seasons):
            continue
        if not _matches_scalar(_captured_year(record), filters.years):
            continue
        if not _matches_scalar(_captured_month(record), filters.months):
            continue
        if not _matches_scalar(record.designer, filters.designers):
            continue
        if not _matches_list(record.annotation_tags, filters.annotation_tags):
            continue
        results.append(record)
    return results


def _unique(values: Iterable[str | None]) -> list[str]:
    return sorted({value.strip() for value in values if value and value.strip()})


def build_filter_options(records: Iterable[ImageRecord]) -> dict[str, list[str]]:
    records = list(records)
    return {
        "garment_types": _unique(record.garment_type for record in records),
        "styles": _unique(record.style for record in records),
        "materials": _unique(record.material for record in records),
        "color_palette": _unique(color for record in records for color in record.color_palette),
        "patterns": _unique(record.pattern for record in records),
        "occasions": _unique(record.occasion for record in records),
        "consumer_profiles": _unique(record.consumer_profile for record in records),
        "trend_notes": _unique(note for record in records for note in record.trend_notes),
        "continents": _unique(record.continent for record in records),
        "countries": _unique(record.country for record in records),
        "cities": _unique(record.city for record in records),
        "seasons": _unique(record.season for record in records),
        "years": _unique(_captured_year(record) for record in records),
        "months": _unique(_captured_month(record) for record in records),
        "designers": _unique(record.designer for record in records),
        "annotation_tags": _unique(tag for record in records for tag in record.annotation_tags),
    }

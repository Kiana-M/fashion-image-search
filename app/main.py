import streamlit as st

from app.config import DB_PATH, UPLOAD_DIR
from app.db import init_db
from app.library import LibraryFilters
from app.models import ImageRecord
from app.services import get_filter_options, process_upload, save_designer_annotation, search_library


st.set_page_config(page_title="Fashion Image Search", layout="wide")


def render_sidebar() -> None:
    st.sidebar.title("Fashion Image Search")
    st.sidebar.caption("Local-first inspiration library for design teams.")
    st.sidebar.write(f"Database: `{DB_PATH}`")
    st.sidebar.write(f"Uploads: `{UPLOAD_DIR}`")


def render_filters() -> LibraryFilters:
    options = get_filter_options()
    st.sidebar.subheader("Search and Filters")
    query = st.sidebar.text_input("Natural-language search", placeholder="embroidered neckline")
    garment_types = st.sidebar.multiselect("Garment type", options["garment_types"])
    styles = st.sidebar.multiselect("Style", options["styles"])
    materials = st.sidebar.multiselect("Material", options["materials"])
    colors = st.sidebar.multiselect("Color palette", options["color_palette"])
    patterns = st.sidebar.multiselect("Pattern", options["patterns"])
    occasions = st.sidebar.multiselect("Occasion", options["occasions"])
    consumer_profiles = st.sidebar.multiselect("Consumer profile", options["consumer_profiles"])
    trend_notes = st.sidebar.multiselect("Trend notes", options["trend_notes"])
    continents = st.sidebar.multiselect("Continent", options["continents"])
    countries = st.sidebar.multiselect("Country", options["countries"])
    cities = st.sidebar.multiselect("City", options["cities"])
    seasons = st.sidebar.multiselect("Season", options["seasons"])
    years = st.sidebar.multiselect("Year", options["years"])
    months = st.sidebar.multiselect("Month", options["months"])
    designers = st.sidebar.multiselect("Designer", options["designers"])
    annotation_tags = st.sidebar.multiselect("Designer tags", options["annotation_tags"])
    return LibraryFilters(
        query=query,
        garment_types=tuple(garment_types),
        styles=tuple(styles),
        materials=tuple(materials),
        color_palette=tuple(colors),
        patterns=tuple(patterns),
        occasions=tuple(occasions),
        consumer_profiles=tuple(consumer_profiles),
        trend_notes=tuple(trend_notes),
        continents=tuple(continents),
        countries=tuple(countries),
        cities=tuple(cities),
        seasons=tuple(seasons),
        years=tuple(years),
        months=tuple(months),
        designers=tuple(designers),
        annotation_tags=tuple(annotation_tags),
    )


def render_annotation_editor(record_id: int, tags: list[str], notes: str) -> None:
    with st.expander("Designer annotations", expanded=False):
        with st.form(f"annotation-form-{record_id}"):
            tags_text = st.text_input("Tags", value=", ".join(tags), key=f"tags-{record_id}")
            notes_text = st.text_area("Notes", value=notes, key=f"notes-{record_id}")
            save = st.form_submit_button("Save annotations")
        if save:
            save_designer_annotation(record_id, tags_text=tags_text, notes=notes_text)
            st.success("Annotations saved.")
            st.rerun()


def render_record_card(record: ImageRecord) -> None:
    st.image(record.file_path, use_container_width=True)
    st.markdown(f"**{record.file_name}**")
    meta_lines = [
        f"Designer: {record.designer}" if record.designer else None,
        f"Captured: {record.captured_at}" if record.captured_at else None,
        f"Location: {', '.join([part for part in [record.city, record.country, record.continent] if part])}"
        if any([record.city, record.country, record.continent])
        else None,
    ]
    for line in meta_lines:
        if line:
            st.caption(line)

    if record.description:
        st.write(record.description)

    ai_tags = [
        ("Garment", record.garment_type),
        ("Style", record.style),
        ("Material", record.material),
        ("Pattern", record.pattern),
        ("Season", record.season),
        ("Occasion", record.occasion),
        ("Consumer", record.consumer_profile),
    ]
    visible_ai_tags = [f"{label}: {value}" for label, value in ai_tags if value]
    if record.color_palette:
        visible_ai_tags.append(f"Colors: {', '.join(record.color_palette)}")
    if record.trend_notes:
        visible_ai_tags.append(f"Trend notes: {', '.join(record.trend_notes)}")
    if visible_ai_tags:
        st.markdown("**AI metadata**")
        for tag in visible_ai_tags:
            st.caption(tag)

    if record.annotation_tags or record.annotation_notes:
        st.markdown("**Designer annotations**")
        if record.annotation_tags:
            st.caption(f"Tags: {', '.join(record.annotation_tags)}")
        if record.annotation_notes:
            st.write(record.annotation_notes)

    st.caption(
        "Classification source: "
        + (record.classification_source or "pending")
        + (f" ({record.model_name})" if record.model_name else "")
    )
    render_annotation_editor(record.id, record.annotation_tags, record.annotation_notes)


def render_home() -> None:
    st.title("Fashion Inspiration Library")
    st.write(
        "Upload field imagery, enrich it with AI-generated fashion metadata, and "
        "search it later through designer-friendly filters."
    )

    with st.form("upload-form", clear_on_submit=True):
        designer = st.text_input("Designer", placeholder="Jane Doe")
        captured_at = st.text_input("Capture date", placeholder="2026-04-01")
        uploaded = st.file_uploader(
            "Upload garment or streetwear inspiration",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
        )
        submit = st.form_submit_button("Upload and classify")

    if submit and not uploaded:
        st.warning("Select an image before submitting.")
    elif submit and uploaded:
        with st.spinner("Saving image and generating metadata..."):
            image_record, result = process_upload(
                file_name=uploaded.name,
                file_bytes=uploaded.getvalue(),
                designer=designer or None,
                captured_at=captured_at or None,
            )
        st.success(f"Stored {image_record.file_name} and generated metadata.")
        st.subheader("Latest Classification")
        st.caption(
            f"Source: {result.source}"
            + (f" | Model: {result.model_name}" if result.model_name else " | Heuristic fallback")
        )
        st.json(result.model_dump())

    filters = render_filters()
    results = search_library(filters)
    st.subheader("Library")
    st.caption(f"{len(results)} result(s)")
    if not results:
        if get_filter_options()["designers"] or get_filter_options()["garment_types"]:
            st.info("No results match the current search and filters.")
        else:
            st.info("No images uploaded yet.")
        return

    columns = st.columns(3)
    for index, record in enumerate(results):
        with columns[index % 3]:
            render_record_card(record)


def main() -> None:
    init_db()
    render_sidebar()
    render_home()


if __name__ == "__main__":
    main()

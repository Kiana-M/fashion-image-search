import streamlit as st

from app.config import DB_PATH, UPLOAD_DIR
from app.db import init_db
from app.services import load_recent_images, process_upload


st.set_page_config(page_title="Fashion Image Search", layout="wide")


def render_sidebar() -> None:
    st.sidebar.title("Fashion Image Search")
    st.sidebar.caption("Local-first inspiration library for design teams.")
    st.sidebar.write(f"Database: `{DB_PATH}`")
    st.sidebar.write(f"Uploads: `{UPLOAD_DIR}`")


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

    recent_images = load_recent_images()
    st.subheader("Recent Uploads")
    if not recent_images:
        st.info("No images uploaded yet.")
        return

    for record in recent_images[:10]:
        left, right = st.columns([1, 2])
        with left:
            st.image(record.file_path, use_container_width=True)
        with right:
            st.markdown(f"**{record.file_name}**")
            if record.designer:
                st.write(f"Designer: {record.designer}")
            if record.captured_at:
                st.write(f"Captured: {record.captured_at}")
            if record.description:
                st.write(record.description)
            summary_parts = [
                record.garment_type,
                record.style,
                record.material,
                ", ".join(record.color_palette) if record.color_palette else None,
            ]
            visible_parts = [part for part in summary_parts if part]
            if visible_parts:
                st.caption(" | ".join(visible_parts))
            st.caption(
                "Classification source: "
                + (record.classification_source or "pending")
                + (f" ({record.model_name})" if record.model_name else "")
            )


def main() -> None:
    init_db()
    render_sidebar()
    render_home()


if __name__ == "__main__":
    main()

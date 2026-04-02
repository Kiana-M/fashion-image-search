from pathlib import Path

import streamlit as st

from app.config import DB_PATH, UPLOAD_DIR
from app.db import init_db
from app.services import build_placeholder_classification


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

    uploaded = st.file_uploader(
        "Upload garment or streetwear inspiration",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
        disabled=True,
        help="Upload will be enabled once the persistence and classification flow is implemented.",
    )

    if uploaded:
        st.info("Upload support is coming in the next implementation step.")

    st.subheader("Next Milestones")
    st.markdown(
        """
        - Enable image upload and local asset persistence
        - Run AI classification and parse structured attributes
        - Add visual library search, filters, and annotations
        - Evaluate model quality on a labeled test set
        """
    )

    placeholder = build_placeholder_classification()
    st.subheader("Expected Classification Shape")
    st.json(placeholder.model_dump())


def main() -> None:
    init_db()
    render_sidebar()
    render_home()


if __name__ == "__main__":
    main()

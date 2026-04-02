# Fashion Image Search

A lightweight Streamlit app for uploading, classifying, organizing, and searching fashion inspiration photos with AI-assisted metadata.

## Project Status

This repository is being built incrementally. The current scaffold includes:

- a Streamlit entrypoint
- SQLite storage setup
- initial app/service module structure
- pytest test layout

## Planned Scope

- image upload and local asset storage
- multimodal AI classification into rich descriptions and structured fashion/context attributes
- dynamic search and filtering
- designer-authored annotations
- evaluation workflow over a labeled image set
- unit, integration, and end-to-end style tests

## Tech Stack

- Python 3.9+
- Streamlit
- SQLite
- OpenAI API
- pytest

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -e .[dev]
```

3. Copy environment variables:

```bash
cp .env.example .env
```

4. Run the app:

```bash
streamlit run app/main.py
```

5. Run tests:

```bash
pytest
```

## Repository Structure

```text
app/       Streamlit app, data access, and service code
eval/      Evaluation scripts and labeled test set
tests/     Unit, integration, and end-to-end style tests
data/      Local runtime storage for uploaded assets
```

## Architecture Notes

- The app will store uploaded images on disk and structured metadata in SQLite.
- AI-generated descriptions and parsed attributes will be stored separately from designer-authored annotations.
- Filters will be generated dynamically from the stored metadata to avoid hardcoded facets.

## Assumptions

- This is a local-first proof of concept optimized for fast setup and demoability.
- SQLite is sufficient for the expected one-day prototype scope.
- Evaluation results and known limitations will be added as implementation progresses.

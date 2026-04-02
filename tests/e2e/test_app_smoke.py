from app.services import build_placeholder_classification


def test_placeholder_classification_has_description() -> None:
    result = build_placeholder_classification()

    assert "not wired up yet" in result.description

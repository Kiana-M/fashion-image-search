from app.models import ClassificationResult


def test_classification_result_defaults() -> None:
    result = ClassificationResult(description="Sample description", attributes={})

    assert result.description == "Sample description"
    assert result.attributes.color_palette == []
    assert result.attributes.trend_notes == []

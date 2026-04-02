from app.parsing import parse_classification_output


def test_parse_classification_output_normalizes_list_fields() -> None:
    raw_output = """
    {
      "description": "A denim jacket with striped trim.",
      "attributes": {
        "garment_type": "jacket",
        "style": "streetwear",
        "material": "denim",
        "color_palette": "blue, white",
        "pattern": "striped",
        "season": "spring",
        "occasion": "casual",
        "consumer_profile": "young urban consumer",
        "trend_notes": "contrast trim, cropped proportion",
        "continent": "Asia",
        "country": "Japan",
        "city": "Tokyo"
      }
    }
    """

    result = parse_classification_output(raw_output, source="openai", model_name="demo-model")

    assert result.description == "A denim jacket with striped trim."
    assert result.attributes.color_palette == ["blue", "white"]
    assert result.attributes.trend_notes == ["contrast trim", "cropped proportion"]
    assert result.attributes.city == "Tokyo"
    assert result.source == "openai"

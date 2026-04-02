from app.models import ClassificationResult, GarmentAttributes


def build_placeholder_classification() -> ClassificationResult:
    return ClassificationResult(
        description=(
            "Classification is not wired up yet. Uploaded images will be analyzed "
            "with a multimodal model in the next implementation step."
        ),
        attributes=GarmentAttributes(),
    )

# Evaluation Dataset

Store the labeled evaluation set here as JSONL.

Each row should include:

```json
{
  "image_path": "eval/dataset/images/look-001.jpg",
  "description": "Short manual description of the image",
  "garment_type": "jacket",
  "style": "streetwear",
  "material": "denim",
  "color_palette": ["blue", "white"],
  "pattern": "striped",
  "season": "spring",
  "occasion": "casual",
  "consumer_profile": "young urban consumer",
  "trend_notes": ["contrast trim", "cropped proportion"],
  "continent": "asia",
  "country": "japan",
  "city": "tokyo",
  "notes": "Optional evaluator notes"
}
```

Recommended workflow:

1. Add 50-100 images under `eval/dataset/images/`.
2. Label the expected attributes manually in `starter_labels.jsonl` or a new JSONL file.
3. Run `python3 -m eval.evaluate --dataset <your-jsonl>`.
4. Review the generated report in `eval/results/`.

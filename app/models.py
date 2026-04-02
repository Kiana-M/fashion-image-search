from typing import List, Optional

from pydantic import BaseModel, Field


class GarmentAttributes(BaseModel):
    garment_type: Optional[str] = None
    style: Optional[str] = None
    material: Optional[str] = None
    color_palette: List[str] = Field(default_factory=list)
    pattern: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    consumer_profile: Optional[str] = None
    trend_notes: List[str] = Field(default_factory=list)
    continent: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None


class ClassificationResult(BaseModel):
    description: str
    attributes: GarmentAttributes
    raw_response: str = ""
    source: str = "unknown"
    model_name: Optional[str] = None


class Annotation(BaseModel):
    tags: List[str] = Field(default_factory=list)
    notes: str = ""


class ImageRecord(BaseModel):
    id: int
    file_name: str
    file_path: str
    designer: Optional[str] = None
    captured_at: Optional[str] = None
    created_at: str
    description: Optional[str] = None
    garment_type: Optional[str] = None
    style: Optional[str] = None
    material: Optional[str] = None
    color_palette: List[str] = Field(default_factory=list)
    pattern: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    consumer_profile: Optional[str] = None
    trend_notes: List[str] = Field(default_factory=list)
    continent: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    classification_source: Optional[str] = None
    model_name: Optional[str] = None

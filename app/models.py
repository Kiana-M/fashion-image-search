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


class Annotation(BaseModel):
    tags: List[str] = Field(default_factory=list)
    notes: str = ""

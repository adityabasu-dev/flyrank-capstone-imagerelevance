from pydantic import BaseModel, Field
from typing import List, Optional

class ImageMetadata(BaseModel):
    subject: str = Field(description="Primary subject, e.g., 'red fox'")
    category: str = Field(description="High-level category, e.g., 'animal', 'vehicle', 'landscape'")
    attributes: List[str] = Field(description="Visual descriptors, e.g., ['orange fur', 'forest', 'daylight']")
    caption: str = Field(description="A clear, detailed description of what is visible in the image")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")

class BatchIngestResponse(BaseModel):
    message: str
    total_queued: int

class ImageProcessResult(BaseModel):
    id: int
    filename: str
    subject: Optional[str]
    category: Optional[str]
    confidence: float
    flagged: bool
    status: str
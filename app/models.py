from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON
from enum import Enum

class BatchStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ReviewStatus(str, Enum):
    SUGGESTED = "SUGGESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

# --- Database Models ---

class Image(SQLModel, table=True):
    __tablename__ = "images"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    file_path: str
    subject: Optional[str] = Field(default=None, index=True)
    category: Optional[str] = Field(default=None, index=True)
    attributes: List[str] = Field(default=[], sa_column=Column(JSON))
    caption: Optional[str] = None
    confidence: float = Field(default=0.0)
    
    # Store vector embedding as JSON float list (compatible across standard SQL DBs)
    embedding: List[float] = Field(default=[], sa_column=Column(JSON))
    
    flagged: bool = Field(default=False)
    status: BatchStatus = Field(default=BatchStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    category: str = Field(index=True)
    content: str
    embedding: List[float] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AICostLog(SQLModel, table=True):
    __tablename__ = "ai_cost_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    operation: str  # e.g., "VISION_TAGGING", "TEXT_EMBEDDING"
    model_name: str
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ImageMatchReview(SQLModel, table=True):
    __tablename__ = "image_match_reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="posts.id", index=True)
    image_id: int = Field(foreign_key="images.id", index=True)
    similarity_score: float
    status: ReviewStatus = Field(default=ReviewStatus.SUGGESTED)
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
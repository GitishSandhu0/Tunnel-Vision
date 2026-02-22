from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str = Field(..., description="Canonical name of the entity")
    type: str = Field(
        ...,
        description="Entity type: PERSON | ORG | TECH | TOPIC | PLACE | EVENT | PRODUCT",
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Relative importance (frequency-based). Higher = more prominent.",
    )
    mentions: int = Field(
        default=1,
        ge=1,
        description="Raw count of how many times this entity appeared across all texts",
    )


class Category(BaseModel):
    name: str = Field(..., description="Broad interest/knowledge domain name")
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Aggregate weight of all entities belonging to this category",
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Entity names that belong to this category",
    )


class ExtractionResult(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    categories: List[Category] = Field(default_factory=list)
    source_platform: Optional[str] = None
    total_texts_processed: int = 0
    extraction_model: str = "gemini-1.5-flash"

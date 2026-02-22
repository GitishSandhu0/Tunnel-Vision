from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str = Field(..., description="Unique node identifier (name:type or category name)")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Node type: Entity | Category | User")
    weight: float = Field(default=1.0, ge=0.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")
    relationship: str = Field(..., description="Relationship type, e.g. INTERESTED_IN")
    weight: float = Field(default=1.0, ge=0.0)


class GraphData(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    links: List[GraphEdge] = Field(default_factory=list)
    user_id: str


class GraphStats(BaseModel):
    user_id: str
    total_entities: int = 0
    total_categories: int = 0
    total_relationships: int = 0
    top_entities: List[Dict[str, Any]] = Field(default_factory=list)
    top_categories: List[Dict[str, Any]] = Field(default_factory=list)


class Recommendation(BaseModel):
    entity_name: str
    entity_type: str
    reason: str = Field(..., description="Human-readable explanation of why this was recommended")
    distance: int = Field(..., description="Graph distance from user's known interests")
    bridge_entities: List[str] = Field(
        default_factory=list,
        description="Intermediate entities that connect user to this recommendation",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score 0–1 based on path strength",
    )
    category: Optional[str] = None

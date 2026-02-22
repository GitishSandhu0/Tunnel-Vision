from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class WorldEvent(BaseModel):
    name: str = Field(..., description="Article headline / event title")
    url: str = Field(..., description="Source article URL")
    domain: str = Field(..., description="Publisher domain")
    seen_date: str = Field(..., description="ISO-8601 date GDELT indexed the article")


class LearningBridge(BaseModel):
    world_event_name: str = Field(..., description="The global event the user is missing")
    world_event_url: str = Field(..., description="URL of the world event article")
    user_anchor_entity: str = Field(
        default="",
        description="Name of the user's existing interest that connects to this event",
    )
    via_category: str = Field(
        ...,
        description="The knowledge domain that bridges user interest to the world event",
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of the bridge path",
    )
    distance: int = Field(
        default=2,
        description="Graph distance (hops) between user anchor and world event",
    )


class TunnelVisionReport(BaseModel):
    user_id: str
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Tunnel Vision Score 0–100.  Higher means the user is more disconnected "
            "from current global reality."
        ),
    )
    severity: str = Field(
        ...,
        description="Severity label: Aware | Moderate | Narrowing | High | Critical",
    )
    total_world_events: int = Field(
        default=0,
        description="Number of active World Today nodes in the graph",
    )
    connected_count: int = Field(
        default=0,
        description="World events the user is already connected to",
    )
    connected_event_names: List[str] = Field(
        default_factory=list,
        description="Names of world events the user is directly connected to",
    )
    missed_events: List[WorldEvent] = Field(
        default_factory=list,
        description="World events the user has no path to",
    )
    learning_bridges: List[LearningBridge] = Field(
        default_factory=list,
        description="Suggested learning bridges from user interests to missed events",
    )

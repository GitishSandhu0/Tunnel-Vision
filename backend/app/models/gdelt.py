from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GDELTArticle(BaseModel):
    url: str = Field(..., description="Canonical article URL")
    title: str = Field(..., description="Article headline")
    domain: str = Field(..., description="Source domain (e.g. 'bbc.co.uk')")
    seen_date: str = Field(..., description="ISO-8601 date the article was indexed by GDELT")
    language: str = Field(default="English", description="Article language")
    source_country: str = Field(default="", description="Publisher's country code")
    social_image: Optional[str] = Field(default=None, description="Hero image URL if available")


class GDELTNewsResponse(BaseModel):
    entity_name: str = Field(..., description="The entity whose news was fetched")
    articles: List[GDELTArticle] = Field(default_factory=list)
    total: int = Field(default=0, description="Number of articles returned")


class GDELTEnrichResponse(BaseModel):
    enriched_entities: List[str] = Field(
        default_factory=list,
        description="Entity names for which GDELT articles were ingested into Neo4j",
    )
    total_articles_ingested: int = Field(
        default=0,
        description="Total number of GDELTArticle nodes written to Neo4j",
    )

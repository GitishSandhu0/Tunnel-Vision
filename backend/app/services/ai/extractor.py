from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import Settings, get_settings
from app.models.entities import Category, Entity, ExtractionResult

logger = logging.getLogger(__name__)

# Maximum number of text items to send to Gemini in a single API call.
# Keeps prompts well under the 1M-token context window of gemini-1.5-flash.
_BATCH_SIZE = 50

# Prompt template ─ we ask Gemini to return structured JSON so we can parse
# it reliably without an output parser schema dependency.
_SYSTEM_PROMPT = """You are an expert knowledge analyst. Extract structured information from the provided texts.

Return ONLY a valid JSON object with this exact schema:
{
  "entities": [
    {
      "name": "canonical entity name",
      "type": "PERSON|ORG|TECH|TOPIC|PLACE|EVENT|PRODUCT",
      "mentions": <integer count>,
      "weight": <float 0.0-1.0 normalised by frequency>
    }
  ],
  "categories": [
    {
      "name": "broad knowledge domain",
      "weight": <float 0.0-1.0>,
      "entities": ["entity name 1", "entity name 2"]
    }
  ]
}

Rules:
- Normalise entity names (e.g. "US" → "United States", "ML" → "Machine Learning")
- Only include entities that appear AT LEAST twice across the texts OR are clearly significant
- Category names must be broad (e.g. "Technology", "Politics", "Music", "Science", not sub-topics)
- Weight is relative frequency: most-frequent entity gets weight 1.0, others scaled proportionally
- Return at most 30 entities and 10 categories per batch
- Do NOT include any markdown formatting, code fences, or explanations outside the JSON
"""

_USER_PROMPT_TEMPLATE = """Analyse the following {count} text samples from a social media export:

---
{texts}
---

Extract entities and categories following the schema."""


class AIExtractor:
    """
    Extracts named entities and knowledge categories from a corpus of text
    using LangChain + Google Gemini (gemini-1.5-flash).

    The extractor processes texts in batches of {_BATCH_SIZE} items to stay
    within API request limits, then deduplicates and merges results.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._llm = self._build_llm()

    def _build_llm(self):
        """Lazily construct the LangChain ChatGoogleGenerativeAI wrapper."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "langchain-google-genai is required. Add it to requirements.txt."
            ) from exc

        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self._settings.GEMINI_API_KEY,
            temperature=0.1,          # low temp for consistent structured output
            max_output_tokens=4096,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def extract_entities_and_categories(
        self,
        texts: List[str],
        source_platform: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Process `texts` in batches and return a merged :class:`ExtractionResult`.

        Args:
            texts:           Cleaned, PII-scrubbed text strings.
            source_platform: Optional hint (e.g. "twitter") added to the result.

        Returns:
            ExtractionResult with deduplicated, weight-normalised entities and categories.
        """
        if not texts:
            return ExtractionResult(source_platform=source_platform)

        # Split into manageable batches
        batches = [texts[i : i + _BATCH_SIZE] for i in range(0, len(texts), _BATCH_SIZE)]
        logger.info(
            "AIExtractor: processing %d texts across %d batch(es)",
            len(texts),
            len(batches),
        )

        all_entities: Dict[str, Entity] = {}
        all_categories: Dict[str, Category] = {}

        for batch_idx, batch in enumerate(batches):
            logger.debug("Processing batch %d/%d (%d items)", batch_idx + 1, len(batches), len(batch))
            try:
                batch_result = await self._extract_batch(batch)
                self._merge_entities(all_entities, batch_result.get("entities", []))
                self._merge_categories(all_categories, batch_result.get("categories", []))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Batch %d extraction failed, skipping: %s", batch_idx + 1, exc)

            # Small delay between batches so combined with the queue submission
            # delay we stay within Gemini free-tier RPM limits without doubling wait time.
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(0.3)

        # Normalise weights so the top entity has weight 1.0
        entities = self._normalise_entity_weights(list(all_entities.values()))
        categories = list(all_categories.values())

        return ExtractionResult(
            entities=entities,
            categories=categories,
            source_platform=source_platform,
            total_texts_processed=len(texts),
            extraction_model="gemini-1.5-flash",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _extract_batch(self, batch: List[str]) -> Dict[str, Any]:
        """Send a single batch to Gemini and return parsed JSON."""
        from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore[import-untyped]

        text_block = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(batch))
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(
                content=_USER_PROMPT_TEMPLATE.format(count=len(batch), texts=text_block)
            ),
        ]

        response = await self._llm.ainvoke(messages)
        raw_content: str = response.content if hasattr(response, "content") else str(response)

        return self._parse_llm_response(raw_content)

    @staticmethod
    def _parse_llm_response(raw: str) -> Dict[str, Any]:
        """
        Extract JSON from the LLM response, tolerating markdown code fences
        that the model occasionally adds despite instructions.
        """
        # Strip markdown fences if present
        raw = raw.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if fence_match:
            raw = fence_match.group(1).strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract just the JSON object
            obj_match = re.search(r"\{[\s\S]*\}", raw)
            if obj_match:
                try:
                    return json.loads(obj_match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("Could not parse LLM JSON response: %s…", raw[:200])
            return {"entities": [], "categories": []}

    @staticmethod
    def _merge_entities(
        existing: Dict[str, Entity],
        new_entities: List[Dict[str, Any]],
    ) -> None:
        """
        Merge a batch's entity list into the running aggregate.
        Uses (name.lower, type) as the dedup key; accumulates mention counts.
        """
        for raw in new_entities:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name", "")).strip()
            entity_type = str(raw.get("type", "TOPIC")).strip().upper()
            if not name:
                continue
            key = f"{name.lower()}::{entity_type}"
            mentions = int(raw.get("mentions", 1))
            weight = float(raw.get("weight", 0.1))

            if key in existing:
                existing[key].mentions += mentions
                existing[key].weight = max(existing[key].weight, weight)
            else:
                existing[key] = Entity(
                    name=name,
                    type=entity_type,
                    mentions=mentions,
                    weight=weight,
                )

    @staticmethod
    def _merge_categories(
        existing: Dict[str, Category],
        new_categories: List[Dict[str, Any]],
    ) -> None:
        for raw in new_categories:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name", "")).strip()
            if not name:
                continue
            key = name.lower()
            weight = float(raw.get("weight", 0.1))
            entity_names: List[str] = [str(e) for e in raw.get("entities", [])]

            if key in existing:
                existing[key].weight = max(existing[key].weight, weight)
                # Union of entity lists
                merged = list(set(existing[key].entities) | set(entity_names))
                existing[key].entities = merged
            else:
                existing[key] = Category(name=name, weight=weight, entities=entity_names)

    @staticmethod
    def _normalise_entity_weights(entities: List[Entity]) -> List[Entity]:
        """Scale weights so the highest-weight entity has weight 1.0."""
        if not entities:
            return entities
        max_weight = max(e.weight for e in entities)
        if max_weight <= 0:
            return entities
        for entity in entities:
            entity.weight = round(entity.weight / max_weight, 4)
        return sorted(entities, key=lambda e: e.weight, reverse=True)

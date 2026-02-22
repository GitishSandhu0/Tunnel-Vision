from __future__ import annotations

import json
import logging
import os
import zipfile
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_upload(file_path: str, file_extension: str) -> Dict[str, Any]:
    """
    Parse an uploaded file and return a normalised dict with text items.

    Args:
        file_path:      Absolute path to the temp file on disk.
        file_extension: Lower-cased extension including dot, e.g. '.zip' or '.json'.

    Returns:
        {
            "source_platform": str | None,   # detected platform or None
            "items":           list[str],     # cleaned text strings
            "metadata":        dict,          # file-level stats
        }
    """
    if file_extension == ".zip":
        return _parse_zip(file_path)
    elif file_extension == ".json":
        return _parse_json_file(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")


# ---------------------------------------------------------------------------
# ZIP handling
# ---------------------------------------------------------------------------


def _parse_zip(file_path: str) -> Dict[str, Any]:
    """
    Extract all JSON files from a ZIP archive, detect the platform from
    known file names, and aggregate text items.
    """
    items: List[str] = []
    platform: str | None = None
    metadata: Dict[str, Any] = {"files_parsed": [], "total_files": 0}

    with zipfile.ZipFile(file_path, "r") as zf:
        json_members = [m for m in zf.namelist() if m.lower().endswith(".json")]
        metadata["total_files"] = len(json_members)

        for member in json_members:
            basename = os.path.basename(member).lower()
            try:
                with zf.open(member) as f:
                    raw = f.read().decode("utf-8", errors="replace")
                    data = _safe_json_loads(raw, member)
                    if data is None:
                        continue

                    detected_platform, extracted = _dispatch_json(basename, data)
                    if detected_platform and platform is None:
                        platform = detected_platform

                    items.extend(extracted)
                    metadata["files_parsed"].append(basename)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not parse %s inside ZIP, skipping: %s", member, exc)

    return {"source_platform": platform, "items": items, "metadata": metadata}


# ---------------------------------------------------------------------------
# Direct JSON handling
# ---------------------------------------------------------------------------


def _parse_json_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, encoding="utf-8", errors="replace") as f:
        raw = f.read()

    data = _safe_json_loads(raw, file_path)
    if data is None:
        return {"source_platform": None, "items": [], "metadata": {}}

    basename = os.path.basename(file_path).lower()
    platform, items = _dispatch_json(basename, data)
    return {
        "source_platform": platform,
        "items": items,
        "metadata": {"total_items": len(items)},
    }


# ---------------------------------------------------------------------------
# Platform dispatch
# ---------------------------------------------------------------------------


def _dispatch_json(basename: str, data: Any) -> tuple[str | None, List[str]]:
    """
    Route parsed JSON data to the appropriate platform extractor based on
    the originating filename. Falls back to a generic extractor.
    """
    # Twitter / X  ─ tweets.js, like.js
    if "tweet" in basename:
        return "twitter", _extract_twitter_tweets(data)
    if basename in {"like.js", "likes.json", "liked_tweets.json"}:
        return "twitter", _extract_twitter_likes(data)

    # Reddit
    if "comment" in basename and "reddit" not in basename:
        # Could be reddit comments.json
        pass
    if basename in {"comments.json", "posts.json"} or "reddit" in basename:
        return "reddit", _extract_reddit_content(data)

    # Instagram
    if basename in {
        "liked_posts.json",
        "post_comments.json",
        "direct_messages.json",
        "saved.json",
    }:
        return "instagram", _extract_instagram(data)

    # YouTube – watch history, search history
    if "watch-history" in basename or "search-history" in basename:
        return "youtube", _extract_youtube_history(data)

    # Google Takeout – generic search / activity
    if "myactivity" in basename or "activity" in basename:
        return "google", _extract_google_activity(data)

    # Fallback: walk the JSON tree and collect strings
    return None, _extract_generic_strings(data)


# ---------------------------------------------------------------------------
# Platform-specific extractors
# ---------------------------------------------------------------------------


def _extract_twitter_tweets(data: Any) -> List[str]:
    texts: List[str] = []
    # Twitter export wraps each file as:  [{"tweet": {"full_text": "..."}}]
    records = data if isinstance(data, list) else []
    for record in records:
        tweet = record.get("tweet", record) if isinstance(record, dict) else {}
        text = tweet.get("full_text") or tweet.get("text", "")
        if text:
            texts.append(str(text))
    return texts


def _extract_twitter_likes(data: Any) -> List[str]:
    texts: List[str] = []
    records = data if isinstance(data, list) else []
    for record in records:
        like = record.get("like", record) if isinstance(record, dict) else {}
        text = like.get("fullText") or like.get("full_text", "")
        if text:
            texts.append(str(text))
    return texts


def _extract_reddit_content(data: Any) -> List[str]:
    texts: List[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key in ("body", "selftext", "title", "text"):
                    val = item.get(key, "")
                    if val and val not in ("[deleted]", "[removed]", ""):
                        texts.append(str(val))
    elif isinstance(data, dict):
        # Some exports are {"data": [...]}
        inner = data.get("data", [])
        texts.extend(_extract_reddit_content(inner))
    return texts


def _extract_instagram(data: Any) -> List[str]:
    texts: List[str] = []

    def _walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key in ("value", "text", "title", "caption"):
                val = obj.get(key)
                if isinstance(val, str) and val.strip():
                    texts.append(val.strip())
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(data)
    return texts


def _extract_youtube_history(data: Any) -> List[str]:
    texts: List[str] = []
    records = data if isinstance(data, list) else []
    for record in records:
        if isinstance(record, dict):
            title = record.get("title", "")
            # Strip "Watched " / "Searched for " prefixes added by Google Takeout
            for prefix in ("Watched ", "Searched for ", "Visited "):
                if title.startswith(prefix):
                    title = title[len(prefix):]
                    break
            if title.strip():
                texts.append(title.strip())
    return texts


def _extract_google_activity(data: Any) -> List[str]:
    texts: List[str] = []
    records = data if isinstance(data, list) else []
    for record in records:
        if isinstance(record, dict):
            title = record.get("title", "")
            for prefix in ("Visited ", "Watched ", "Searched for ", "Used "):
                if title.startswith(prefix):
                    title = title[len(prefix):]
                    break
            if title.strip():
                texts.append(title.strip())
            # Also pick up subtitles
            for subtitle_block in record.get("subtitles", []):
                name = subtitle_block.get("name", "")
                if name.strip():
                    texts.append(name.strip())
    return texts


# ---------------------------------------------------------------------------
# Generic / fallback extractor
# ---------------------------------------------------------------------------


def _extract_generic_strings(data: Any, max_depth: int = 8) -> List[str]:
    """
    Recursively walk any JSON structure and collect non-trivial string values.
    Ignores URLs, timestamps, and very short strings.
    """
    texts: List[str] = []
    _walk_generic(data, texts, depth=0, max_depth=max_depth)
    return texts


def _walk_generic(obj: Any, texts: List[str], depth: int, max_depth: int) -> None:
    if depth > max_depth:
        return
    if isinstance(obj, str):
        stripped = obj.strip()
        # Skip URLs, single words under 4 chars, and obvious timestamps
        if (
            len(stripped) >= 10
            and not stripped.startswith(("http://", "https://", "www."))
            and not _looks_like_timestamp(stripped)
        ):
            texts.append(stripped)
    elif isinstance(obj, dict):
        for v in obj.values():
            _walk_generic(v, texts, depth + 1, max_depth)
    elif isinstance(obj, list):
        for item in obj:
            _walk_generic(item, texts, depth + 1, max_depth)


def _looks_like_timestamp(s: str) -> bool:
    """Heuristic: strings that look like ISO dates or Unix timestamps."""
    import re

    return bool(re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", s)) or s.isdigit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_json_loads(raw: str, source: str) -> Any:
    """
    Try to parse JSON, stripping a leading JS variable assignment if present
    (Twitter exports use `window.YTD.tweets.part0 = [...]` style).
    """
    raw = raw.strip()
    # Handle Twitter-style: `window.YTD.*.part0 = <json>`
    if raw.startswith("window.") and "=" in raw:
        _, _, rest = raw.partition("=")
        raw = rest.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("JSON decode error in %s: %s", source, exc)
        return None

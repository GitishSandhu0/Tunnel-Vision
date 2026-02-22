from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Dict

logger = logging.getLogger(__name__)

# Maximum concurrent Gemini API calls allowed at any one time.
# Gemini free tier allows 15 RPM; we leave headroom for retries.
_MAX_CONCURRENT = 3

# Minimum gap in seconds between successive job submissions to the semaphore.
# Spreads requests over time even when the semaphore slot is immediately free.
_SUBMISSION_DELAY_SECONDS = 1.0


class ProcessingQueue:
    """
    Lightweight async rate-limiter for Gemini API calls.

    Uses an :class:`asyncio.Semaphore` to cap the number of concurrent
    in-flight API requests.  A configurable inter-submission delay prevents
    burst spikes that would trip the RPM quota even within the concurrency cap.

    Design notes
    ────────────
    - No external broker required (avoids Redis/Celery on the free tier).
    - The semaphore is created lazily so the class can be instantiated at
      module level before the event loop exists.
    - Thread-safety is not a concern because FastAPI runs in a single-threaded
      async event loop.
    """

    def __init__(
        self,
        max_concurrent: int = _MAX_CONCURRENT,
        submission_delay: float = _SUBMISSION_DELAY_SECONDS,
    ) -> None:
        self._max_concurrent = max_concurrent
        self._submission_delay = submission_delay
        self._semaphore: asyncio.Semaphore | None = None
        self._active_jobs: Dict[str, bool] = {}
        self._submission_lock: asyncio.Lock | None = None
        # Track in-flight count independently to avoid relying on semaphore internals
        self._in_flight: int = 0

    # ------------------------------------------------------------------
    # Lazy initialisation (event loop must exist when first used)
    # ------------------------------------------------------------------

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    def _get_submission_lock(self) -> asyncio.Lock:
        if self._submission_lock is None:
            self._submission_lock = asyncio.Lock()
        return self._submission_lock

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enqueue(self, job_id: str, coro: Awaitable[Any]) -> Any:
        """
        Acquire a semaphore slot, optionally wait for the inter-submission
        delay, then run *coro* and return its result.

        Args:
            job_id: Opaque identifier used for tracking and logging.
            coro:   The coroutine to execute (e.g. AIExtractor.extract_…).

        Returns:
            Whatever *coro* returns.

        Raises:
            Any exception raised by *coro* propagates to the caller.
        """
        semaphore = self._get_semaphore()
        submission_lock = self._get_submission_lock()

        # Serialise submissions so they're at least _submission_delay apart
        async with submission_lock:
            await asyncio.sleep(self._submission_delay)

        async with semaphore:
            self._active_jobs[job_id] = True
            self._in_flight += 1
            logger.debug(
                "ProcessingQueue: starting job %s (%d/%d slots used)",
                job_id,
                self._in_flight,
                self._max_concurrent,
            )
            try:
                result = await coro
                return result
            except Exception as exc:
                logger.error("ProcessingQueue: job %s raised %s", job_id, exc)
                raise
            finally:
                self._in_flight -= 1
                self._active_jobs.pop(job_id, None)

    @property
    def active_job_count(self) -> int:
        """Number of jobs currently being executed."""
        return len(self._active_jobs)

    @property
    def active_job_ids(self) -> list[str]:
        return list(self._active_jobs.keys())


# Module-level singleton – shared across the entire FastAPI process.
processing_queue = ProcessingQueue()

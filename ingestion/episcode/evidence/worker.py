"""Sequential background delivery loop for accepted Evidence Episodes."""

from __future__ import annotations

import asyncio

from ingestion.episcode.evidence.module import EvidenceEpisodeModule


async def run_worker(
    module: EvidenceEpisodeModule,
    *,
    stop_event: asyncio.Event,
    poll_interval_seconds: float = 1.0,
    batch_size: int = 5,
) -> None:
    if poll_interval_seconds <= 0:
        raise ValueError("poll interval must be positive")
    if batch_size <= 0:
        raise ValueError("batch size must be positive")

    while not stop_event.is_set():
        result = await module.process_pending(limit=batch_size)
        if result.succeeded_ids or result.retry_ids or result.failed_ids:
            continue
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_seconds)
        except TimeoutError:
            continue

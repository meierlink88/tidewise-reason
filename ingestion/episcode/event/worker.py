"""Single active Event resolver loop."""

from __future__ import annotations

import asyncio

from ingestion.episcode.event.module import EventCandidateModule


async def run_worker(module: EventCandidateModule, *, stop_event: asyncio.Event, poll_interval_seconds: float = 1.0, batch_size: int = 5) -> None:
    while not stop_event.is_set():
        if await module.process_pending(limit=batch_size):
            continue
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_seconds)
        except TimeoutError:
            pass

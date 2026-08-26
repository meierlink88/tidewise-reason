from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from analysis.event.trigger import AnalysisSchedulingEventProjector
from ingestion.episcode.event.resolver import AnalysisSchedulingUnavailable
from tests.test_event_graphiti_projector import event


class EventAnalysisTriggerTest(unittest.IsolatedAsyncioTestCase):
    async def test_successful_native_projection_enqueues_analysis_once(self) -> None:
        native = SimpleNamespace(project=AsyncMock(return_value="episode-1"))
        module = SimpleNamespace(enqueue=Mock())
        projector = AnalysisSchedulingEventProjector(native, module)

        await projector.project(event())

        native.project.assert_awaited_once_with(event())
        module.enqueue.assert_called_once()
        input_ = module.enqueue.call_args.args[0]
        self.assertEqual(input_.event, event())
        self.assertEqual(input_.episode_uuid, "episode-1")

    async def test_native_projection_failure_does_not_enqueue_analysis(self) -> None:
        native = SimpleNamespace(project=AsyncMock(side_effect=RuntimeError("failed")))
        module = SimpleNamespace(enqueue=Mock())

        with self.assertRaises(RuntimeError):
            await AnalysisSchedulingEventProjector(native, module).project(event())

        module.enqueue.assert_not_called()

    async def test_analysis_enqueue_failure_is_distinct_from_projection_failure(self) -> None:
        native = SimpleNamespace(project=AsyncMock(return_value="episode-1"))
        module = SimpleNamespace(enqueue=Mock(side_effect=OSError("disk unavailable")))

        with self.assertRaises(AnalysisSchedulingUnavailable):
            await AnalysisSchedulingEventProjector(native, module).project(event())

        native.project.assert_awaited_once()
        module.enqueue.assert_called_once()


if __name__ == "__main__":
    unittest.main()

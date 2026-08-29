from __future__ import annotations

import unittest
from datetime import UTC, datetime

from analysis.event.contracts import EventClass
from analysis.event.review import ControlledSignalReviewer
from tests.test_event_analysis_pipeline import (
    candidates,
    classification,
    event_input,
    proposal,
)


class ControlledSignalReviewerTest(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_whitelisted_direct_signal_with_bounded_window(self) -> None:
        variable, anchor = candidates().variables[0], candidates().anchors[0]
        reviewed = proposal().model_copy(
            update={
                "valid_at": datetime(2026, 8, 25, tzinfo=UTC),
                "assertion_modality": "ACTUAL",
            }
        )

        self.assertTrue(
            await ControlledSignalReviewer().review(
                event_input(), classification(), reviewed, variable, anchor
            )
        )

    async def test_company_class_is_never_accepted_in_current_scope(self) -> None:
        variable, anchor = candidates().variables[0], candidates().anchors[0]

        self.assertFalse(
            await ControlledSignalReviewer().review(
                event_input(),
                classification(EventClass.COMPANY),
                proposal(),
                variable,
                anchor,
            )
        )


if __name__ == "__main__":
    unittest.main()

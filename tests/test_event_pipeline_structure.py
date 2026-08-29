from __future__ import annotations

import unittest
from pathlib import Path

import ingestion.episcode.event as event_package


class EventPipelineStructureTest(unittest.TestCase):
    def test_capability_exports_only_the_pipeline_business_interface(self) -> None:
        self.assertEqual(event_package.__all__, ["EventCandidatePipeline"])
        self.assertFalse(hasattr(event_package, "GraphitiEventProjector"))

    def test_non_test_callers_do_not_import_the_internal_episode_stage(self) -> None:
        root = Path(__file__).resolve().parents[1]
        offenders = []
        for area in ("evaluation", "scripts"):
            for path in (root / area).rglob("*"):
                if path.suffix not in {".py", ".sh"}:
                    continue
                content = path.read_text(encoding="utf-8")
                if "ingestion.episcode.event.stages" in content:
                    offenders.append(str(path.relative_to(root)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()

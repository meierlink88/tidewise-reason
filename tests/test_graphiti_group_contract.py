from __future__ import annotations

import unittest

from ingestion.episcode.evidence.graphiti_writer import GRAPHITI_GROUP_ID
from projection.authoritative_writer import GROUP_ID


class GraphitiGroupContractTest(unittest.TestCase):
    def test_projection_and_episode_ingestion_share_the_community_database_group(self) -> None:
        self.assertEqual(GROUP_ID, "neo4j")
        self.assertEqual(GRAPHITI_GROUP_ID, GROUP_ID)


if __name__ == "__main__":
    unittest.main()

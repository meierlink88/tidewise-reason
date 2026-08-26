from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

import httpx

from ingestion.episcode.event.adapters import CompositeEventHistory, DataEventClient
from ingestion.episcode.event.contracts import EventCandidateRequest
from ingestion.episcode.event.resolver import (
    EventHistoryUnavailable,
    PublicationRejected,
)
from tests.test_event_candidate_api import EVENT_ID, candidate_payload


class EventDataClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_publication_uses_submission_id_and_parses_the_formal_data_event(self) -> None:
        observed = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            observed["authorization"] = request.headers.get("authorization")
            observed["payload"] = json.loads(request.content)
            event = {"id": EVENT_ID, **observed["payload"]["event"], "status": "ACTIVE"}
            return httpx.Response(201, json={
                "request_id": "request-1",
                "result": {
                    "event": event,
                    "evidence_link_ids": ["EEL44444444-4444-4444-8444-444444444444"],
                    "receipt_id": "EPR55555555-5555-4555-8555-555555555555",
                    "payload_hash": "a" * 64,
                    "replayed": False,
                },
            })

        request = EventCandidateRequest.model_validate(candidate_payload())
        submission = SimpleNamespace(submission_id="evt-submission-1", event=request.event,
                                     evidence_ids=request.evidence_ids)
        client = DataEventClient("http://data.example", "data-token",
                                 transport=httpx.MockTransport(handler))
        published = await client.publish(submission)

        self.assertEqual(published.id, EVENT_ID)
        self.assertEqual(observed["authorization"], "Bearer data-token")
        self.assertEqual(observed["payload"]["publication_key"], "evt-submission-1:create")
        self.assertNotIn("status", observed["payload"]["event"])

    async def test_list_candidates_reads_all_pages_in_the_time_window(self) -> None:
        pages = []

        async def handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params["page"])
            pages.append(page)
            event = {
                "id": EVENT_ID,
                **candidate_payload()["event"],
                "status": "ACTIVE",
            }
            return httpx.Response(
                200,
                json={
                    "request_id": f"request-{page}",
                    "result": {
                        "items": [event] if page == 1 else [],
                        "total": 101,
                        "page": page,
                        "page_size": 100,
                    },
                },
            )

        request = EventCandidateRequest.model_validate(candidate_payload())
        client = DataEventClient(
            "http://data.example", "data-token", transport=httpx.MockTransport(handler)
        )
        await client.list_candidates(request.event)

        self.assertEqual(pages, [1, 2])

    async def test_publication_4xx_is_classified_as_permanent_rejection(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json={"error": {"code": "INVALID_REQUEST"}})

        request = EventCandidateRequest.model_validate(candidate_payload())
        submission = SimpleNamespace(
            submission_id="evt-submission-rejected",
            event=request.event,
            evidence_ids=request.evidence_ids,
        )
        client = DataEventClient(
            "http://data.example", "data-token", transport=httpx.MockTransport(handler)
        )

        with self.assertRaises(PublicationRejected):
            await client.publish(submission)

    async def test_graphiti_failure_degrades_to_data_history(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class Search:
            async def episode_fulltext_search(self, *args, **kwargs):
                raise RuntimeError("graph unavailable")

        class Driver:
            search_interface = Search()

            async def execute_query(self, *args, **kwargs):
                raise RuntimeError("graph unavailable")

        class Data:
            async def list_candidates(self, candidate):
                from ingestion.episcode.event.contracts import HistoricalEvent

                return [HistoricalEvent(id=EVENT_ID, event=request.event)]

        graphiti = SimpleNamespace(driver=Driver())
        result = await CompositeEventHistory(graphiti, Data()).retrieve(request.event)

        self.assertEqual([item.id for item in result], [EVENT_ID])

    async def test_titled_graphiti_episode_remains_available_to_fulltext_history(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        content = json.dumps(
            {"id": EVENT_ID, **request.event.model_dump(mode="json"), "status": "ACTIVE"}
        )

        class Search:
            async def episode_fulltext_search(self, *args, **kwargs):
                return [SimpleNamespace(name=request.event.title, content=content)]

        class Driver:
            search_interface = Search()

            async def execute_query(self, *args, **kwargs):
                return [], None, None

        class Data:
            async def list_candidates(self, candidate):
                return []

        graphiti = SimpleNamespace(driver=Driver())
        result = await CompositeEventHistory(graphiti, Data()).retrieve(request.event)

        self.assertEqual([item.id for item in result], [EVENT_ID])

    async def test_titled_graphiti_episode_uses_durable_native_source_in_anchor_history(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        content = json.dumps(
            {"id": EVENT_ID, **request.event.model_dump(mode="json"), "status": "ACTIVE"}
        )

        class Search:
            async def episode_fulltext_search(self, *args, **kwargs):
                return []

        class Driver:
            search_interface = Search()

            async def execute_query(self, query, **kwargs):
                self.query = query
                return [{"content": content}], None, None

        class Data:
            async def list_candidates(self, candidate):
                return []

        driver = Driver()
        graphiti = SimpleNamespace(driver=driver)
        result = await CompositeEventHistory(graphiti, Data()).retrieve(request.event)

        self.assertEqual([item.id for item in result], [EVENT_ID])
        self.assertIn("episode.source_description = $source_description", driver.query)

    async def test_graphiti_history_rejects_non_formal_event_identity(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        content = json.dumps(
            {
                "id": "not-an-event-id",
                **request.event.model_dump(mode="json"),
                "status": "ACTIVE",
            }
        )

        class Search:
            async def episode_fulltext_search(self, *args, **kwargs):
                return [SimpleNamespace(name=request.event.title, content=content)]

        class Driver:
            search_interface = Search()

            async def execute_query(self, *args, **kwargs):
                return [], None, None

        class Data:
            async def list_candidates(self, candidate):
                return []

        graphiti = SimpleNamespace(driver=Driver())
        result = await CompositeEventHistory(graphiti, Data()).retrieve(request.event)

        self.assertEqual(result, [])

    async def test_data_failure_never_degrades_to_stale_graphiti_history(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class Search:
            async def episode_fulltext_search(self, *args, **kwargs):
                return []

        class Driver:
            search_interface = Search()

            async def execute_query(self, *args, **kwargs):
                return [], None, None

        class Data:
            async def list_candidates(self, candidate):
                raise RuntimeError("Data unavailable")

        graphiti = SimpleNamespace(driver=Driver())
        with self.assertRaises(EventHistoryUnavailable):
            await CompositeEventHistory(graphiti, Data()).retrieve(request.event)

    async def test_readiness_checks_the_authoritative_event_contract(self) -> None:
        observed = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            observed["authorization"] = request.headers.get("authorization")
            observed["params"] = dict(request.url.params)
            return httpx.Response(
                200,
                json={
                    "request_id": "request-ready",
                    "result": {
                        "items": [],
                        "total": 0,
                        "page": 1,
                        "page_size": 1,
                    },
                },
            )

        client = DataEventClient(
            "http://data.example",
            "data-token",
            transport=httpx.MockTransport(handler),
        )

        self.assertTrue(await client.ready())
        self.assertEqual(observed["authorization"], "Bearer data-token")
        self.assertEqual(
            observed["params"],
            {"page": "1", "page_size": "1", "status": "ACTIVE"},
        )


if __name__ == "__main__":
    unittest.main()

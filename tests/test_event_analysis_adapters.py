from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from graphiti_core.prompts.models import Message
from pydantic import ValidationError

from analysis.event.adapters import GraphitiEventAnalysisLLM
from analysis.event.contracts import AnchorSignalSelection


class GraphitiEventAnalysisLLMTest(unittest.IsolatedAsyncioTestCase):
    async def test_structured_response_uses_schema_and_retries_malformed_output(self) -> None:
        client = SimpleNamespace(
            generate_response=AsyncMock(
                side_effect=[
                    {},
                    {
                        "has_signal": True,
                        "variable_key": "V1",
                        "rationale": "事件直接支持该变量。",
                    },
                ]
            )
        )
        adapter = GraphitiEventAnalysisLLM(
            SimpleNamespace(clients=SimpleNamespace(llm_client=client))
        )

        result = await adapter._structured(
            [Message(role="user", content="test")],
            AnchorSignalSelection,
            max_tokens=300,
            prompt_name="test_structured_retry",
        )

        self.assertTrue(result.has_signal)
        self.assertEqual(client.generate_response.await_count, 2)
        for call in client.generate_response.await_args_list:
            self.assertIs(call.kwargs["response_model"], AnchorSignalSelection)

    async def test_structured_response_stops_after_bounded_attempts(self) -> None:
        client = SimpleNamespace(generate_response=AsyncMock(return_value={}))
        adapter = GraphitiEventAnalysisLLM(
            SimpleNamespace(clients=SimpleNamespace(llm_client=client))
        )

        with self.assertRaises(ValidationError):
            await adapter._structured(
                [Message(role="user", content="test")],
                AnchorSignalSelection,
                max_tokens=300,
                prompt_name="test_structured_failure",
            )

        self.assertEqual(client.generate_response.await_count, 3)


if __name__ == "__main__":
    unittest.main()

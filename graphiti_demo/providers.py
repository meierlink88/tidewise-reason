import json

from graphiti_core import Graphiti
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from openai import AsyncOpenAI
from pydantic import ValidationError

from runtime import RuntimeConfig


def unwrap_schema_properties(result: dict, response_model) -> dict:
    if response_model is None:
        return result
    required = set(response_model.model_fields)
    wrapped = result.get("properties")
    if not required.issubset(result) and isinstance(wrapped, dict) and required.issubset(wrapped):
        return wrapped
    return result


def validate_structured_response(result: dict, response_model) -> dict:
    normalized = unwrap_schema_properties(result, response_model)
    if response_model is None:
        return normalized
    try:
        response_model.model_validate(normalized)
    except ValidationError:
        # Graphiti retries JSON decoding failures. Reclassifying a provider's JSON-Schema echo as
        # a decoding failure keeps retry ownership in Graphiti's existing client boundary.
        raise json.JSONDecodeError("structured response contract mismatch", "", 0) from None
    return normalized


class DeepSeekCompatibleClient(OpenAIGenericClient):
    """Normalize DeepSeek's occasional top-level JSON-Schema `properties` wrapper."""

    async def _generate_response(self, messages, response_model=None, max_tokens=16384, model_size=None):
        instance_instruction = (
            "\n\nReturn one data instance that satisfies the schema. Do not return or describe "
            "the schema itself, its properties, descriptions, or JSON types."
        )
        if response_model is not None and instance_instruction not in messages[-1].content:
            messages[-1].content += instance_instruction
        kwargs = {"max_tokens": max_tokens}
        if model_size is not None:
            kwargs["model_size"] = model_size
        result = await super()._generate_response(messages, response_model, **kwargs)
        return validate_structured_response(result, response_model)


def create_graphiti(config: RuntimeConfig) -> Graphiti:
    llm_config = LLMConfig(
        api_key=config.graphiti_llm_api_key.get_secret_value(),
        base_url=str(config.graphiti_llm_base_url).rstrip("/"),
        model=config.graphiti_llm_model,
        small_model=config.graphiti_llm_model,
        temperature=0,
        max_tokens=8192,
    )
    return Graphiti(
        uri=config.neo4j_uri,
        user=config.neo4j_user,
        password=config.neo4j_password.get_secret_value(),
        llm_client=DeepSeekCompatibleClient(
            config=llm_config,
            max_tokens=8192,
            structured_output_mode="json_object",
        ),
        embedder=OpenAIEmbedder(
            OpenAIEmbedderConfig(
                api_key=config.graphiti_embedding_api_key.get_secret_value(),
                base_url=str(config.graphiti_embedding_base_url).rstrip("/"),
                embedding_model=config.graphiti_embedding_model,
                embedding_dim=config.graphiti_embedding_dim,
            )
        ),
        max_coroutines=2,
    )


class AnalysisLLMAdapter:
    def __init__(self, config: RuntimeConfig) -> None:
        self._model = config.graphiti_llm_model
        self._client = AsyncOpenAI(
            api_key=config.graphiti_llm_api_key.get_secret_value(),
            base_url=str(config.graphiti_llm_base_url).rstrip("/"),
        )

    async def generate_json(self, *, system: str, context: dict) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(context, ensure_ascii=False, default=str)},
                ],
            )
            return response.choices[0].message.content or "{}"
        finally:
            await self._client.close()

from datetime import UTC, datetime
from uuid import UUID, uuid5


QUESTION = "推理未来12个月AI数据中心液冷服务器产业链各节点的变化趋势"
AS_OF = datetime(2026, 8, 21, tzinfo=UTC)
EVIDENCE_PUBLISHED_FROM = datetime(2026, 8, 16, tzinfo=UTC)
# Graphiti 0.29 maps an explicit group ID to a Neo4j database. Community Edition exposes only
# the default `neo4j` database, which is dedicated to this local evaluation.
DEMO_GROUP_ID = "neo4j"
DEMO_NAMESPACE = UUID("b798e748-7d61-4f89-9ee3-a82620317acd")

CHAIN = {
    "name": "AI数据中心液冷服务器产业链",
    "description": "AI数据中心从算力芯片、服务器散热部件、液冷服务器与液冷系统到数据中心部署的示例产业链。",
    "nodes": [
        {"name": "AI芯片", "role": "算力与热源核心"},
        {"name": "服务器冷板", "role": "贴近芯片的液冷换热部件"},
        {"name": "液冷服务器", "role": "采用液冷散热的服务器整机"},
        {"name": "液冷系统", "role": "冷却液循环、换热与控制系统"},
        {"name": "数据中心", "role": "采购、部署并运营AI算力基础设施"},
    ],
    "relations": [
        {
            "source": "AI芯片",
            "relation": "ComponentOf",
            "target": "液冷服务器",
            "mechanism": "AI芯片是液冷服务器的核心算力与主要热源部件",
        },
        {
            "source": "服务器冷板",
            "relation": "ComponentOf",
            "target": "液冷服务器",
            "mechanism": "冷板把芯片热量传递给液冷回路",
        },
        {
            "source": "液冷服务器",
            "relation": "DependsOn",
            "target": "液冷系统",
            "mechanism": "液冷服务器依赖循环、换热和控制系统持续散热",
        },
        {
            "source": "液冷服务器",
            "relation": "InputTo",
            "target": "数据中心",
            "mechanism": "液冷服务器是AI数据中心扩容的算力设备投入",
        },
    ],
}

EVIDENCE_IDS = [
    "EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd",
    "EVDd50775dc-1ace-51f6-8e17-acaa4e25cb41",
    "EVD2e06b439-94cf-5df2-b4a9-8e2b11f3d6a4",
]


def episode_uuid(name: str) -> str:
    return str(uuid5(DEMO_NAMESPACE, name))


TOPOLOGY_EPISODE_UUID = episode_uuid("topology")
EVIDENCE_EPISODE_UUIDS = {
    evidence_id: episode_uuid(f"evidence:{evidence_id}") for evidence_id in EVIDENCE_IDS
}

# This fixture is an authoritative domain acceptance contract, not an LLM conclusion. It lets the
# pipeline detect whether extraction attached each derived signal to the intended stable anchor.
EXPECTED_SIGNAL_TARGETS = {
    "EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd": {"数据中心"},
    "EVDd50775dc-1ace-51f6-8e17-acaa4e25cb41": {"AI芯片"},
    "EVD2e06b439-94cf-5df2-b4a9-8e2b11f3d6a4": {"数据中心"},
}

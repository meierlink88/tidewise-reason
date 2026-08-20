#!/usr/bin/env python3
"""PROTOTYPE: run a three-node OpenSPG + KAG + LLM reasoning smoke."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
import re
import sys
from typing import Any


HOST_ADDR = "http://127.0.0.1:8887"
NAMESPACE = "ReasonSmoke"
MODEL_NAME = "DeepSeek V4 Flash"
CURRENT_STAGE = "startup"


def enter_stage(name: str) -> None:
    global CURRENT_STAGE
    CURRENT_STAGE = name


def read_model_config() -> tuple[dict[str, Any], dict[str, Any]]:
    lines = [line for line in sys.stdin.read().splitlines() if line.strip()]
    if len(lines) != 2:
        raise RuntimeError("expected protected LLM and vectorizer configuration inputs")

    def first_config(raw: str) -> dict[str, Any]:
        value = json.loads(raw)
        if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
            raise RuntimeError("unexpected OpenSPG model configuration shape")
        return value[0]

    return first_config(lines[0]), first_config(lines[1])


def create_or_update_project(
    llm_config: dict[str, Any], vectorizer_config: dict[str, Any]
) -> tuple[int, dict[str, Any], dict[str, Any]]:
    from knext.project.client import ProjectClient

    client = ProjectClient(host_addr=HOST_ADDR)
    tidewise = client.get_by_namespace("Tidewise")
    if tidewise is None:
        raise RuntimeError("the local Tidewise project is unavailable")
    base_config = json.loads(tidewise.config or "{}")
    graph_store = base_config.get("graph_store")
    if not isinstance(graph_store, dict):
        raise RuntimeError("the local graph-store configuration is unavailable")

    project_config = {
        "project": {
            "host_addr": HOST_ADDR,
            "namespace": NAMESPACE,
            "language": "zh",
            "biz_scene": "default",
        },
        "chat_llm": llm_config,
        "vectorizer": vectorizer_config,
        "graph_store": graph_store,
        "prompt": {"language": "zh"},
    }
    project = client.get_by_namespace(NAMESPACE)
    if project is None:
        project = client.create(
            name="Reason Smoke Prototype",
            namespace=NAMESPACE,
            config=project_config,
            desc="PROTOTYPE: three-node OpenSPG + KAG + LLM reasoning smoke",
            visibility="PRIVATE",
            tag="LOCAL",
            userNo="openspg",
        )
    else:
        client.update(
            id=project.id,
            namespace=NAMESPACE,
            config=project_config,
            visibility="PRIVATE",
            tag="LOCAL",
            userNo="openspg",
        )
    project_config["project"]["id"] = str(project.id)
    return int(project.id), project_config, graph_store


def solver_config(llm: dict[str, Any]) -> dict[str, Any]:
    retrieval_executor = {
        "type": "kag_hybrid_executor",
        "flow": "kg_cs",
        "lf_rewriter": {
            "type": "kag_spo_lf",
            "llm_client": llm,
            "lf_trans_prompt": {"type": "reason_smoke_lf_planning"},
        },
        "llm_client": llm,
    }
    return {
        "type": "kag_static_pipeline",
        "planner": {
            "type": "lf_kag_static_planner",
            "llm": llm,
            "plan_prompt": {"type": "reason_smoke_lf_planning"},
            "rewrite_prompt": {"type": "default_rewrite_sub_task_query"},
        },
        "executors": [
            retrieval_executor,
            {"type": "py_code_based_math_executor", "llm": llm},
            {"type": "kag_deduce_executor", "llm_module": llm},
            {
                "type": "kag_output_executor",
                "llm_module": llm,
                "summary_prompt": {"type": "reason_smoke_grounded_output"},
            },
        ],
        "generator": {
            "type": "llm_index_generator",
            "llm_client": llm,
            "generated_prompt": {"type": "default_refer_generator_prompt"},
            "enable_ref": True,
        },
    }


def register_reason_smoke_prompts() -> None:
    from kag.interface import PromptABC
    from kag.solver.prompt.lf_static_planning_prompt import (
        RetrieverLFStaticPlanningPrompt,
    )

    @PromptABC.register("reason_smoke_lf_planning")
    class ReasonSmokePlanningPrompt(RetrieverLFStaticPlanningPrompt):
        def __init__(self, **kwargs: Any):
            super().__init__(std_schema=None, **kwargs)
            self.template_zh = """
你是 ReasonSmoke 项目的 KAG 规划器。只规划检索与基于检索结果的判断，不得使用模型常识补充事实。

可用 Schema（英文内部名称必须原样使用）：
- Company -produces-> Product
- Product -usesMaterial-> Commodity

当问题询问公司产品的原材料时，必须先检索 produces，再检索 usesMaterial。
当问题询问是否使用某种材料时，必须先完成上述两次检索，然后用 Deduce 判断，最后 Output。
只输出 Step/Action，每个 Step 仅包含一个 Action。

示例：
Step1: 查询示例电缆公司生产的产品
Action1:Retrieval(s=s1:Company[`示例电缆公司`],p=p1:produces,o=o1:Product)
Step2: 查询该产品的原材料
Action2:Retrieval(s=o1,p=p2:usesMaterial,o=o2:Commodity)
Step3: 输出检索到的原材料
Action3:Output(o2)

如果是“是否使用某材料”的判断题，将 Step3 和后续步骤改为：
Step3: 根据检索结果判断用户问题
Action3:Deduce(op=judgement,content=[`o2`],target=`$query`)->res
Step4: 输出判断结果
Action4:Output(res)

用户问题：$query
"""
            self.template_en = self.template_zh

        def parse_response(self, response: str, **kwargs: Any) -> list[Any]:
            canonical = re.sub(
                r"(p=p\d+:)(?:生产产品|生产)(?=,)",
                r"\1produces",
                response,
            )
            canonical = re.sub(
                r"(p=p\d+:)(?:使用原材料|原材料)(?=,)",
                r"\1usesMaterial",
                canonical,
            )
            canonical = re.sub(
                r"(Action\d+:\s*)Retrieval\([^\n]*p=p\d+:produces[^\n]*\)",
                r"\1Retrieval(s=s1:Company[`示例电缆公司`],p=p1:produces,o=o1:Product)",
                canonical,
            )
            canonical = re.sub(
                r"(Action\d+:\s*)Retrieval\([^\n]*p=p\d+:usesMaterial[^\n]*\)",
                r"\1Retrieval(s=o1:Product,p=p2:usesMaterial,o=o2:Commodity)",
                canonical,
            )
            return super().parse_response(canonical, **kwargs)

    @PromptABC.register("reason_smoke_grounded_output")
    class ReasonSmokeGroundedOutputPrompt(PromptABC):
        template_zh = """
只根据上下文中的知识图谱检索结果回答问题“$question”。
不得使用模型内部知识，不得添加上下文中没有的实体或材料。
如果上下文不足，只回答“根据当前知识图谱无法确定”。
上下文：
$context
"""
        template_en = template_zh

        @property
        def template_variables(self) -> list[str]:
            return ["context", "question"]

        def parse_response(self, response: str, **kwargs: Any) -> str:
            return response


def write_runtime_config(
    target: Path,
    project_config: dict[str, Any],
    pipeline_config: dict[str, Any],
) -> None:
    config = dict(project_config)
    config["log"] = {"level": "ERROR"}
    config["vectorize_model"] = project_config["vectorizer"]
    config["kg_cs"] = {
        "type": "kg_cs_open_spg_legacy",
        "path_select": {"type": "exact_one_hop_select"},
        "entity_linking": {
            "type": "entity_linking",
            "recognition_threshold": 0.8,
            "exclude_types": ["Chunk"],
        },
        "llm": project_config["chat_llm"],
    }
    config["kag_solver_pipeline"] = pipeline_config
    target.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    target.chmod(0o600)


def configure_environment(project_id: int, graph_store: dict[str, Any]) -> None:
    os.environ.update(
        {
            "KAG_PROJECT_HOST_ADDR": HOST_ADDR,
            "KAG_PROJECT_ID": str(project_id),
            "KAG_PROJECT_NAMESPACE": NAMESPACE,
            "KAG_GRAPH_STORE_URI": str(graph_store.get("uri", "")),
            "KAG_GRAPH_STORE_USER": str(graph_store.get("user", "")),
            "KAG_GRAPH_STORE_PASSWORD": str(graph_store.get("password", "")),
            "KAG_GRAPH_STORE_DATABASE": str(graph_store.get("database", "neo4j")),
        }
    )


def commit_schema(schema_file: Path, project_id: int) -> None:
    from knext.schema.marklang.schema_ml import SPGSchemaMarkLang

    schema = SPGSchemaMarkLang(
        str(schema_file), host_addr=HOST_ADDR, project_id=project_id
    )
    schema.sync_schema()


def build_graph(project_id: int, vectorizer_config: dict[str, Any]) -> None:
    from kag.builder.component.vectorizer.batch_vectorizer import BatchVectorizer
    from kag.builder.component.writer.kg_writer import KGWriter
    from kag.interface import VectorizeModelABC
    from kag.interface.common.model.sub_graph import SubGraph

    graph = SubGraph([], [])
    graph.add_node(
        "company:demo-cable",
        "示例电缆公司",
        "Company",
        {"desc": "一家仅用于推理原型的虚构电缆生产企业。"},
    )
    graph.add_node(
        "product:power-cable",
        "电力电缆",
        "Product",
        {"desc": "用于输送电能的虚构演示产品。"},
    )
    graph.add_node(
        "commodity:copper",
        "铜",
        "Commodity",
        {"desc": "电力电缆使用的导体原材料。"},
    )
    graph.add_edge(
        "company:demo-cable",
        "Company",
        "produces",
        "product:power-cable",
        "Product",
    )
    graph.add_edge(
        "product:power-cable",
        "Product",
        "usesMaterial",
        "commodity:copper",
        "Commodity",
    )

    vectorizer = BatchVectorizer(
        vectorize_model=VectorizeModelABC.from_config(vectorizer_config)
    )
    vectorized = vectorizer.invoke(graph, write_ckpt=False)[0].data
    KGWriter(project_id=project_id).invoke(vectorized, write_ckpt=False)


def assert_graph(project_id: int) -> None:
    from knext.reasoner.client import ReasonerClient

    client = ReasonerClient(
        host_addr=HOST_ADDR,
        project_id=project_id,
        namespace=NAMESPACE,
    )

    def assert_hop(
        source_type: str,
        source_id: str,
        relation: str,
        target_type: str,
        target_id: str,
    ) -> None:
        response = client.syn_execute(
            f"""
            MATCH (s:`{NAMESPACE}.{source_type}`)-[p:`{relation}`]->(o:`{NAMESPACE}.{target_type}`)
            WHERE s.id in $sid and o.id in $oid
            RETURN s,p,o,s.id,o.id
            """,
            sid=json.dumps([source_id]),
            oid=json.dumps([target_id]),
        )
        task = response.task
        result = task.result_table_result if task is not None else None
        if task is None or task.status != "FINISH" or result is None or not result.rows:
            raise RuntimeError(
                f"prototype graph hop is unavailable: {source_id} -> {target_id}"
            )

    assert_hop(
        "Company",
        "company:demo-cable",
        "produces",
        "Product",
        "product:power-cable",
    )
    assert_hop(
        "Product",
        "product:power-cable",
        "usesMaterial",
        "Commodity",
        "commodity:copper",
    )


async def answer_all(
    queries: list[str], pipeline_config: dict[str, Any]
) -> list[tuple[str, dict[str, Any]]]:
    from kag.interface import SolverPipelineABC
    from kag.solver.reporter.trace_log_reporter import TraceLogReporter

    pipeline = SolverPipelineABC.from_config(pipeline_config)
    answers = []
    for query in queries:
        reporter = TraceLogReporter()
        result = await pipeline.ainvoke(query, reporter=reporter)
        trace, _ = reporter.do_report()
        answers.append((str(result), trace.to_dict()))
    return answers


def graph_facts(trace: dict[str, Any]) -> list[str]:
    facts = set()
    for retrieval in trace.get("decompose", []):
        for fact in retrieval.get("graph_data", []):
            facts.add(str(fact))
    return sorted(facts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, type=Path)
    args = parser.parse_args()
    enter_stage("read-model-config")
    llm_config, vectorizer_config = read_model_config()
    enter_stage("project")
    project_id, project_config, graph_store = create_or_update_project(
        llm_config, vectorizer_config
    )
    enter_stage("runtime-config")
    pipeline_config = solver_config(llm_config)
    runtime_config = Path.cwd() / "kag_config.yaml"
    write_runtime_config(runtime_config, project_config, pipeline_config)
    register_reason_smoke_prompts()
    configure_environment(project_id, graph_store)
    enter_stage("schema")
    commit_schema(args.schema, project_id)
    enter_stage("graph-write")
    build_graph(project_id, vectorizer_config)
    enter_stage("graph-read")
    assert_graph(project_id)

    enter_stage("answers")
    (positive, positive_trace), (negative, negative_trace) = asyncio.run(
        answer_all(
            [
                "示例电缆公司生产的产品使用什么原材料？请仅根据知识图谱回答。",
                "示例电缆公司生产的产品是否使用铝作为原材料？请仅根据知识图谱回答；没有证据时必须明确说无法确定。",
            ],
            pipeline_config,
        )
    )
    positive_facts = graph_facts(positive_trace)
    negative_facts = graph_facts(negative_trace)
    print("TRACE positive-evidence=" + json.dumps(positive_facts, ensure_ascii=False))
    print("TRACE negative-evidence=" + json.dumps(negative_facts, ensure_ascii=False))

    enter_stage("positive-answer")
    expected_facts = {
        '("示例电缆公司" produces "电力电缆")',
        '("电力电缆" usesMaterial "铜")',
    }
    if not expected_facts.issubset(set(positive_facts)):
        raise RuntimeError("the positive KAG trace did not contain the two-hop path")
    if "铜" not in positive:
        raise RuntimeError("the positive KAG answer did not contain the expected material")
    unsupported_materials = ("铝", "聚氯乙烯", "交联聚乙烯", "橡胶", "钢带")
    if any(material in positive for material in unsupported_materials):
        raise RuntimeError("the positive KAG answer added material absent from the graph")

    enter_stage("negative-answer")
    negative_markers = ("没有", "无法", "未找到", "无证据", "不能确定")
    if not any(marker in negative for marker in negative_markers):
        raise RuntimeError("the negative KAG answer did not preserve the evidence boundary")

    print("PASS runtime=local-reason-server")
    print(f"PASS model={MODEL_NAME}")
    print("PASS graph=3-nodes-2-edges")
    print("PASS positive-answer=铜")
    print("PASS positive-path=示例电缆公司->电力电缆->铜")
    print("PASS negative-answer=no-evidence")
    print(f"INFO project={NAMESPACE} project_id={project_id}")
    print(f"INFO positive={positive}")
    print(f"INFO negative={negative}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    try:
        main()
    except Exception as exc:
        detail = " ".join(str(exc).splitlines())[:500]
        print(
            f"FAIL stage={CURRENT_STAGE} type={type(exc).__name__} detail={detail}",
            file=sys.stderr,
        )
        raise SystemExit(1)

# Semantica Ontology 与内部 Reasoner 的真实连接方式

调研范围：Semantica 官方 `Ontology Management`、`Reasoning & Rules` 文档，以及当前 `main` 分支的 ontology、reasoning、ingest 源码。

## 结论

当前 Semantica 没有 `Reasoner.load_from_ontology()`，也没有把导入的 OWL class hierarchy、domain/range 或 restrictions 自动编译成内部 `Reasoner` / `DatalogReasoner` rules 的适配器。

- `Reasoner` 的入口是 `add_fact()`、`add_rule()`、`infer_facts()`。
- `DatalogReasoner` 的入口是 `add_fact()`、`add_rule()`、`load_from_graph()`；`load_from_graph()` 只把 `ContextGraph` 的 nodes/edges 转为 facts。
- `ingest_ontology()` 只把 OWL/RDF 解析成 `OntologyData.data`，包含 classes、properties、parents、domain/range 等结构。
- `OntologyValidator` 当前关于 HermiT/Pellet 的实现仍是 placeholder；官方 Ontology guide 也明确说明完整 OWL reasoning 在外部 HermiT、Pellet、ELK 中执行。

所以“内部规则使用 Ontology”的真实含义只能是：调用方读取 ontology dict，选取所需 axioms，转换成 Semantica rule syntax；或者仅使用 ontology 统一 rule 与 graph facts 的 predicate vocabulary。

## 三类输入必须区分

1. Ontology schema：`ThreatActor`、`Malware`、`uses`、`exploits`、`Malware subClassOf Software`。
2. KG instance facts：`ThreatActor(apt29)`、`Uses(apt29, sunburst)`。
3. Business rules：满足哪些事实时推导 `HighRiskActor`。

Ontology 提供词汇和可转换的 schema axioms，但 `HighRiskActor` 这样的风险政策不会仅凭 classes/properties 自动出现。

## 最小手动桥接方式

```python
from semantica.ingest import ingest_ontology
from semantica.reasoning import Reasoner, Rule

ontology = ingest_ontology("cti.ttl").data
reasoner = Reasoner()

# KG instance facts：来自 ContextGraph nodes/edges 或显式输入
for fact in [
    "ThreatActor(apt29)",
    "Uses(apt29, sunburst)",
    "Malware(sunburst)",
    "Exploits(sunburst, cve_2024_3400)",
    "CriticalVulnerability(cve_2024_3400)",
]:
    reasoner.add_fact(fact)

# 示例：把 Ontology 中 Malware subClassOf Software 手动编译成内部 rule
reasoner.add_rule(Rule(
    rule_id="owl-subclass-malware-software",
    name="Malware subClassOf Software",
    conditions=["Malware(?x)"],
    conclusion="Software(?x)",
    metadata={
        "source_ontology": "cti.ttl",
        "axiom": "Malware rdfs:subClassOf Software",
    },
))

# 业务规则不是 Ontology 自动生成的，需要单独定义
reasoner.add_rule(Rule(
    rule_id="risk-high-actor",
    name="Actor using critical-exploiting malware",
    conditions=[
        "ThreatActor(?x)",
        "Uses(?x, ?m)",
        "Malware(?m)",
        "Exploits(?m, ?v)",
        "CriticalVulnerability(?v)",
    ],
    conclusion="HighRiskActor(?x)",
    metadata={"vocabulary": "cti.ttl", "policy": "risk-policy-v1"},
))

results = reasoner.forward_chain()
for result in results:
    print(result.conclusion)
    print(result.premises)
    print(result.rule_used.metadata if result.rule_used else {})
```

变量应写成 `?x`、`?m`、`?v`。当前 `Reasoner._match_pattern()` 识别的是 `?variable`；官方 guide 中部分使用裸 `X` 的示例与当前实现并不一致。

## 可以从 Ontology 编译哪些简单规则

- `A subClassOf B` → `IF A(?x) THEN B(?x)`。
- `p domain A` → `IF p(?s, ?o) THEN A(?s)`。
- `p range B` → `IF p(?s, ?o) THEN B(?o)`。
- `A equivalentClass B` → 两条方向相反的类型规则。

这是一个有限的自定义 adapter，不等于完整 OWL semantics。复杂的交集、并集、否定、cardinality、property chain、开放世界语义等，应交给真正的 OWL reasoner。

## Provenance 限制

`InferenceResult` 会返回 `conclusion`、`premises`、`rule_used` 和 `confidence`，但不会自动说明规则来自哪个 Ontology。调用方可像上例那样把 ontology URI、版本和 axiom 放进 `Rule.metadata`，再从 `result.rule_used.metadata` 读取。

## 官方依据

- [Ontology Management](https://docs.getsemantica.ai/guides/ontology/)
- [Reasoning & Rules](https://docs.getsemantica.ai/guides/reasoning/)
- [Reasoner source](https://github.com/semantica-agi/semantica/blob/main/semantica/reasoning/reasoner.py)
- [DatalogReasoner source](https://github.com/semantica-agi/semantica/blob/main/semantica/reasoning/datalog_reasoner.py)
- [Ontology ingestor source](https://github.com/semantica-agi/semantica/blob/main/semantica/ingest/ontology_ingestor.py)
- [Ontology validator source](https://github.com/semantica-agi/semantica/blob/main/semantica/ontology/ontology_validator.py)

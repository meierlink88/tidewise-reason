# Semantica Cookbook：运行机制与预定义 Ontology

## 核心结论

Semantica 是模块化的知识工程工具箱。Cookbook 的端到端案例均通过显式调用把 ingest、parse、normalize、extract、KG、ontology、reasoning、storage、context 等模块串起来；模块不会因为某份 Ontology 存在就自动彼此连接。

预定义 Ontology 的官方推荐路径由 `advanced/13_Manual_Ontology_Snowflake_Mapping.ipynb` 明确给出：

```text
人工定义 Ontology as code
  -> 从数据源读取原始数据
  -> 显式 mapping / semantic transformation
  -> 构建 ontology-aligned KG
  -> 从 ontology 生成 OWL 与 SHACL
  -> 显式执行 graph validation（如需要）
  -> 写入 TripletStore 并用 SPARQL 查询
```

## 预定义 Ontology 如何生效

1. Ontology 先声明稳定的 class、object property、datatype property、domain、range、required/cardinality 与 namespace。
2. Ingestor 只读取数据；不会检查表结构、推断 class，也不会把字段自动映射到 Ontology。
3. 调用方编写 mapping，将业务主键变成稳定 node ID，将字段值路由到 Ontology property，将记录组装为 Ontology class，并生成使用标准 URI 的 edge。这一层被 Cookbook 原文称为 “the part that makes your ontology real”。
4. `OntologyEngine.validate(ontology)` 校验 Ontology 自身结构；`to_shacl()` / `export_shacl()` 从 Ontology 生成 SHACL shapes。
5. `OntologyEngine.validate_graph(data_graph, ontology=ontology)` 才执行实例图的 SHACL 校验并返回报告。
6. 当前 `TripletStore.store(knowledge_graph, ontology)` 的源码把 Ontology schema triples 与 KG instance triples 一起序列化/加载，并用 Ontology namespace 生成 IRI；该函数本身没有调用 `validate_graph()`，因此不能把“传入 ontology”理解为自动 SHACL 入库门禁。

## Ontology 的作用边界

- 对 extraction：默认没有直接作用；`NERExtractor`、`RelationExtractor` 不会自动读取 Ontology。
- 对 semantic mapping：作为目标语义模型；映射代码必须显式使 entity type、property、edge、URI 与它一致。
- 对 validation：生成 SHACL shapes，并在显式调用 `validate_graph()` 时检查实例图。
- 对 storage/query：提供统一 namespace、class/property IRI，使不同数据源能进入同一个 RDF/SPARQL 语义空间。
- 对 reasoning：Ontology/规则为推理提供语义基础，但 Cookbook 的推理案例仍显式加载 facts、定义 rules 并调用 reasoner；不是自动发生。
- 对 context/agent：ContextGraph、vector store、AgentContext 需要显式构造和注入；Ontology 不自动变成 agent memory 或 GraphRAG context。

## Cookbook 体现的理念

- 模块化：每个模块可独立使用。
- 显式编排：端到端流程由应用或 Pipeline DSL 串联。
- Schema 与物理数据源解耦：数据源 schema 变化只改 mapping，稳定 Ontology 不应静默漂移。
- 原始事实、语义模型、质量校验、推理、存储是不同阶段。
- 自动能力主要发生在明确调用的模块内部（例如 NER、OntologyGenerator、Reasoner），不是跨模块的隐式魔法。

## 官方来源

- [Cookbook Index](https://docs.getsemantica.ai/cookbook/)
- [Welcome to Semantica notebook](https://github.com/semantica-agi/semantica/blob/main/cookbook/introduction/01_Welcome_to_Semantica.ipynb)
- [Ontology notebook](https://github.com/semantica-agi/semantica/blob/main/cookbook/introduction/14_Ontology.ipynb)
- [Unstructured Text to Ontology notebook](https://github.com/semantica-agi/semantica/blob/main/cookbook/advanced/12_Unstructured_to_Ontology.ipynb)
- [Manual Ontology + Snowflake Mapping notebook](https://github.com/semantica-agi/semantica/blob/main/cookbook/advanced/13_Manual_Ontology_Snowflake_Mapping.ipynb)
- [Semantic Layer Construction notebook](https://github.com/semantica-agi/semantica/blob/main/cookbook/advanced/09_Semantic_Layer_Construction.ipynb)
- [OntologyEngine source](https://github.com/semantica-agi/semantica/blob/main/semantica/ontology/engine.py)
- [TripletStore source](https://github.com/semantica-agi/semantica/blob/main/semantica/triplet_store/triplet_store.py)

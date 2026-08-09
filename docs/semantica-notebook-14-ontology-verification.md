# Semantica Notebook 14 Ontology 用法核对

## 结论

`cookbook/introduction/14_Ontology.ipynb` 与此前对 Ontology 生成路径的理解一致：它把已经结构化的 entities/relationships（或自然语言描述）转换成 Ontology schema，并管理、评估和导出这个 schema。它没有展示预定义 Ontology 自动约束 NER、RelationExtractor 或 GraphBuilder。

## Notebook 实际展示的 API

- `OntologyEngine.from_data(data)`：从已有 entities/relationships 推断 classes、properties、domain/range 和 hierarchy。
- `ClassInferrer` / `PropertyGenerator`：对输入中的 type、属性和关系做更细粒度的 schema 推断。
- `OntologyOptimizer`：清理 Ontology 自身的重复或结构问题；不是 KG instance entity resolution。
- `LLMOntologyGenerator.generate_ontology_from_text()`：从领域描述生成 schema；不是从 Event 抽取实例事实。
- `CompetencyQuestionsManager.validate_ontology()`：检查 Ontology 是否包含回答需求问题所需的术语；不是 SHACL instance graph validation。
- `VersionManager` / `ReuseManager`：对 Ontology 做版本管理与外部 vocabulary import。
- `to_owl()` / `export_owl()`：把 Ontology 序列化为 Turtle/OWL。

## 没有展示的能力

- 没有把 Ontology 传给 `NERExtractor` 或 `RelationExtractor`。
- 没有把预定义 Ontology 自动映射到原始字段或 Event。
- 没有调用 `OntologyEngine.validate_graph()` 做 SHACL 实例图校验。
- 没有展示 Ontology 自动修改 KG 或自动触发推理。

Notebook 最后把“将生成的 Ontology feed into Knowledge Graph module 进行推理”列为下一步，说明这仍然是后续显式集成，而不是本 notebook 已自动完成的机制。

## 文档质量提示

- 标题写 “5-Stage”，正文称 “6-stage”，实际只列出 5 个阶段。
- Summary 称“serialized your knowledge graph”，但代码实际导出的是 Ontology。
- 开头称“validated OWL ontologies”，但 notebook 没有调用 SHACL graph validation。

## 官方来源

- [Notebook 14 — Ontology](https://github.com/semantica-agi/semantica/blob/main/cookbook/introduction/14_Ontology.ipynb)
- [Raw notebook](https://raw.githubusercontent.com/semantica-agi/semantica/refs/heads/main/cookbook/introduction/14_Ontology.ipynb)

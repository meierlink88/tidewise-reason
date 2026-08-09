# Semantica Ontology: “When To Use” 的实现机制

调研范围：Semantica 官方 `Ontology Management`、`SHACL Validation`、`Reasoning & Rules` 文档及当前 `main` 分支源码。

## 核心结论

Ontology 在 Semantica 中主要是知识图谱的正式 schema contract。它可以从已有 KG 生成，也可以由 OWL/RDF 导入；加载本身不会自动改变实体提取、修正事实或阻止入库。要影响实际数据流程，调用方需要显式启用对齐、SHACL 校验、推理、版本治理或导出环节。

典型生命周期：

1. 从 KG 生成 Ontology，或导入预定义 Ontology。
2. 审核 classes、object/datatype properties、hierarchy、domain/range 和 namespace。
3. 发布带稳定 IRI 和版本的 schema。
4. 将 schema 用于以下一个或多个消费者：跨团队映射、SHACL 数据门禁、OWL/规则推理、长期版本治理、外部工具。

## 五种用途如何实现

### 1. Formal knowledge graphs with complex entity relationships

- `OntologyGenerator`、`ClassInferrer`、`PropertyGenerator` 将 KG 中的实体类型、关系和属性正式化为 OWL classes、object properties、datatype properties、class hierarchy、domain/range。
- `base_uri` 为概念和关系生成稳定、全局唯一的 IRI。
- `OWLGenerator` / `export_owl` 将模型序列化为机器可读的 OWL/RDF。
- 这些声明描述“允许和期望的结构”，但不自动约束实例数据。要执行数据约束，应生成或手写 SHACL shapes，并调用验证器。

### 2. Data integration across multiple teams or organizations

- 所有团队使用共同 namespace 和 canonical IRIs，避免 `ThreatActor`、`Threat_Actor` 等命名漂移。
- `OntologyEngine.create_alignment()` 可用 `owl:equivalentClass`、`owl:equivalentProperty`、`owl:sameAs`、SKOS match 关系记录不同词表间的映射。
- `QueryEngine.expand_entity_uri(..., use_alignments=True)` 可在查询时把概念扩展到已对齐的等价 URI。
- Semantica 不会自动协商语义或合并不同团队的数据。团队仍需约定 canonical ontology、创建映射，并让查询或导入流程显式使用这些映射。

### 3. Automated reasoning and rule-based systems

- OWL class hierarchy和公理可供 OWL reasoner 推导隐含事实，例如 `Malware subClassOf Software` 且 `HAMMERTOSS rdf:type Malware`，可推出它也是 `Software`。
- 官方 Ontology guide 明确：Semantica 负责导出 OWL/Turtle；HermiT、Pellet、ELK 等外部工具负责 OWL reasoning。
- Semantica 自己另有 `Reasoner`、Datalog、RETE 等规则引擎，但它们运行调用方提供/从 `ContextGraph` 加载的 facts 和显式 rules；导入的 Ontology 不会自动变成这些规则。
- 推理所得事实默认在 working memory 中；要写回 KG，需要调用方显式持久化。

### 4. Long-term knowledge bases that need consistency over time

- 稳定的 element IRI 保证同一概念跨版本仍有同一身份。
- `VersionManager` 支持 ontology version IRI、`owl:versionInfo`、版本比较、diff 和 migration。
- SHACL 可成为每批新数据或发布前的数据质量门禁；`TemporalVersionManager` 可为 KG 做快照、diff、回滚和完整性校验。
- 官方文档说明 ontology 会 drift：新类型出现后，必须监控、重新生成或增量更新。Semantica 提供组件，但不会后台自动同步、审批或迁移 ontology。

### 5. Integration with external tools that expect OWL/RDF schemas

- `export_owl` / `export_rdf` 可输出 OWL/XML、Turtle、JSON-LD、N-Triples。
- 对应消费者包括 Protégé、OWL API、HermiT/Pellet、SHACL 工具链、GraphDB、Stardog、Oxigraph 和 linked-data API。
- `ingest_ontology` 支持把外部 OWL/RDF 词表导入 Semantica。
- Semantica解决的是标准格式和 schema 互操作；调用方仍需把文件加载进外部系统，并确保实例数据使用同一套 IRIs。

## 何时不值得使用

如果场景只是文档语义搜索、轻量 RAG、schema 快速变化的原型或一次性分析，没有 validator、reasoner、跨团队数据消费者或长期治理流程，Ontology 的建模、映射、版本和迁移成本通常大于收益。

## 官方依据

- [Ontology Management](https://docs.getsemantica.ai/guides/ontology/)
- [SHACL Validation](https://docs.getsemantica.ai/guides/shacl-validation/)
- [Reasoning & Rules](https://docs.getsemantica.ai/guides/reasoning/)
- [Change Management](https://docs.getsemantica.ai/guides/change-management/)
- [OntologyEngine source](https://github.com/semantica-agi/semantica/blob/main/semantica/ontology/engine.py)
- [QueryEngine source](https://github.com/semantica-agi/semantica/blob/main/semantica/triplet_store/query_engine.py)

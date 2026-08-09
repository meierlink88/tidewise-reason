# Semantica Ontology / Vocabulary 导入后的真实数据流

核对基线：Semantica 官方仓库 `main` commit `e90bd048e18ff81d5a1e30a2a95e1be469bd2c23`，以及当前 Tidewise 本地部署锁定的 `semantica==0.6.0`。

## 结论

Semantica 的 Ontology 能力是模块化、显式调用的能力，不是全局自动中间件。导入 Ontology/Vocabulary 会使其可被 Explorer 浏览、搜索、治理，并可由显式 SHACL、alignment、query expansion 等操作消费；它不会自动改变 NER、normalization、KG build 或 Explorer enrichment extraction。

截图中的页面是 `Vocabulary Browser`，其导入路径主要是 SKOS 词表浏览，不等同于完整 OWL Ontology Hub。

## 截图中的 Import Vocabulary

前端 `explorer/src/workspaces/VocabularyWorkspace/queries.ts` 将文件 POST 到 `/api/vocabulary/import`。

后端 `semantica/explorer/routes/vocabulary.py`：

1. 调用 `parse_skos_file()`；
2. 得到 nodes / edges；
3. 写入当前 Explorer `GraphSession` 的 `ContextGraph`；
4. `/api/vocabulary/schemes`、`/concepts`、`/hierarchy` 再读取这些节点和边供 UI 展示。

`semantica/explorer/utils/rdf_parser.py` 只提取：

- `skos:ConceptScheme`；
- `skos:Concept`；
- `skos:prefLabel`、`skos:altLabel`、`skos:definition`；
- `skos:broader`、`narrower`、`inScheme`、`related` 等结构关系。

它不会在这个入口把业务事件实体自动映射到 SKOS concept。

官方源码：

- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/explorer/src/workspaces/VocabularyWorkspace/queries.ts>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/explorer/routes/vocabulary.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/explorer/utils/rdf_parser.py>

## 完整 Ontology Hub 的显式消费点

`/api/ontology/load` 可通过 `OntologyIngestor` 解析 OWL classes / properties，将它们作为 ontology nodes / edges 加入同一 Explorer graph，并在 registry 中登记。导入后可显式用于：

- ontology / SKOS 浏览、搜索与详情；
- ontology health；
- cross-ontology alignment 建议与人工 authoring；
- 从 ontology 生成 SHACL shapes；
- 调用 `/api/ontology/shacl/validate` 进行 SHACL 验证；
- proposals、versioning、diff 等治理操作；
- 在持久 TripletStore 中保存 alignment 后，由 `QueryEngine.expand_entity_uri(..., use_alignments=True)` 显式扩展查询 URI。

官方源码：

- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/explorer/routes/ontology.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/ontology/engine.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/triplet_store/query_engine.py>

## 没有自动联动的环节

Explorer `/api/enrich/extract` 直接调用 `semantic_extract.methods.extract_entities()` 与 `extract_relations()`，没有读取当前 GraphSession 中的 Ontology/Vocabulary。`semantica.semantic_extract` 与 `semantica.normalize` 当前也没有导入 Ontology 的通用自动路径。

`split_ontology_aware()` 当前源码明确是占位实现：忽略 `ontology_uri`，转而调用 entity-aware splitting。

SHACL validation 是显式操作，返回 conform / violations；它不是 ingest 前置门禁，也不会自动拒绝或改写事实。Alignment 同样不自动重写实体，只有显式 alignment-aware query 才扩展 URI。

官方源码：

- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/explorer/routes/enrich.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/split/methods.py>

## 当前 Tidewise 部署的额外边界

当前项目固定 `semantica[explorer,...]==0.6.0`，并把 `semantic-runtime` 与 `semantica-explorer` 作为两个独立容器运行：

- Semantic Runtime 连接 Neo4j / Qdrant；
- Explorer 加载 `/data/context-graph.json` 到独立的内存 `GraphSession`；
- Semantica 0.6.0 不会把 Explorer 自动绑定到 Semantic Runtime 的 Neo4j / Qdrant；
- Explorer import 修改当前进程中的 ContextGraph，源码没有自动 `save_to_file()`；重启前若未显式导出，导入变更不会自动写回初始 JSON；
- Ontology registry 和 Explorer alignment store 也位于 `request.app.state`，是进程内状态。

项目依据：

- `AGENTS.md`
- `CONTEXT-MAP.md`
- `services/semantic-runtime/CONTEXT.md`
- `docs/design/one-click-runtime-v1.md`
- `services/semantic-runtime/src/tidewise_semantic_runtime/explorer.py`
- `services/semantic-runtime/pyproject.toml`

## 正确使用模型

```text
导入 Ontology / Vocabulary
  -> 形成可查询的 classes / properties / concepts / hierarchy
  -> 显式选择一个消费动作：
       A. 用 labels / altLabels 做实体候选映射
       B. 用 class/property URI 对齐抽取结果
       C. 用 SHACL 验证待入库或已入库 RDF
       D. 用 alignments 扩展查询
       E. 用 ontology axioms + reasoning engine 做推理
```

当前 Semantica Explorer 已实现其中的浏览、治理、SHACL、alignment 等工具，但没有把 A/B/C 自动挂到 event extraction → KG ingestion 的流水线上。

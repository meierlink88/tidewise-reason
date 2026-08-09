# Semantica Explorer 的官方定位、数据源与规模边界

调研范围：Semantica 官方 `Explorer Setup`、`Explorer Reference`、README，以及当前 `main` 分支的 Explorer CLI、FastAPI app 和 GraphSession 源码。

## 结论

Semantica Explorer 不是单纯的演示页面；官方将它定义为浏览器中的知识图谱工作台，用于图搜索、邻域/路径分析、Ontology Hub、SHACL、对齐、决策、溯源、标注、导入导出和分析。

但是，当前实现也不是 Neo4j/Qdrant 的生产实时管理台：CLI 强制要求一个由 `ContextGraph.save_to_file()` 生成的 JSON 文件，启动时将整张图加载进内存。当前没有 Neo4j、Qdrant 或 FalkorDB 的直接连接参数；源码明确注释，FalkorDB 直连是 future support。

因此，若生产 KG 已持久化在 Neo4j，想在当前 Explorer 中查看它，就需要另行生成一个 ContextGraph JSON 快照或限定子图。这种快照投影是官方 CLI 的既定使用方式；但官方没有提供 Neo4j/Qdrant 与 Explorer 的实时同步机制。

## 是否只是 Demo

不是纯 Demo。官方提供完整 REST API、WebSocket graph mutation、图搜索、路径、分析、Ontology、SHACL、reasoning、decision/provenance 等能力，并称其为 browser-based graph workbench / interactive dashboard。

但它具有明显的本地交互式工具边界：

- 图和 Explorer session 都在内存中。
- session 修改没有 auto-save，重启会丢失，需显式 export。
- CLI 没有内置 authentication 或 TLS。
- 它不是 Neo4j/Qdrant 的 live console。

较准确的定位是：对一个 ContextGraph 快照或受控子图进行交互探索和语义治理的工作台，而非生产 KG 的唯一存储或实时运维界面。

## ContextGraph JSON 会不会很大

会。文件大小随 nodes、edges、properties 线性增长；`save_to_file()` 使用带缩进的普通 JSON，并将 node/edge metadata 一并保存。Explorer 还会把整个文件加载进 Python 内存并建立本地搜索索引，因此运行内存通常高于文件本身。

官方给出的边界提示存在两个不同维度：

- 索引搜索曾在 118k nodes 图上测试；超过 500k nodes 需预留更长启动时间。
- 但官方同时警告，超过 10k nodes 应在导出 JSON 前过滤到相关子图，因为全量 force-directed layout 会不可用。
- `/api/import` 单次上传限制为 50 MB；CLI 初始 `--graph` 没有硬编码 50 MB 上限，但仍受文件解析、内存和浏览器渲染能力限制。

不应把 Qdrant 中的全量向量复制进 Explorer JSON，除非确实需要 Explorer 的 semantic-neighborhood/distance 功能。向量以 JSON 浮点数组保存会显著放大文件；基本图浏览只需要 ID、类型、显示属性和边。

## 对当前项目的含义

如果继续使用官方 Explorer，不应复制整个生产 KG。更合适的是由 Semantic Runtime 针对一次调试、调查或版本发布，生成有界的 ContextGraph 子图快照，并明确标记数据 revision。Neo4j/Qdrant 仍是完整投影；Explorer JSON 是诊断视图。

如果产品要求 Explorer 实时浏览完整 Neo4j，则需要扩展/fork Explorer，增加 server-backed GraphSession。这不是 Semantica 0.6.0 的官方现成功能。

## 官方依据

- [Explorer Setup](https://docs.getsemantica.ai/explorer-setup/)
- [Explorer Reference](https://docs.getsemantica.ai/reference/explorer/)
- [Semantica README — Knowledge Explorer](https://github.com/semantica-agi/semantica#knowledge-explorer)
- [Explorer CLI source](https://github.com/semantica-agi/semantica/blob/main/semantica/explorer/__init__.py)
- [Explorer app source](https://github.com/semantica-agi/semantica/blob/main/semantica/explorer/app.py)
- [GraphSession source](https://github.com/semantica-agi/semantica/blob/main/semantica/explorer/session.py)

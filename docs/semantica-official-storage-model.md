# Semantica 官方存储模型

## 结论

Semantica 不是“全部使用内存或文件”的系统。它是模块化 Python framework：开发示例默认大量使用内存结构和本地文件，以实现零配置启动；正式部署则通过 pluggable stores 使用持久化数据库。

| 模块 | 开发/本地模式 | 持久化/生产模式 |
| --- | --- | --- |
| `ContextGraph` | Python 内存 property graph | `save_to_file()` JSON；`AgentContext.save()` 保存 graph/vector/memory 快照 |
| `graph_store` | 可省略，或小图内存处理 | Neo4j、FalkorDB、Apache AGE、Amazon Neptune |
| `vector_store` | `inmemory` | FAISS 文件、Qdrant、Pinecone、Weaviate、Milvus、PgVector |
| `triplet_store` | Jena/rdflib 等本地模式 | Oxigraph 本地持久化；Blazegraph、RDF4J 等服务端存储 |
| `Explorer` | 从 ContextGraph JSON 加载到内存 | 当前没有直连 Neo4j/Qdrant 的官方实现 |

官方 `Learning More` 明确将 NetworkX/in-memory 推荐给开发和小图，将 Neo4j/FalkorDB 推荐给生产和大语料。Quickstart 的大图内存错误排查也要求切换到持久化 backend。Vector Store 文档同样把 `inmemory` 定义为开发/测试，把 FAISS 定义为本地持久化，并列出 Qdrant 等托管持久化后端。

因此目前的问题不是 Semantica Core 只能使用内存，而是 Explorer 这个应用没有接上 Semantica Core 已有的 persistent backend abstraction。Core 的存储能力和 Explorer 的数据访问实现并不一致。

## 官方依据

- [Architecture](https://docs.getsemantica.ai/architecture/)
- [Quickstart](https://docs.getsemantica.ai/quickstart/)
- [Learning More](https://docs.getsemantica.ai/learning-more/)
- [Graph Store](https://docs.getsemantica.ai/reference/graph_store/)
- [Vector Store](https://docs.getsemantica.ai/reference/vector_store/)
- [Triplet Store](https://docs.getsemantica.ai/reference/triplet_store/)
- [Explorer Setup](https://docs.getsemantica.ai/explorer-setup/)

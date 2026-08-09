# OpenSPG + KAG 图谱与向量技术核验

核验时间：2026-08-09

## 结论

当前官方产品模式默认采用一套以 Neo4j 为核心的融合存储：

- 图数据：Neo4j 属性图，通过 Cypher 查询；官方镜像启用 APOC。KAG 还调用 Neo4j GDS 执行 PageRank/PPR 等图算法。
- 向量数据：embedding 作为节点属性写入同一个 Neo4j，使用 Neo4j 原生 Vector Index 做近邻检索；源码支持 HNSW 参数，距离支持 cosine 或 euclidean，默认 cosine。
- 全文检索：使用 Neo4j Full-Text Index（底层为 Neo4j/Lucene 能力）。
- Embedding 模型：并未固定。KAG 支持 OpenAI/OpenAI-compatible、Azure、Ollama、本地 BGE/BGE-M3 等；官方 `domain_kg` 示例使用经 SiliconFlow 调用的 `BAAI/bge-m3`，1024 维。
- 元数据与文件：MySQL 保存产品/项目配置与任务元数据，MinIO 保存上传文件等对象；两者不承担图和向量检索。

因此，默认部署不是 `Neo4j + Qdrant/Milvus` 双库，而是 Neo4j 同时承担属性图、全文索引与稠密向量索引。

## 可替换范围

OpenSPG 的 `cloudext` 源码提供抽象与若干适配模块：

- Graph Store：Neo4j、TuGraph。
- Search Engine：Neo4j、Elasticsearch。

但当前官方 Docker Compose 把 `graphstore` 和 `searchengine` 两个连接都指向同一个 Neo4j；KAG 当前主要实现也是 Neo4j/内存图。源码中没有开箱即用的 Qdrant 或 Milvus 适配器。Elasticsearch 适配代码主要覆盖传统检索接口，不能直接等同于当前 KAG 的完整 Neo4j 向量路径。

## 实现证据

- 官方 Compose 的 `server` 同时把 `cloudext.graphstore.url` 与 `cloudext.searchengine.url` 配置为 Neo4j，并启动 MySQL、Neo4j、MinIO：<https://github.com/OpenSPG/openspg/blob/master/dev/release/docker-compose.yml>
- OpenSPG `cloudext` 声明 Neo4j/TuGraph 图存储与 Neo4j/Elasticsearch 搜索实现：<https://github.com/OpenSPG/openspg/blob/master/cloudext/pom.xml>
- OpenSPG 的 Neo4j 工具通过 `CREATE VECTOR INDEX` 与 `db.index.vector.queryNodes` 建索引和检索，支持 HNSW、cosine/euclidean：<https://github.com/OpenSPG/openspg/blob/master/common/util/src/main/java/com/antgroup/openspg/common/util/neo4j/Neo4jIndexUtils.java>
- KAG Neo4j GraphStore 同时初始化图索引、全文索引、向量索引，并调用 GDS PageRank：<https://github.com/OpenSPG/KAG/blob/master/kag/common/graphstore/neo4j_graph_store.py>
- 官方领域图谱示例使用 `BAAI/bge-m3`、1024 维，但模型通过配置注入：<https://github.com/OpenSPG/KAG/blob/master/kag/examples/domain_kg/kag_config.yaml>

## 对当前观潮家方案的含义

如果采用 OpenSPG + KAG，最顺滑的 PoC 是接受其默认 Neo4j 融合索引路线。保留当前 `Neo4j + Qdrant` 架构也可以，但 Qdrant 不是官方现成后端，需要自己实现 KAG/OpenSPG 的检索适配与双写一致性，工作量和风险都会增加。

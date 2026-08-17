# OpenSPG/KAG 0.8 横向扩容依赖矩阵

> 调查日期：2026-08-13  
> OpenSPG 基线：`v0.8` / `ceeb3ef549df79ca4c4878e7ff452c73584991f3`  
> 本地镜像：OpenSPG Server 0.8、Neo4j Enterprise 5.25.1、MariaDB 10.5.8、MinIO RELEASE.2024-12-18T13-15-44Z

## 结论

OpenSPG/KAG 使用的多数底层组件都有集群方案，但开源 OpenSPG 0.8 官方交付本身不是可直接水平扩容的分布式系统。官方 Compose 中 Server、Neo4j、MariaDB 和 MinIO 均只有一个实例。更关键的是，Server 默认使用进程内调度状态和线程池，Neo4j 适配中的多个读查询也会默认路由到 writer。

## 矩阵

| 组件 | 组件自身支持 | OpenSPG 0.8 默认集成 | 判断 |
|---|---|---|---|
| OpenSPG Server / KAG 产品服务 | HTTP 服务理论上可多副本 | 单容器；调度元数据默认 `local`，任务和 Future 保存在 `ConcurrentHashMap`，Builder/KAG 用进程内线程池和本地 Python | 不能把官方镜像直接加 replicas 当作完整水平扩容 |
| 调度元数据 | 源码存在 `db` 实现和 DB 抢锁 | 默认 `scheduler.handler.type=local` 且 `scheduler.metadata.store.type=local` | 具备改造起点，但无官方多副本生产部署指南/验收基准 |
| Neo4j 图+全文+向量 | Enterprise 集群支持 HA 和 secondary 读扩容 | 单实例；`neo4j://` 可使用 driver routing，但许多读路径直接 `session.run()`，默认按 write 模式路由 writer | 可做 HA/部分读扩容；不会线性扩展单图写入或存储 |
| MariaDB（镜像名为 MySQL） | primary-replica 可扩读，Galera 可 HA/多主 | 单实例、单 JDBC host | 可经 proxy/VIP 接集群；写入扩展不线性，Galera 会有复制和冲突成本 |
| MinIO | 支持多节点多盘、erasure coding 和新 server pool 扩容 | 单节点单 volume | 是最容易改成分布式的组件，OpenSPG 通过对象存储 endpoint 使用它 |
| LLM / Embedding API | 托管提供商或自建推理集群可水平扩容 | OpenSPG/KAG 只是 HTTP 客户端 | 扩容由模型端负责；配额、限流和模型延迟仍是上限 |
| Web UI | 静态资源可复制/CDN | 与 Server 同镜像 | 不是核心容量瓶颈 |

## 核心限制

### 1. OpenSPG Server 不是开箱即用的分布式 worker

官方默认配置选择本地 scheduler 和本地 metadata store。`LocalSchedulerTaskServiceImpl` 用静态 `ConcurrentHashMap` 保存任务，`MemoryTaskServer` 又用进程内 Map、Future 和线程池执行异步任务。负载均衡后的另一个 Server 副本不能看到这些状态。

源码确实包含 DB-backed scheduler 和数据库抢锁，说明开发者考虑了多主机协调。但它没有在官方 Compose 中启用，也不等于已验证的分布式任务队列。

### 2. Neo4j 集群主要解决 HA 和读扩容

Neo4j 集群对每个数据库仍只选一个 writer；多个 primary 用于写入仲裁和容灾，secondary 用于读扩容。因此普通 causal cluster 不是单图写分片。更多 primary 还可能增加同步确认延迟。

OpenSPG 使用 `neo4j://` 和官方 Java Driver，因此具有路由集群的基础。但其 Neo4j utility 内多个纯读查询直接在默认 Session 上调用 `run()`；Neo4j 官方说明这种方式默认路由 writer。若不修正为 read access/`executeRead`，增加 secondary 未必能为所有 OpenSPG 查询分流。

### 3. “组件可集群”不等于“整个系统可线性扩展”

即使将 MariaDB、Neo4j 和 MinIO 全部换成集群，KAG 的 LLM 调用、OpenSPG Builder 进程内线程池、单图 writer、向量索引更新和多跳图查询仍会形成独立瓶颈。

## 对观潮家的含义

当前每日数千事件和数千推理请求不要求立即进行全链路水平扩容。更合理的顺序是：

1. 先在单节点上通过定点索引、时间窗口、1–3 跳上限、异步导入和推理并发控制完成基准。
2. 需要 HA 时，再分别引入 MariaDB 代理/集群、Neo4j Enterprise cluster 和 distributed MinIO。
3. 在 OpenSPG Server 多副本前，必须实验 DB-backed scheduler、任务归属、失败恢复、幂等及本地 Python 执行边界。
4. 若终极要求单图写入和存储真正水平分片，不能仅靠 Neo4j causal cluster；需要额外的图分区/联邦设计，并验证 OpenSPG 适配层。

## 主要证据

- [OpenSPG 0.8 官方 Compose：所有核心服务均为单实例](https://github.com/OpenSPG/openspg/blob/ceeb3ef549df79ca4c4878e7ff452c73584991f3/dev/release/docker-compose.yml#L1-L95)
- [OpenSPG 默认配置：local scheduler 和 local metadata store](https://github.com/OpenSPG/openspg/blob/ceeb3ef549df79ca4c4878e7ff452c73584991f3/server/arks/sofaboot/src/main/resources/config/application-default.properties#L42-L61)
- [OpenSPG 本地调度任务状态](https://github.com/OpenSPG/openspg/blob/ceeb3ef549df79ca4c4878e7ff452c73584991f3/server/core/scheduler/service/src/main/java/com/antgroup/openspg/server/core/scheduler/service/metadata/impl/local/LocalSchedulerTaskServiceImpl.java#L29-L179)
- [OpenSPG 进程内异步任务执行](https://github.com/OpenSPG/openspg/blob/ceeb3ef549df79ca4c4878e7ff452c73584991f3/server/core/scheduler/service/src/main/java/com/antgroup/openspg/server/core/scheduler/service/common/MemoryTaskServer.java#L35-L119)
- [OpenSPG Neo4j 工具中的默认 Session 读取](https://github.com/OpenSPG/openspg/blob/ceeb3ef549df79ca4c4878e7ff452c73584991f3/common/util/src/main/java/com/antgroup/openspg/common/util/neo4j/Neo4jDataUtils.java#L300-L430)
- [Neo4j 集群架构](https://neo4j.com/docs/operations-manual/current/clustering/introduction/)
- [Neo4j Java Driver 的读路由建议](https://neo4j.com/docs/java-manual/current/performance/#_route_read_queries_to_cluster_readers)
- [MariaDB 复制与读扩容](https://mariadb.com/docs/server/ha-and-performance/standard-replication/replication-overview)
- [MariaDB Galera 架构及扩容代价](https://mariadb.com/docs/galera-cluster/galera-architecture/introduction-to-galera-architecture)
- [MinIO 多节点多盘部署](https://min.io/docs/minio/linux/operations/install-deploy-manage/deploy-minio-multi-node-multi-drive.html)
- [MinIO server pool 扩容](https://min.io/docs/minio/linux/operations/install-deploy-manage/expand-minio-deployment.html)

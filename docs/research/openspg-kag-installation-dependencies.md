# OpenSPG / KAG 安装要求与中间件依赖核验

核验时间：2026-08-09

核验基线：OpenSPG `master`（本地核验提交 `ceeb3ef549df79ca4c4878e7ff452c73584991f3`，对应 0.8 发布）与 KAG `master`（本地核验提交 `fdab15b3929d2ee40dfcdd388f90233096a6afc9`，`KAG_VERSION=0.8.0`）。

## 结论

官方最短体验路径是 Docker Compose，一次启动 OpenSPG/KAG 产品服务、MySQL、Neo4j 和 MinIO；随后还必须配置生成模型与 Embedding 模型，才能实际构建知识库和进行问答。默认部署不依赖 Qdrant、Milvus、Elasticsearch、Redis、Kafka、RabbitMQ 或 PostgreSQL。

官方 Quick Start 给出的硬件要求是：CPU 至少 8 核、内存至少 32 GB、磁盘至少 100 GB。官方推荐系统为 macOS Monterey 12.6+、CentOS 7 / Ubuntu 20.04+、Windows 10 LTSC 2021+；macOS/Linux 需要 Docker 与 Docker Compose，Windows 还依赖 WSL2 或 Hyper-V。

## 安装模式

### 1. 产品模式

宿主机只需 Docker/Compose 和访问镜像仓库、模型服务的网络。官方 Compose 启动以下组件：

| 组件 | 默认角色 | 暴露端口 | 是否默认必需 |
| --- | --- | --- | --- |
| `openspg-server:latest` | Web UI、OpenSPG API、Builder/Reasoner、KAG 产品能力 | 8887 | 是 |
| `openspg-mysql:latest` | 项目、用户、Schema、模型配置、任务等产品元数据 | 3306 | 是 |
| `openspg-neo4j:latest` | 属性图、全文索引、稠密向量索引、图算法 | 7474、7687 | 是 |
| `openspg-minio:latest` | 上传文件和对象存储 | 9000、9001 | 是 |
| 生成模型服务 | OpenIE/抽取、规划、推理、答案生成 | 供应商决定 | 实际使用必需 |
| Embedding 模型服务 | 构图阶段属性向量、查询向量 | 供应商决定 | 建库与语义检索必需 |

官方模型文档允许选择商业 API，或自行部署 vLLM、Ollama、Xinference 等本地模型服务。GPU 不是远程模型方案的官方硬性安装项；如果自托管大模型或本地 Embedding，GPU/显存和模型运维属于额外依赖。

### 2. KAG 开发者模式

开发者模式仍需先启动上面的 OpenSPG 引擎与依赖镜像，然后在宿主机安装：

- Git；
- Python 环境；官方 Quick Start 推荐 Python 3.10；
- Conda 或 `venv`、pip；
- 克隆 KAG 后执行 `pip install -e .`。

`setup.py` 的元数据写的是 Python `>=3.8`，但官方操作步骤明确使用 3.10。为了降低兼容风险，应按 3.10 锁定。KAG 的 `requirements.txt` 有大量未固定版本的依赖（例如 pydantic、neo4j、openai、pandas、httpx），不能直接当成可复现生产锁文件；PoC 应单独生成并验证完整锁文件。

### 3. OpenSPG 源码构建

使用官方预构建镜像不要求宿主机安装 Java/Maven。只有修改并构建 OpenSPG Java 服务时才需要：

- JDK 8（根 POM 与 CI 均固定 Java 8）；
- Maven；
- Scala 2.11.12 由 Maven 工程管理。

## 默认与可选中间件边界

OpenSPG `cloudext` 源码包含可插拔模块：

- Graph Store：Neo4j、TuGraph；
- Search Engine：Neo4j、Elasticsearch；
- Cache：Redis；
- Object Storage：MinIO、OSS。

但这些是适配能力，不等于默认安装依赖。当前官方 Compose 只启用 Neo4j、MySQL、MinIO，并将 `graphstore` 和 `searchengine` 都指向 Neo4j。源码中没有开箱即用的 Qdrant 或 Milvus 后端。

## 官方 Quick Start 的生产风险

官方 Compose 更适合本地体验，不能原样视为生产部署：

- 四个镜像都使用 `latest`，没有不可变版本或 digest；
- MySQL、Neo4j 的 `/data` 和 MinIO 的 `/data` 没有持久化卷；Neo4j 只挂载日志目录，删除或重建容器可能丢数据；
- 默认账号密码硬编码；
- 3306、7474、7687、9000、9001、8887 默认暴露到宿主机所有接口；
- Compose 没有 healthcheck，也没有基于健康状态的启动门槛；
- OpenSPG Server 配置为 JVM `-Xms2G -Xmx8G`，Neo4j 配置最大 4 GB heap 和 1 GB page cache，印证其不是轻量服务。

生产化至少需要：锁镜像版本/digest、独立持久卷、Secrets、仅内部网络开放中间件、健康检查、备份恢复、资源限制、TLS/认证、模型调用超时与重试、数据迁移和升级演练。

## 与当前 Tidewise Agent OS 的冲突

当前 `deploy/compose.yaml` 已占用 Neo4j 的 7474/7687，并由 Semantic Runtime 使用标准 `neo4j:5.26.28-community`；OpenSPG Quick Start 也占用相同端口，但使用其自有 `openspg-neo4j:latest` 镜像及插件组合。两套 Compose 不能按默认配置并行启动。

不能未经验证就让 OpenSPG 直接复用当前 Neo4j：OpenSPG 依赖 APOC、向量索引和 GDS/PageRank 路径，其自有镜像的插件/数据库能力需要锁版本实测。按仓库 authority，OpenSPG/KAG 若采用，应作为 Semantic Runtime 下游实现，并通过 Semantic Runtime 契约暴露；不应让 Agent Runtime 绕过契约直连其数据库。

PoC 有两个安全方向：

1. 独立启动 OpenSPG/KAG，修改其宿主机端口并使用独立持久卷，只做能力验证；
2. 设计并批准迁移后，用 OpenSPG/KAG 替换现有 Semantica + Neo4j/Qdrant 投影实现。

不建议在第一步让两套语义栈共享同一 Neo4j 数据库。

## 官方来源

- [KAG 官方 README / Quick Start](https://github.com/OpenSPG/KAG#4-quick-start)
- [OpenSPG/KAG 官方 Quick Start（含 8 核、32 GB、100 GB 要求）](https://openspg.yuque.com/ndx6g9/docs_en/rs7gr8g4s538b1n7)
- [官方 Docker Compose](https://github.com/OpenSPG/openspg/blob/master/dev/release/docker-compose.yml)
- [KAG Python 安装元数据](https://github.com/OpenSPG/KAG/blob/master/setup.py)
- [KAG Python 依赖](https://github.com/OpenSPG/KAG/blob/master/requirements.txt)
- [生成模型配置](https://openspg.yuque.com/ndx6g9/docs_en/uafdyw2s39rdmqn4)
- [Embedding 模型配置](https://openspg.yuque.com/ndx6g9/docs_en/ml7ogtxgm1x5oo2o)
- [OpenSPG Cloudext 适配模块](https://github.com/OpenSPG/openspg/blob/master/cloudext/pom.xml)
- [OpenSPG Java/Maven 根 POM](https://github.com/OpenSPG/openspg/blob/master/pom.xml)
- [OpenSPG 官方 CI（JDK 8）](https://github.com/OpenSPG/openspg/blob/master/.github/workflows/openspg-ci.yml)

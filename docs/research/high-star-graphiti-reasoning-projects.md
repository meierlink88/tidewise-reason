# 基于 Graphiti / Zep 的高星推理、预测与模拟项目核验

> 核验日期：2026-08-21  
> 范围：仅使用 GitHub 官方仓库页面、README、依赖清单和源码。Star 数来自当日 GitHub Repository API/仓库页面快照，会继续变化。  
> 判定标准：仓库必须在默认分支的依赖或实际源码中调用 Graphiti/Zep，且自身定位为推理、预测或模拟引擎；只在 README 提及 Graphiti、只提供记忆组件或普通 Agent 框架不算。

## 结论

**最可能对应的高星项目是 [`666ghj/MiroFish`](https://github.com/666ghj/MiroFish)，当前约 71,308 stars。**

它是本次检索中唯一同时满足“真正高星”“默认主线明确使用 Zep 图谱/记忆”“实际进行预测与多智能体模拟”的项目。没有发现第二个达到 1,000 stars、且默认源码明确使用 Graphiti OSS 或 Zep 的独立推理/预测/模拟引擎。

必须准确理解它的分工：**Zep 不是 MiroFish 的预测算法本身。** Zep 负责种子资料形成图谱、实体与关系检索、长期/时序记忆和模拟结果回写；真正推动社会互动模拟的是 OASIS，多智能体及 LLM 产生行为，ReportAgent 再从模拟图谱中检索和组织预测报告。

## 已确认项目

| 项目 | 当前 stars | 固定源码基线 | Graphiti/Zep 使用证据 | 实际定位与判断 |
| --- | ---: | --- | --- | --- |
| [`666ghj/MiroFish`](https://github.com/666ghj/MiroFish) | 71,308 | [`117ed377`](https://github.com/666ghj/MiroFish/tree/117ed37758cdc96f73b7d5e0d22713c50439695f) | 后端固定依赖 [`zep-cloud==3.25.0`](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/backend/pyproject.toml)；[`graph_builder.py`](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/backend/app/services/graph_builder.py) 创建 Zep graph、设置 ontology 并提交 Episode；[`simulation_manager.py`](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/backend/app/services/simulation_manager.py) 从 Zep 图谱取实体生成 OASIS profiles；[`zep_tools.py`](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/backend/app/services/zep_tools.py) 给报告阶段提供图搜索与实体关系工具 | 官方定位是“群体智能预测引擎”；工作流是图构建 → 人设/环境 → OASIS 双平台模拟 → ReportAgent 报告。它是最明确答案，但使用的是 **Zep Cloud**，不是直接依赖 `graphiti-core` |
| [`tt-a1i/MiroFish-local`](https://github.com/tt-a1i/MiroFish-local) | 148 | [`a4c47d3`](https://github.com/tt-a1i/MiroFish-local/tree/a4c47d3e3b3427b59fffe18781f84be45f346819) | [`requirements-graphiti.txt`](https://github.com/tt-a1i/MiroFish-local/blob/a4c47d3e3b3427b59fffe18781f84be45f346819/backend/requirements-graphiti.txt) 固定 `graphiti-core>=0.25,<0.26`；[`zep_graphiti_impl.py`](https://github.com/tt-a1i/MiroFish-local/blob/a4c47d3e3b3427b59fffe18781f84be45f346819/backend/app/services/zep_graphiti_impl.py) 实例化 `Graphiti` 并以 Neo4j 实现 Zep adapter；README 明确支持 `ZEP_BACKEND=cloud|graphiti` | MiroFish 的本地化 fork。预测/模拟路径仍由 OASIS + ReportAgent 承担，Graphiti + Neo4j 替代 Zep Cloud 的图谱和记忆层。是最直接的 Graphiti OSS 参考实现，但还不是高星项目 |
| [`mzjsbql-web/AGARS-Ai-Generated-Ai-Roleplay-Simulator`](https://github.com/mzjsbql-web/AGARS-Ai-Generated-Ai-Roleplay-Simulator) | 25 | [`1858758`](https://github.com/mzjsbql-web/AGARS-Ai-Generated-Ai-Roleplay-Simulator/tree/1858758cc73a17d9cf0e4f1d48080130152d734c) | [`pyproject.toml`](https://github.com/mzjsbql-web/AGARS-Ai-Generated-Ai-Roleplay-Simulator/blob/1858758cc73a17d9cf0e4f1d48080130152d734c/backend/pyproject.toml) 依赖 `graphiti-core[falkordb]>=0.28.0`；[`graph_builder.py`](https://github.com/mzjsbql-web/AGARS-Ai-Generated-Ai-Roleplay-Simulator/blob/1858758cc73a17d9cf0e4f1d48080130152d734c/backend/app/services/graph_builder.py) 明确实例化 Graphiti + FalkorDB | 互动叙事/角色扮演多智能体模拟器。Graphiti 主要负责本地图谱构建；源码说明搜索、实体读取和模拟更新仍走 Zep Cloud。属于混合迁移状态，不是成熟预测底座 |
| [`linroger/DeepResearchForecast`](https://github.com/linroger/DeepResearchForecast) | 8 | [`6df6b37`](https://github.com/linroger/DeepResearchForecast/tree/6df6b37d4829c89d19fe5d71c135062181526e26) | [`Graphiti client`](https://github.com/linroger/DeepResearchForecast/blob/6df6b37d4829c89d19fe5d71c135062181526e26/backend/app/services/graphiti_client/client.py) 是基于本地 Graphiti 的 Zep-compatible facade；[README](https://github.com/linroger/DeepResearchForecast/blob/6df6b37d4829c89d19fe5d71c135062181526e26/README.md) 明确使用 Graphiti + 嵌入式 FalkorDB | “深度研究 → 知识图谱 → 多智能体人群模拟 → 预测报告”，还增加因果边、多跳因果查询、时间轴和预测市场校准。与投研预测场景最接近，但 stars 很低、项目年轻，只适合源码参考和 PoC |

### MiroFish 的真实执行链

从默认分支源码能确认：

```text
用户上传种子材料 + 预测问题
          │
          v
Zep Cloud Graph
文本 Episode → 实体/关系/ontology → 图谱与初始记忆
          │
          v
Persona / Simulation Config
从图谱读取实体，LLM 生成人设、行为参数和环境配置
          │
          v
OASIS Multi-Agent Simulation
Agent 在 Twitter/Reddit 模拟环境中交互
          │
          v
Zep Dynamic Memory
可选地将模拟活动和时序变化写回图谱
          │
          v
ReportAgent
调用图搜索、全景检索、洞察与访谈工具生成预测报告
```

证据：MiroFish [README 工作流与 OASIS 说明](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/README.md)、[`simulation_runner.py`](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/backend/app/services/simulation_runner.py)、[`zep_graph_memory_updater.py`](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/backend/app/services/zep_graph_memory_updater.py)、[`report_agent.py`](https://github.com/666ghj/MiroFish/blob/117ed37758cdc96f73b7d5e0d22713c50439695f/backend/app/services/report_agent.py)。

因此，更准确的描述是：

> MiroFish 是“Zep 时态图谱/记忆 + OASIS 多智能体社会模拟 + LLM/ReportAgent 综合”的预测系统，不是由 Graphiti 图算法直接算出预测结论。

## 高星但不满足条件的相邻项目

### `nikmcfly/MiroFish-Offline`：2,475 stars，但已移除 Zep/Graphiti

[`MiroFish-Offline`](https://github.com/nikmcfly/MiroFish-Offline) 是值得关注的高星本地 fork，但不能列为 Graphiti 项目。固定基线 [`313fe64`](https://github.com/nikmcfly/MiroFish-Offline/tree/313fe642853ff9fff05e3ecae2e439886c2d29f4) 的 README 明确说它将 Zep Cloud 替换为自建 `Neo4jStorage + Ollama`；[`neo4j_storage.py`](https://github.com/nikmcfly/MiroFish-Offline/blob/313fe642853ff9fff05e3ecae2e439886c2d29f4/backend/app/storage/neo4j_storage.py) 直接使用 Neo4j driver，自行实现 NER/RE、embedding 和混合搜索，依赖清单没有 `graphiti-core`。

它证明 **MiroFish 的图谱后端可以被替换**，却不能证明 Graphiti 本身提供了预测/模拟能力。

### `getzep/graphiti` 和 `getzep/zep`

[`getzep/graphiti`](https://github.com/getzep/graphiti) 本身约 30k stars，[`getzep/zep`](https://github.com/getzep/zep) 约 4.9k stars，但它们是时态知识图谱/Agent memory 基础设施，不是独立的产业预测或多智能体模拟引擎，因此没有为了凑“高星”而列入结果。

## 对观潮家的启示

MiroFish 说明了一条成立的系统分工：图谱负责提供世界状态、角色关系和长时记忆，多智能体/LLM 才负责行为演化与结果综合。这与“Graphiti 作事件证据底座、Codex Agent 负责逐节点推导”的方向一致。

但它不能作为投研准确性的直接证明：

- MiroFish 模拟的是 Agent 群体交互和舆情/行为涌现，不是按产业链业务关系穷举每个节点；
- 图谱主要支撑上下文、人物关系、记忆和结果检索，不是确定性规则引擎；
- 预测结果仍高度依赖 LLM 生成人设、模拟参数、Agent 行为和 ReportAgent 综合；
- 高 star 说明项目关注度高，不等于金融预测已经过回测验证。

如果要借鉴，最有价值的是 MiroFish-local 的 **Graphiti adapter 边界** 和 DeepResearchForecast 的 **研究/图谱/模拟/报告分层**；不应直接复用其“让大量 Agent 自由互动即可预测产业链”的假设。

## 最终答案

**项目名：MiroFish。**

- 高星原版：[`666ghj/MiroFish`](https://github.com/666ghj/MiroFish)，使用 Zep Cloud 图谱/记忆。
- Graphiti OSS 版参考：[`tt-a1i/MiroFish-local`](https://github.com/tt-a1i/MiroFish-local)，使用 Graphiti + Neo4j，但当前只有 148 stars。
- 最接近投研预测的 Graphiti 实验：[`linroger/DeepResearchForecast`](https://github.com/linroger/DeepResearchForecast)，但当前只有 8 stars。

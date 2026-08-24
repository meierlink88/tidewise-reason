# KAG `think_pipeline` 与 `kag_thinker_pipeline` 血缘核查

核查日期：2026-08-20

## 结论

1. **两者都属于 KAG 体系。** 两份配置都位于官方 `OpenSPG/KAG` 仓库的
   `kag/solver/pipelineconf/` 下，且都组装同一个 `kag_static_pipeline`；它们不是“一个是
   KAG、一个不是 KAG”。官方 v0.8.0 同时包含
   [`deep_thought.yaml`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipelineconf/deep_thought.yaml)
   和
   [`kag_thinker.yaml`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipelineconf/kag_thinker.yaml)。
2. **`kag_thinker_pipeline` 在时间上更新。** `think_pipeline` 的配置最早于
   2025-04-05 加入，随 KAG 0.7 的 Solver 重构发布；`kag_thinker_pipeline` 于
   2025-06-20 以“support kag thinker model”加入，随 KAG 0.8.0 的 KAG-Thinker 适配发布。
3. **但官方没有把两者定义为“新一代替代老一代”。** 0.8.0 发布后两条管线仍并存，
   官方当前示例仍使用 `lf_kag_static_planner`。因此，准确说法是：前者是 KAG 0.7
   的通用逻辑形式规划路径，后者是 0.8 新增的 KAG-Thinker 专用适配路径；它们是并行
   方案，而不是已经确认的替代关系。

## 官方时间线

| 时间 | 官方事实 | 判断 |
|---|---|---|
| 2025-04-05 | 提交 [`95ff21c`](https://github.com/OpenSPG/KAG/commit/95ff21c919671e2cffaca7a1a6ba99d97149a589) 以 “add pipelineconf” 加入 `deep_thought.yaml`，其中名称为 `think_pipeline`、Planner 为 `lf_kag_static_planner` | `think_pipeline` 的源码起点 |
| 2025-04-17 | [KAG 0.7 发布说明](https://github.com/OpenSPG/KAG/releases/tag/v0.7)称 KAG-Solver 被完全重构，新增 Static/Iterative 两种任务规划模式和内置 Pipeline | `think_pipeline` 属于 KAG 0.7 Solver 架构 |
| 2025-06-20 | 提交 [`1bc3c0c`](https://github.com/OpenSPG/KAG/commit/1bc3c0c694609782521c8cfb3b250faf465d8786) 以 “support kag thinker model” 加入 `kag_thinker.yaml` 与 `kag_model_planner.py` | `kag_thinker_pipeline` 是后加入的模型适配路径 |
| 2025-06-27/28 | [KAG 0.8.0 发布说明](https://github.com/OpenSPG/KAG/releases/tag/v0.8.0)明确写明“完成了对 KAG-Thinker 模型的适配”，并把它描述为复杂问题广度拆分、深度求解、知识边界判断和抗噪检索的多轮迭代思考范式 | 后者是面向 KAG-Thinker 的新增能力 |

官方独立的
[`OpenSPG/KAG-Thinker`](https://github.com/OpenSPG/KAG-Thinker)
仓库把 KAG-Thinker 定义为“interactive thinking and deep reasoning model”，即一个面向复杂
多跳问题的模型及认知推理范式。这进一步说明 `kag_thinker_pipeline` 名字中的
“KAG Thinker”指的是该专门模型/协议适配，而不是“KAG 框架本身”的同义词。

## 两条管线在代码层的关系

| 对比项 | `think_pipeline` | `kag_thinker_pipeline` |
|---|---|---|
| 官方配置 | `deep_thought.yaml` | `kag_thinker.yaml` |
| 首次发布代际 | KAG 0.7 | KAG 0.8.0 |
| 外层执行框架 | `kag_static_pipeline` | `kag_static_pipeline` |
| Planner | `lf_kag_static_planner` | `kag_model_planner` |
| 规划接口 | `default_lf_static_planning` 生成逻辑形式计划 | `kag_system` + `kag_clarification`；Planner 按 KAG-Thinker 的 `<think>` / `<answer>` 输出协议解析结果 |
| 检索 Executor | `kag_hybrid_retrieval_executor` | `kag_model_hybrid_retrieval_executor`，另带 `kag_subquestion_think` |
| 官方定位 | KAG-Solver 的逻辑形式静态规划路径 | KAG-Solver 对 KAG-Thinker 模型的适配路径 |

以上结构可直接对照官方 v0.8.0 的
[`deep_thought.yaml`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipelineconf/deep_thought.yaml)、
[`kag_thinker.yaml`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipelineconf/kag_thinker.yaml)、
[`lf_kag_static_planner.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/planner/lf_kag_static_planner.py)
和
[`kag_model_planner.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/planner/kag_model_planner.py)。
后一份 Planner 源码显式解析 KAG-Thinker 输出中的 `</think>` 和 `<answer>` 标记，说明这不只是
给通用 Planner 换了一个名字，而是适配了特定模型输出协议。

## “新一代 / 老一代”应如何表述

### 可以确认的事实

- `kag_thinker_pipeline` 比 `think_pipeline` 晚一个正式版本加入。
- KAG 0.8.0 官方把 KAG-Thinker 适配列为新增能力，并强调多轮迭代式思考。
- KAG 0.8.0 和当前官方源码仍同时保留两条管线；当前
  [`domain_kg` 示例](https://github.com/OpenSPG/KAG/blob/master/kag/examples/domain_kg/kag_config.yaml)
  仍采用 `lf_kag_static_planner`。

### 不能从官方资料推出的说法

- 没有官方发布说明把 `think_pipeline` 标记为 deprecated、legacy 或 removed。
- 没有官方资料声明 `kag_thinker_pipeline` 对所有模型和场景全面取代
  `think_pipeline`。
- 因此不能笼统称前者为“废弃的老一代”、后者为“通用的新一代”。

### 最合理的工程解释（推断）

`think_pipeline` 是对普通聊天 LLM 较通用的 KAG 逻辑形式规划基线；
`kag_thinker_pipeline` 是更新、但更专门化的 KAG-Thinker 模型协议路径。这个判断来自
官方提交名称、0.8.0 发布说明和两套 Planner/Executor 的结构差异；官方没有声明后者只允许
KAG-Thinker 模型，因此“专门化”是目标适配关系，不是代码中的模型名称硬校验。不过，其他
LLM 若不能稳定遵循相同的 `<think>` / `<answer>` 协议，就不应假定能获得等价行为。

## 对当前 DeepSeek v4 Demo 的含义

当前目标是用 DeepSeek v4 验证 OpenSPG + KAG + LLM 的基本推理闭环。基于上述血缘，选择
`think_pipeline` 更合适：不是因为它是应被淘汰的旧方案，而是因为它是仍在官方保留和示例
使用的通用 KAG 路径，并且当前镜像中的该配置完整。

如果后续目标变为评估 KAG-Thinker 模型或其多轮迭代思考协议，再选择
`kag_thinker_pipeline` 更匹配；届时应先解决当前镜像中它缺失 `rewrite_prompt` 的配置/代码
一致性问题。

## 当前本地运行时核对

- `reason-server` 内安装版本：`openspg-kag 0.8.0.20250703.2020`。
- 该镜像同时携带 `deep_thought.yaml` 和 `kag_thinker.yaml`，进一步证明本地实际运行时也把
  两者作为并列配置交付。
- 本地 `kag_thinker.yaml` 缺少当前 `KAGModelPlanner` 构造所需的 `rewrite_prompt`；这是当前
  UI 初始化错误的版本内配置一致性问题，不是两条管线血缘关系的证据。

补充官方历史：v0.8.0 tag 中的 `KAGModelPlanner` 构造函数尚不要求 `rewrite_prompt`，因此
当时的 `kag_thinker.yaml` 与代码是相符的。此后提交
[`e1012d3`](https://github.com/OpenSPG/KAG/commit/e1012d39e41900bb9b0d0b01fbd1a2fdd409ee37)
（[PR #640](https://github.com/OpenSPG/KAG/pull/640)）给 Planner 增加了该参数，而模板没有同步；
当前镜像呈现的是“较新 Planner 合同 + 较旧模板形状”。这是对官方源码差异和本地运行时的
比对结论；官方发布说明没有单独将其公告为 bug。

## 核查范围

仅使用 OpenSPG/KAG 官方 GitHub 仓库、提交历史、正式发布说明、官方 KAG-Thinker 仓库和
当前官方 `reason-server` 镜像内源码。未采用第三方文章或社区二手解释。

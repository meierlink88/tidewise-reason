# 投研推理 DAG

## 目标

对同一个冻结的 Graphiti 上下文，用固定的多阶段推理链分析产业链及节点在短、中、长周期的升温、降温或分化趋势。执行器可替换，但上下文、DAG 步骤、结果合同和校验规则不变。

## 固定步骤

1. `Context Assembly`：按决策时点召回 48 小时内 Event，读取有效 Fact / Signal Fact，使用 Graphiti 原生混合检索，然后加载真实产业链成员和拓扑。
2. `Propagation`：最多三轮传导。第一轮必须引用已知 Fact，后续轮必须引用已接受的上一轮传导。
3. `Aggregation`：对每个真实产业链节点生成短、中、长期趋势、投资判断、理由和风险。
4. `Review`：检查证据覆盖、投资证据完整性、时间边界和过度外推，决定 `SUCCEEDED` 或 `NEEDS_REVIEW`。

## 硬校验

- 只接受冻结 Context 中存在的产业链、节点和拓扑边。
- 不允许 LLM 创造新节点、新边或无证据传导。
- 每个真实节点必须有结果；没有足够证据时显式返回 `INSUFFICIENT_EVIDENCE`。
- 节点在某个周期没有直接 Fact 或同周期已接受 Transmission 时，公共 Pipeline 必须把该周期结论归一化为 `INSUFFICIENT_EVIDENCE`。
- 单个边或节点的 LLM 调用失败只能局部降级，不得使整个 DAG 失败；只记录阶段与异常类型。
- 对比必须使用相同 `context_fingerprint`。稳定性按节点×周期计算，“升温”与“降温”互为实质矛盾。

## 执行器

- `RecordedInvestmentReasoner`：将 Codex 产生的结构化中间结果回放到同一 Pipeline，由 Pipeline 做真实拓扑和证据校验。
- `GraphitiLLMInvestmentReasoner`：使用 Reasoning Server 已配置的 Graphiti `llm_client`（当前为 DeepSeek）。为避免全局大上下文不稳定，传导和节点聚合均按产业链 Map，然后做确定性 Reduce；Pipeline 仍对每条边和每个节点做白名单校验。

## CLI

```bash
python -m reasoning.investment.cli build-context request.json context.json
python -m reasoning.investment.cli run-recorded context.json codex-payload.json codex-result.json
python -m reasoning.investment.cli run-deepseek context.json deepseek-result.json
python -m reasoning.investment.cli replay-result context.json prior-result.json normalized-result.json
python -m reasoning.investment.cli review-result context.json normalized-result.json reviewed-result.json
python -m reasoning.investment.cli compare codex-result.json deepseek-result.json comparison.json
```

CLI 和未来 API 入口必须复用 `InvestmentReasoningPipeline`，不得另建一套推理编排。

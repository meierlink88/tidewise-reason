# OpenSPG + KAG 0.8 中 Schema 的作用与使用环节

## 结论

OpenSPG Schema 是知识图谱的 TBox（知识模型），不是事实数据本身，也不是一条完整的数据清洗流水线。它定义领域中允许出现的实体、概念、事件、属性、关系、约束、索引和可编程规则，并在知识构建与查询推理两个阶段被重复使用。

Schema 的主要价值是把来源各异的事实映射到一套稳定语义，使 KAG 可以用类型、属性和关系进行图检索及逻辑形式求解，而不只依赖文本向量相似度。

## 生命周期

| 环节 | Schema 的实际作用 |
| --- | --- |
| 1. 领域建模 | 定义 EntityType、ConceptType、EventType，以及属性、关系、约束、索引与规则。通过 `knext schema commit` 提交到 OpenSPG。 |
| 2. 结构化数据构建 | `SPGTypeMapping` 从 OpenSPG 加载 Schema，确认目标类型和属性存在，把输入字段组装成节点与边；默认链路为 `Mapping -> (Vectorizer) -> Writer`。 |
| 3. 非结构化知识抽取 | Schema-constrained extractor 从项目 Schema 获得实体、事件、属性和关系边界，以此约束 LLM 的实体识别、属性/事件抽取；Schema-free 模式则不要求全部知识都落入业务类型。 |
| 4. 索引构建 | 属性的索引声明决定哪些字段生成 dense/sparse vector；图节点、关系、原文 Chunk 等可形成互相引用的多层索引。 |
| 5. 检索与推理 | KAG 的部分 NER、逻辑形式解析和图检索组件读取 reason schema，用合法的实体类型、属性、关系重写和执行 SPO 查询；KAG 0.8 也会按知识库已有索引类型选择相应 retriever。 |
| 6. 规则求值 | OpenSPG 可在 Schema 的属性或关系上定义规则，查询时计算派生属性/关系；产业链示例还用 concept rule 的 Action 创建下游事件节点和因果边。 |

## Schema 不等于数据清洗

Schema 能提供：字段映射、类型边界、非法类型过滤、属性/关系结构约束、索引策略，以及对 LLM 抽取的输出空间约束。

Schema 不能自动完成：PostgreSQL CDC、水位线、去重黄金记录、稳定实体 ID、跨源冲突裁决、事实置信度、版本/墓碑、来源追踪和全量对账。这些仍应由 Tidewise 的数据治理与同步层负责。KAG 的实体标准化和 postprocessor 可以辅助别名归一、相似实体链接及无效节点过滤，但不能替代完整的数据质量系统。

## 对当前 Tidewise Schema 的判断

当前 `schemas/Tidewise.schema` 主要定义 16 个领域实体类型及类型描述，尚未加入业务属性、实体间关系、正式 EventType、索引策略和可执行规则。因此当前阶段的直接收益主要是：

- 统一 Company、Security、Industry、IndustryChain、Commodity 等类型边界；
- 为后续 schema-constrained 抽取提供候选类型和领域语义；
- 为 PostgreSQL ABox 投影准备稳定目标类型。

它目前还不能单独支撑“事件影响哪条产业链”“某事件如何传导到企业/证券”等多跳图检索与因果推理。要获得这部分价值，下一阶段至少需要补齐：

1. EventType 及时间、状态、来源、置信度、观察/预测性质；
2. Event 到主体、地点、商品、产业链节点、行业、企业和证券的关系；
3. 产业链节点间的投入、产出、替代、依赖和瓶颈关系；
4. 事实、规则推导和 LLM 假设的明确分层；
5. 对关键属性的文本/向量索引声明，以及经验证的规则。

## 关键边界

KAG Solver 默认是读取图谱与索引来回答问题，不会因为一次问答就自动把 LLM 的推测当成事实写回图谱。需要长期跟踪的“推导事件”应由显式规则或受控 Workflow 生成，带 `derived` 状态、证据、规则版本和置信度，再通过 Writer/API 注册为新 Event；不能直接把自由生成答案写成事实。

## 官方依据

- [KAG v0.8 README：Builder、Solver 与 schema-constrained knowledge construction](https://github.com/OpenSPG/KAG/tree/v0.8.0)
- [KAG v0.8 发布说明：索引构建与检索的配置化管理](https://openspg.github.io/v2/blog/recent_posts/release_notes/0.8)
- [默认 Builder 链：structured 与 unstructured](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/default_chain.py)
- [SPGTypeMapping：加载 Schema 并校验/映射类型属性](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/mapping/spg_type_mapping.py)
- [SchemaConstraintExtractor：按项目 Schema 抽取实体、事件和关系](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/extractor/schema_constraint_extractor.py)
- [BatchVectorizer：读取 Schema 的属性索引类型](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/vectorizer/batch_vectorizer.py)
- [QuestionNER：推理问答时读取 reason schema](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/prompt/question_ner.py)
- [产业链 Schema：类型、派生属性和关系规则](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema)
- [产业链 concept rules：创建推导事件及因果边](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/concept.rule)

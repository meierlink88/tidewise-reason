# OpenSPG KGDSL 概念核验

核验时间：2026-08-09

## 一句话结论

KGDSL（Knowledge Graph Domain Specific Language）是 OpenSPG 的确定性符号规则/图计算语言：用图模式指定要找哪些事实，用条件与计算表达式判断何时成立，再返回结果或创建推导出的节点、关系和属性。

它不是自然语言 Prompt，也不是让 LLM 自由判断的规则；OpenSPG 会解析 KGDSL、结合 SPG Schema 做语义检查，生成逻辑执行计划，再由 Reasoner 对图数据执行。

## 三个核心部分

- `GraphStructure` / `Structure`：匹配图中的节点、关系和路径，相当于规则的事实前提。
- `Rule` / `Constraint`：布尔判断、数值计算、聚合或 UDF，相当于规则条件。
- `Action`：返回属性，或显式创建节点、边等推导结果。

`Define (s)-[p]->(o)` 还可以把规则绑定到一个逻辑属性、逻辑关系或概念分类上。OpenSPG 的模型源码明确说明：属性值可以通过 KGDSL 动态计算，关系是否存在也可以通过 KGDSL 计算。

## 与 Cypher、KAG 的区别

- Cypher：面向 Neo4j/LPG 的通用查询与写入语言。
- KGDSL：面向 SPG Schema 和领域语义的规则语言，表达“什么图模式和条件推出什么语义属性/关系”，由 OpenSPG Reasoner 规划执行。
- KAG Solver：LLM 驱动的问题分解与混合求解框架，可选择检索、Cypher、数学、语言推理等执行器。KGDSL 是可供系统使用的确定性符号规则能力，但不等于 KAG 的整个推理流程。

## 是否自动触发

仅保存规则不等于每次事实写入后自动运行。源码暴露 `/public/v1/reason/run`，调用方提交 `projectId`、`dsl` 和参数来运行 Reasoner。规则也可绑定为 Schema 中的逻辑属性/关系，在相关语义计算时使用。若要做到“新事件到达就执行一组规则”，仍需要 ingest/job/agent 等调用方触发 Reasoner；KGDSL 本身不是事件总线或规则调度器。

## 对观潮家的含义

它适合编码可验证、可复现的投研领域规律，例如：匹配“龙头公司—属于—某行业”和“该公司—发生—长时间停产”事实，在产能占比超过阈值时，推出“该事件可能导致该行业供给收缩”这一语义关系。规则只能根据已入图且字段完备的事实工作；结论置信度、时效、反证和市场预期差仍需在领域模型中显式设计。

## 官方来源

- OpenSPG 对 KGDSL 的官方能力说明：<https://github.com/OpenSPG/openspg#core-capabilities>
- KGDSL 的 ANTLR 官方语法：<https://github.com/OpenSPG/openspg/blob/master/reasoner/kgdsl-parser/src/main/antlr4/com/antgroup/openspg/reasoner/KGDSL.g4>
- KGDSL 官方解析器：<https://github.com/OpenSPG/openspg/blob/master/reasoner/kgdsl-parser/src/main/scala/com/antgroup/openspg/reasoner/parser/OpenSPGDslParser.scala>
- LogicalPlanner 明确为 KGDSL/GQL 生成逻辑计划：<https://github.com/OpenSPG/openspg/blob/master/reasoner/lube-logical/src/main/scala/com/antgroup/openspg/reasoner/lube/logical/planning/LogicalPlanner.scala>
- `Property` 源码说明 KGDSL 可动态计算逻辑属性：<https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/predicate/Property.java>
- `Relation` 源码说明 KGDSL 可计算关系是否存在：<https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/predicate/Relation.java>
- Reasoner HTTP 入口与显式 DSL 请求：<https://github.com/OpenSPG/openspg/blob/master/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/ReasonController.java>

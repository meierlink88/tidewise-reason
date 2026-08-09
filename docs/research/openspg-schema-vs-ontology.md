# OpenSPG：SPG Schema 与 Ontology 的关系

核验日期：2026-08-09。仅使用 OpenSPG 官方仓库、源码与 release notes。

## 结论

**SPG Schema 与本体（ontology）高度相似，但不能直接等同于标准的 OWL Ontology。**

- 从知识建模作用看，SPG Schema 就是 OpenSPG 的领域本体/语义模型：定义领域中有哪些类型、属性、关系、继承、谓词语义、约束和逻辑规则，用来指导知识图谱的构建与推理。
- 从技术实现看，它是 OpenSPG 自己的 **SPG 元模型与 DSL**，目标是把 RDF 的语义能力与 LPG（属性图）的工程结构结合起来。官方明确称 SPG “integrates LPG structural and RDF semantic”，并把它与 RDF/OWL 的复杂性区别开，因此不能把一份 SPG Schema 当作一份标准 OWL 文件或假设二者具有相同语义和工具兼容性。[OpenSPG README](https://github.com/OpenSPG/openspg#spg-background)
- OpenSPG 源码内部确实把 Schema 元素统称为 ontology models：`BaseOntology` 是所有 ontology models 的父类；其注释说明 ontology 用来指导领域实体、术语和概念的认知建模，并“define the schema of knowledge graph”。所以在 **OpenSPG 自身术语**里，Schema 是 ontology 的工程化表达与集合，而不是与 ontology 完全无关的数据库表结构。[BaseOntology.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/BaseOntology.java)

## 相似点与差异

| 维度 | SPG Schema | 传统 OWL/RDF Ontology |
|---|---|---|
| 目的 | 定义共享领域语言，约束知识构建，支撑推理 | 定义类、属性、公理和可推导语义 |
| 类型体系 | EntityType、ConceptType、EventType、StandardType、IndexType 等，并支持继承 | Class、Datatype、Object/Data Property 等 |
| 谓词 | Property、Relation、SubProperty，并可声明 transitive、symmetric 等语义 | RDF/OWL property、公理与 property characteristics |
| 约束 | OpenSPG 自有 constraint：非空、多值、正则、枚举、范围、唯一 | OWL 公理偏开放世界推理；数据约束通常另用 SHACL/ShEx |
| 规则 | Property/Relation 可绑定 KGDSL `LogicalRule` | 通常由 OWL reasoner、SWRL、SHACL Rules 或外部规则引擎处理 |
| 存储与执行取向 | 面向 LPG、Builder、Graph Store 和工程化知识加工 | 面向 RDF triples、IRI、标准序列化和 SPARQL/OWL 工具链 |
| 是否等价 | **不是 OWL 的同义词**；是 OpenSPG 自有的语义增强属性图 Schema | W3C 语义网标准体系 |

上述判断可由源码结构直接确认：`SPGSchema` 是一组被修改的 `BaseSPGType`；`ProjectSchema` 是项目内定义的全部 SPG types；`BaseSPGType` 则定义类型的父类型、属性、关系及高级配置。[SPGSchema.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/SPGSchema.java) [ProjectSchema.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/type/ProjectSchema.java) [BaseSPGType.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/type/BaseSPGType.java)

## Schema 中各部分如何作用于知识实例

### 1. 类型是知识实例的模板

`BaseSPGType` 将主体类型分成 EntityType、ConceptType、EventType、IndexType，另有 BasicType 和 StandardType 可作为对象类型。类型可有父类型，并继承父类型的属性和关系。[BaseSPGType.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/type/BaseSPGType.java) [SPGTypeEnum.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/type/SPGTypeEnum.java)

知识实例不是无类型的自由节点：

- `EntityRecord` 持有一个 `EntityType`；
- `EventRecord` 持有一个 `EventType`；
- `ConceptRecord` 持有一个 `ConceptType`；
- `RelationRecord` 持有一个 Schema 中定义的 `Relation`。

也就是说，Schema 描述“公司/政策事件/行业概念/影响关系是什么”，Record 才是“宁德时代/某次政策事件/动力电池板块/具体影响事实”。[EntityRecord.java](https://github.com/OpenSPG/openspg/blob/master/builder/model/src/main/java/com/antgroup/openspg/builder/model/record/EntityRecord.java) [EventRecord.java](https://github.com/OpenSPG/openspg/blob/master/builder/model/src/main/java/com/antgroup/openspg/builder/model/record/EventRecord.java) [ConceptRecord.java](https://github.com/OpenSPG/openspg/blob/master/builder/model/src/main/java/com/antgroup/openspg/builder/model/record/ConceptRecord.java) [RelationRecord.java](https://github.com/OpenSPG/openspg/blob/master/builder/model/src/main/java/com/antgroup/openspg/builder/model/record/RelationRecord.java)

### 2. Property/Relation 决定事实的合法结构

`Property` 定义 subject type、object type、约束、子属性和高级语义；当 object 是语义类型时，Property 也可以表达关系。`Relation` 是特殊 Property，用于两个对象之间的连接，并可声明传递性、对称性或绑定 KGDSL 计算逻辑。[Property.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/predicate/Property.java) [Relation.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/predicate/Relation.java)

因此，Schema 不只是 Explorer 中的说明文档，而是 Builder 把来源字段转换成 SPG Record 时使用的目标结构。`SPGTypeMappingHelper` 会先按配置加载目标 `BaseSPGType`，再把来源字段映射到 Schema 的 property/relation，并生成带类型的 vertex/edge records。[SPGTypeMappingHelper.java](https://github.com/OpenSPG/openspg/blob/master/builder/core/src/main/java/com/antgroup/openspg/builder/core/physical/process/SPGTypeMappingHelper.java)

### 3. 约束会在知识导入时实际生效

OpenSPG 的 `Constraint` 源码注释非常明确：约束作用在 Property 上，知识导入时检查属性值；**只有满足约束的属性值才写入存储**。支持的约束包括 `NOT_NULL`、`MULTI_VALUE`、`REGULAR`、`ENUM`、`RANGE`、`UNIQUE`。[Constraint.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/constraint/Constraint.java) [ConstraintTypeEnum.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/constraint/ConstraintTypeEnum.java)

这比“导入后只展示 ontology”更强：SPG Schema 的约束位于事实加工/入库路径中。但应注意源码的表述是“只写入符合条件的属性值”，并不等于整个实体或整条来源事实一定被整体拒绝；具体失败、过滤或部分写入行为仍取决于 Builder 处理节点和配置。

### 4. 规则从既有实例推导逻辑属性或关系

`PropertyAdvancedConfig` 可同时挂载 constraint、predicate semantics 和 `LogicalRule`；`LogicalRule.content` 保存 KGDSL，由规则引擎使用。`Property`/`Relation` 的源码注释说明，逻辑属性值或逻辑关系可以由 KGDSL 动态计算，而不是在知识加工时直接导入。[PropertyAdvancedConfig.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/predicate/PropertyAdvancedConfig.java) [LogicalRule.java](https://github.com/OpenSPG/openspg/blob/master/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/semantic/LogicalRule.java)

因此三者分工是：

```text
Schema Type/Property/Relation  定义允许表达什么
Constraint                    决定导入值是否符合要求
KGDSL LogicalRule             基于已有事实计算/推导新的属性或关系
Record                        具体的实体、事件、概念和关系实例
```

### 5. Schema 可以直接约束抽取与对齐

OpenSPG v0.6 官方 release notes 明确提供 `schema-constraint` 抽取链接模式：知识库构建阶段“严格按照 Schema 的定义”进行更细粒度、复杂的知识抽取；同一版本也增加默认知识对齐组件，包括无效数据过滤和相似实体链指。[OpenSPG v0.6 release](https://github.com/OpenSPG/openspg/releases/tag/v0.6)

KAG 官方说明也将流程概括为：原始业务数据经过知识抽取、属性标准化和语义对齐进入统一图谱，并同时支持 schema-free 抽取和 schema-constrained 专业知识构建。[KAG README](https://github.com/OpenSPG/KAG#21-knowledge-representation)

## 对 Tidewise 的直接含义

如果采用 OpenSPG，SPG Schema 应被当成 **运行时会参与构建与推理的领域语义模型**，而不是旁路维护的 ontology 文件：

```text
A股领域 SPG Schema
  ├─ 类型：ListedCompany / Sector / PolicyEvent / SupplyEvent
  ├─ 属性与关系：affects / belongsTo / consumes / benefits
  ├─ 约束：代码唯一、事件时间非空、影响方向枚举
  └─ KGDSL 规则：由事件与敞口事实推导 CostPressure/Beneficiary
                         ↓
来源数据 → Schema-constrained 抽取/字段映射/实体链接 → 约束过滤 → SPG Records → 规则推理
```

最准确的定义是：

> **SPG Schema 是 OpenSPG 自有、面向属性图工程落地的 ontology/schema 体系。它承担传统本体的领域语言与推理语义职责，同时承担数据库 Schema 的类型、字段、约束和入库控制职责；它与 OWL Ontology 概念相近，但格式、语义体系和执行机制并不等价。**

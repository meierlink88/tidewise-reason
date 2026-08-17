# OpenSPG TBox Schema DSL 调研

> 调研日期：2026-08-09  
> 适用基线：OpenSPG / KAG `v0.8.0`  
> 目的：为「观潮家」人工导入 OpenSPG 的 `.schema` 文件提供可核对的语法与安全边界。本文不修改或提交运行中的 Schema。

## 结论摘要

1. OpenSPG 使用自己的声明式 Schema DSL，语法类似 YAML，但不是 YAML。它逐行解析，依靠缩进识别层级。
2. 文件必须先声明 `namespace Tidewise`；本 namespace 下的类型在提交时会被补全为 `Tidewise.TypeName`。
3. 主要类型是 `EntityType`、`ConceptType`、`EventType`；子类通过 `Child(中文名) -> Parent:` 声明。
4. 类型可以定义 `properties` 和 `relations`。属性可指向基本类型、标准类型或已定义的业务类型；关系必须指向图中类型，不能指向 `STD.*`。
5. `id`、`name`、`description` 是内建属性，不应在业务 Schema 里重复声明。官方 KAG 示例中的 `desc(描述): Text` 是另一个用于检索的业务字段，不是内建 `description`。
6. `EventType` 必须定义 `subject`，且 subject 必须指向 Entity/Concept 类型，不能是 `Text`、`Integer`、`Float` 等基本类型。
7. 人工导入前必须把文件当成「完整目标 Schema」审查，不能当成只新增几个类型的 patch。KAG 0.8 的同步实现会对比服务端，并删除文件中缺失的同 namespace 类型、属性和关系。

## 核心语法

### 1. Namespace 与顺序

```text
namespace Tidewise
```

- 官方文档要求 `namespace` 出现在文件第一行。
- 0.8 解析器的 namespace 只接受英文字母和数字：`[a-zA-Z0-9]+`。
- 类型使用前应先定义。尤其是继承，父类必须出现在子类之前。KAG 0.8 解析器会预扫描普通类型名，某些属性引用可能侥幸通过前向引用，但官方文档仍明确要求按顺序定义，建议严格遵守。

### 2. 类型声明

```text
Company(公司): EntityType

Industry(行业分类): ConceptType
    hypernymPredicate: isA

CompanyEvent(公司事件): EventType
    properties:
        subject(主体): Company

ListedCompany(上市公司) -> Company:
```

类型通用格式：

```text
EnglishName(中文名): EntityType|ConceptType|EventType
ChildName(中文名) -> ParentName:
```

0.8 解析器还识别 `IndexType`、`StandardType`、`BasicType`，但观潮家的第一版业务 TBox 不需要自定义这三类底层类型。

### 3. 属性、关系和子属性

```text
Company(公司): EntityType
    desc: 上市公司及其基本信息
    properties:
        stockCode(证券代码): Text
            constraint: NotNull
            index: Text
        industry(所属行业): Industry
    relations:
        supplier(供应商): Company
            properties:
                confidence(置信度): Float
```

- 类型元信息位于第二层：`desc`、`properties`、`relations`。
- 属性/关系位于第三层：`englishName(中文名): ObjectType`。
- 属性的元信息可包括 `desc`、`constraint`、`index`、`properties`、`rule`。
- 关系的元信息可包括 `desc`、`properties`、`rule`；关系的子属性应使用基本类型。
- 官方页面说属性英文名要以小写字母开头，且只使用英文字母和数字。为了与 Java/Python/KAG 消费端一致，建议一律使用 `lowerCamelCase`。

### 4. 属性类型

官方 DSL 页面列出的标量类型：

- 基本类型：`Text`、`Integer`、`Float`
- 标准类型：`STD.ChinaMobile`、`STD.Email`、`STD.IdCardNo`、`STD.MacAddress`、`STD.Date`、`STD.ChinaTelCode`、`STD.Timestamp`

同一官方页面的完整示例和 KAG 0.8 解析器还明确支持以已定义的 Entity/Concept 类型作为属性对象，例如 `industry(行业): Industry`。因此，页面中「属性类型只支持以下几种」应理解为标量值类型列表，不是禁止业务类型引用。

### 5. 约束

```text
constraint: NotNull
constraint: MultiValue
constraint: NotNull, MultiValue
constraint: Enum="positive,neutral,negative"
constraint: Regular="^[0-9]{6}$"
```

0.8 解析器支持四类约束：

- `NotNull`
- `MultiValue`
- `Enum="A,B,C"`
- `Regular="..."`

`Enum` 和 `Regular` 必须使用双引号包围参数。

### 6. 检索索引（官方 0.8 源码扩展）

```text
abstract(摘要): Text
    index: TextAndVector
```

KAG 0.8 解析器及官方示例支持：

- `Text`
- `Vector`
- `SparseVector`
- `TextAndVector`
- `TextAndSparseVector`

用户给定的 Yuque DSL 页面没有讲解 `index`，但它是 KAG 0.8 解析器和官方 Schema 示例实际使用的语法。是否创建 `Vector` 类索取决于已配置的 embedding 模型与索引后端；第一版 TBox 可以先少用，避免把模型问题和 Schema 问题混在一次导入中。

### 7. ConceptType

```text
Industry(行业分类): ConceptType
    hypernymPredicate: isA
```

- `hypernymPredicate` 仅适用于 `ConceptType`。
- 0.8 解析器接受 `isA`、`locateAt`、`mannerOf`；Yuque 页面的文案只提到前两个，因此 `mannerOf` 属于已在源码实现、但页面文档未完整列出的能力。
- `autoRelate: ConceptA, ConceptB` 可为概念类型自动创建官方语义谓词关系。第一版观潮家 TBox 建议不使用 `autoRelate`，因为它会一次生成较多关系，增大人工审核范围。
- 概念语义关系的名称使用分类前缀，例如 `IND#belongTo`、`CAU#leadTo`；解析器还定义了 `SYNANT`、`SEQ`、`INC`、`USE` 等组。

### 8. EventType

```text
MarketEvent(市场事件): EventType
    properties:
        subject(主体): ListedCompany
        eventTime(发生时间): STD.Timestamp
```

- 官方页面要求 EventType 定义 `subject`。
- 解析器会把名为 `subject` 的属性标记为 `SUBJECT` 组，并拒绝基本/标准标量类型作为事件主体。
- EntityType 的关系不能指向 EventType；EventType 可以指向 EntityType。这体现了 OpenSPG 「动态事件指向静态实体」的方向约束。

### 9. 谓词逻辑规则

```text
risk(风险关联): Company
    rule: [[
        Define (s:Company)-[p:risk]->(o:Company) {
            ...
        }
    ]]
```

- 多行规则使用 `[[` 和 `]]` 定界。
- `rule` 可以绑定到属性或关系。
- 观潮家当前阶段只建 TBox，建议先不写业务推理规则；等类型和谓词稳定后，再单独 review KGDSL 规则。

## 缩进规则

DSL 最多有六层语义缩进：

1. 无缩进：namespace 或类型
2. 类型元信息：`desc` / `properties` / `relations` 等
3. 属性或关系
4. 属性/关系元信息
5. 子属性
6. 子属性元信息

建议每层固定使用 4 个空格，不要使用 Tab。解析器虽会把 Tab 转为 2 个空格，但官方示例里本身存在 Tab/空格混用，非常容易在人工编辑后产生错层。解析器关心相邻层级缩进变化，并会对无法对齐的回退层级报错。

## 人工导入前的安全检查

### 这不是增量 patch

KAG 0.8 的 `schema commit` 会：

1. 读取本地 `$namespace.schema`；
2. 解析为目标类型集合；
3. 与服务端 Schema 做 diff；
4. 对差异执行创建、更新或删除；
5. 提交 session。

具体而言，同一 namespace 中：

- 服务端存在、但文件里不存在的类型，会被标记删除。
- 类型里已有、但文件里遗漏的非内建属性/关系，会被标记删除。
- 已被继承的类型，某些属性/关系变更会被禁止。
- 类型种类、父类、ConceptType 的 `hypernymPredicate` 不能就地修改；源码要求删除后重建。
- EventType 的 subject 属性不能被删除。

因此，导入前应依次：

1. 从目标项目导出当前完整 Schema 作为基线。
2. 在基线上合并观潮家 TBox，不要用一份只包含「新类型」的短文件覆盖提交。
3. 先执行 diff/preview，确认没有意外的 `Delete type/property/relation`。
4. 再由人工在 OpenSPG 中提交。

## 一个可导入的最小结构示例

```text
namespace Tidewise

Industry(行业): ConceptType
    hypernymPredicate: isA

Company(公司): EntityType
    desc: 公司主体
    properties:
        stockCode(证券代码): Text
            constraint: NotNull
            index: Text
        industry(所属行业): Industry

MarketEvent(市场事件): EventType
    desc: 会影响公司或行业的事件
    properties:
        subject(主体): Company
        eventTime(发生时间): STD.Timestamp
        abstract(事件摘要): Text
            index: Text
```

这只是语法示例，不是观潮家最终领域模型，也不应直接覆盖已有项目 Schema。

## 官方一手来源

- [OpenSPG 用户手册：声明式 schema](https://openspg.yuque.com/ndx6g9/docs/fghnz04etmg0g6ug)  
  语法关键字、缩进层级、基本/标准类型、约束、Entity/Concept/Event 示例。页面正文发布于 2025-06-28，页面元数据显示 2026-05-29 有更新。
- [OpenSPG/KAG v0.8.0：Schema DSL 解析器](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/schema/marklang/schema_ml.py)  
  用于核对 namespace/类型/谓词正则、层级解析、Concept/Event 限制、约束、索引枚举，以及 diff-and-sync 的删除/更新行为。
- [OpenSPG/KAG v0.8.0：`schema commit` 命令](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/command/sub_command/schema.py)  
  用于核对默认 Schema 文件路径、解析器调用和 `sync_schema()` 提交流程。
- [OpenSPG/KAG v0.8.0：SupplyChain 官方 Schema 示例](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema)  
  用于核对供应链领域的 ConceptType、EntityType、EventType、`subject`、`IND#belongTo`、`CAU#leadTo` 和 KGDSL 规则。
- [OpenSPG/KAG v0.8.0：BaiKe 官方 Schema 示例](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/baike/schema/BaiKe.schema)  
  用于核对 `index: Text` / `index: TextAndVector` 以及带 subject 的 EventType 实际写法。

## 文档与 0.8 实现的差异记录

| 主题 | Yuque 页面 | KAG 0.8 源码/示例 | 建议 |
|---|---|---|---|
| 属性类型 | 列出 Basic/STD 标量类型 | 同页面示例与解析器支持业务类型引用 | 允许指向已定义 Entity/Concept，同时保守控制关系方向 |
| `hypernymPredicate` | 文案提到 `isA`、`locateAt` | 解析器另接受 `mannerOf` | 首版仅使用文档化程度最高的 `isA` |
| `index` | 页面未讲解 | 解析器和大量官方示例在用 | 可用，但首次导入尽量少配 Vector |
| 定义顺序 | 要求引用类型先定义 | 解析器会预加载普通类型，但父类仍要先解析 | 统一采用「先定义，后引用」 |
| 缩进 | 建议 4 空格，Tab 视为 2 空格 | 官方示例中存在混合缩进 | 观潮家文件禁止 Tab，固定每层 4 空格 |

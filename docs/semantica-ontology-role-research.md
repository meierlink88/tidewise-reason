# Semantica Ontology 的实际作用

## 结论

Semantica 的 Ontology 模块主要作用于 **Knowledge Graph 的 schema / 元模型**，不是 Event 的事实提取过程本身。

官方 Ontology Management Guide 展示的主路径是：

```text
已有 Knowledge Graph
  -> OntologyGenerator 归纳 classes / object properties / datatype properties / hierarchy
  -> validate_ontology() 校验 ontology 自身的结构
  -> 导出 OWL / Turtle / JSON-LD
  -> 交给 SHACL、外部 reasoner 或需要标准 schema 的下游系统
```

## 运行边界

- `OntologyGenerator.generate_from_graph()` 从 KG 中已经存在的实体类型与关系归纳 ontology；它不参与前面的 NER / relation extraction。
- `validate_ontology(ontology)` 校验生成的 ontology 是否结构有效，返回 errors / warnings；它不是事实真假校验。
- 指南允许人工修正推断出的父类、增量加入 class/property，再导出。
- 名称不一致不会被自动改名或合并。若 KG 同时使用 `ThreatActor` 与 `Threat_Actor`，需要在数据规范化、映射/对齐或人工维护中处理。
- Ontology 导出后可以作为 SHACL graph validation、外部 OWL reasoning、STIX/TAXII 等工具链的机器可读契约。指南明确说明 OWL 推理由 HermiT、Pellet、ELK 等外部工具执行，Semantica 在此负责导出 ontology。

## 对当前 Event Demo 的含义

如果目标只是体验一个真实 Event 的实体/关系提取和 KG 构建，Ontology 不是必需的第一步。只有当存在跨来源的稳定 schema、长期 KG 一致性、SHACL 约束、外部推理或标准化交换需求时，构建 Ontology 才产生明确价值。

## 官方来源

- [Ontology Management Guide](https://docs.getsemantica.ai/guides/ontology/)
- [Ontology Module Reference](https://docs.getsemantica.ai/reference/ontology/)
- [Semantic Extract Module](https://docs.getsemantica.ai/reference/semantic_extract/)

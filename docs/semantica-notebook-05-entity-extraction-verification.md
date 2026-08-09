# Semantica Notebook 05：Entity Extraction 与 Ontology 的关系

核对对象：

- <https://github.com/semantica-agi/semantica/blob/main/cookbook/introduction/05_Entity_Extraction.ipynb>
- <https://github.com/semantica-agi/semantica/blob/main/semantica/semantic_extract/ner_extractor.py>
- <https://github.com/semantica-agi/semantica/blob/main/semantica/semantic_extract/named_entity_recognizer.py>

## 结论

Notebook 05 讲的是从文本中生成候选实体，不包含 Ontology 的加载、查询、类映射、URI 对齐或约束校验。它没有展示 Ontology 自动参与实体提取。

## 提取方法

- `NERExtractor`：输出实体文本、类型、位置、置信度和 metadata。
- 方法：pattern、regex、ML/spaCy、Hugging Face、LLM。
- `NamedEntityRecognizer`：配置方法、置信度阈值、重叠合并和标准类型。
- `EntityClassifier`：归一少量内置标签，例如 `ORG` 与 `ORGANIZATION`。
- `EntityConfidenceScorer`：评分和过滤。
- `CustomEntityDetector`：使用自定义正则提取领域实体。
- 支持批量处理。

## 与 Ontology 的间接接点

当前源码允许调用方传入 `entity_types`，也允许定义 custom patterns。因此应用可以把 Ontology 中选定的类名显式转换为 `entity_types` 或领域模式，以影响候选实体的类型关注范围和评分。但这是调用方建立的桥接，不是 Notebook 所展示的 Ontology 内置联动。

`EntityClassifier` 的标签归一也不等于 Ontology 对齐：它只归并预设标签别名，并不会把结果映射到某个 Ontology 的规范类 URI。

完整的 Ontology-first 流程仍需显式增加：

1. 从 Ontology 选择允许或关注的类；
2. 将其投影到 `entity_types`、自定义模式或 LLM 输出 schema；
3. 执行 NER，产生候选实体；
4. 将候选标签映射到 Ontology 规范类/URI；
5. 再进行关系抽取、入图和约束校验。


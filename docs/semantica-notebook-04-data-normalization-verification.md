# Semantica Notebook 04：Data Normalization 与 Ontology 的关系

核对对象：

- <https://github.com/semantica-agi/semantica/blob/main/cookbook/introduction/04_Data_Normalization.ipynb>
- <https://github.com/semantica-agi/semantica/blob/main/semantica/normalize/entity_normalizer.py>
- <https://github.com/semantica-agi/semantica/blob/main/semantica/normalize/text_normalizer.py>
- <https://github.com/semantica-agi/semantica/blob/main/semantica/normalize/data_cleaner.py>

## 结论

Notebook 04 展示的是格式层和实例名称层的数据标准化，不包含 Ontology 的加载、类/属性 URI 映射、SHACL 校验或 Ontology 驱动的规范化。

它覆盖：文本的 Unicode、空白、大小写和特殊字符；实体名称格式和别名；日期格式；数字、百分比和货币符号；记录去重、字段 schema 校验、缺失值；语言与编码检测。

## EntityNormalizer 的规则来源

`EntityNormalizer.normalize_entity()` 依次执行字符串清理、按实体类型处理格式、查询 `AliasResolver`、处理名称格式。`AliasResolver` 的规范名映射来自调用者通过 `alias_map` 显式传入的字典，默认为空。当前实现不会自行读取 Ontology，也不会自动把 Notebook 中的 `Apple Inc.`、`Apple`、`Apple Incorporated` 合并成同一个实例。

这里的 `entity_type="Organization"` 只是一个方法参数；它不是 Ontology class URI，也不触发 Ontology 查询或校验。

## “schema” 不是 Ontology

`DataCleaner` 可以接收字段 validation schema，检查必填字段和 Python 数据类型。该 schema 是记录结构规则，不是 OWL/SHACL Ontology。

## 在完整流程中的位置

对于自由文本事件：

1. 先进行文本/日期/数字等表面格式标准化；
2. 进行 NER，生成候选实体；
3. 对候选实体名称做别名与实例规范名归并；
4. 再显式映射到 Ontology 的类、属性与规范 URI；
5. 关系抽取、入图和 Ontology/SHACL 校验。

如果事件本来就是结构化记录，且字段已经表示实体名称，则 EntityNormalizer 也可以在 NER 前直接作用于这些字段。

Ontology 中的 `label`、`altLabel` 或实例标识可以由应用转换成 `alias_map`，但这是调用方建立的桥接，不是 Notebook 展示的内置联动。

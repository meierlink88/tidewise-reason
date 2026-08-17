# OpenSPG property description API

## 结论

OpenSPG 后端 Schema 模型支持属性描述：属性的 `basicInfo.desc` 会通过
`POST /schema/alterSchema` 提交。当前 UI 未保存属性描述，不代表服务端不支持。

安全做法是使用 KAG `SchemaClient`：读取现有类型，仅修改目标属性的 `desc`，
将属性标记为 `UPDATE`，再提交类型更新。

不要把仅包含一个 EntityType 的短 `.schema` 文件直接执行 `knext schema commit`；
该命令按完整目标 Schema 做差异同步，可能删除同 namespace 中未出现在文件里的类型、
属性或关系。

## 当前实例核验

- 项目 ID：`1`
- 类型：`Tidewise.AllianceOrganization`
- 四个业务属性均已存在，但属性描述当前为空字符串。
- 已在内存中验证更新载荷可携带 `basicInfo.desc`，未向服务端提交任何修改。

## 官方源码依据

- [`BasicInfo.desc`](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/schema/rest/models/basic_info.py)
- [`/schema/alterSchema`](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/schema/rest/schema_api.py)
- [`SchemaClient` 更新与提交](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/schema/client.py)
- [Schema MarkLang 差异同步](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/schema/marklang/schema_ml.py)

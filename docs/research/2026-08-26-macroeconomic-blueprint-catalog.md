# MacroEconomic 首批初始化候选目录

> 调研日期：2026-08-26  
> 目标：为面向中国股票投研的 `MacroEconomic` 准备一批可持续接收 Event 的宏观叙事蓝图。  
> 来源边界：仅使用央行、财政部、统计局、贸易主管机关、IMF、WTO 等官方一手来源。官方来源证明主题的制度或数据基础，不代表 Tidewise 采纳相关机构的政策判断。  
> 实施边界：本文件只给出候选数据，不写 PG、不写 Graphiti、不分配 `MEC...` ID。

## 结论

建议先由用户审阅以下 **20 个 `ACTIVE` 候选蓝图**，覆盖 6 个对中国股票市场具有关键传导作用的经济中心：

| 经济中心 | 数量 | 入选依据 |
|---|---:|---|
| 中国 | 5 | A 股盈利、信用、估值、地产链和外贸的直接宏观环境 |
| 美国 | 5 | 美元流动性、全球无风险利率、经济数据、对华贸易和先进技术约束 |
| 日本 | 3 | 日元套息与亚洲流动性，以及半导体、材料和设备产业政策 |
| 欧盟/欧元区 | 3 | 中国重要贸易市场、统一货币政策、贸易救济和碳边境监管 |
| 韩国 | 2 | 中国重要贸易伙伴及全球存储芯片、显示和电子制造周期领先样本 |
| 印度 | 2 | 大型增长经济体，以及制造业投资与供应链迁移的重要承接市场 |

欧盟/欧元区应作为政策主体处理，而不是分别为德国、法国等成员国复制货币与贸易蓝图。韩国虽不是最大的总量经济体，但其半导体出口周期对中国 AI、存储、设备和电子制造链具有较高信息价值。印度的意义主要是需求增量和供应链承接，不应把每一项印度产业补贴都建立为独立蓝图。

## 与 ontology 的对齐

本仓库 `MacroEconomic` 允许的业务字段为 `name`、`name_en`、`macro_type`、`description`、`status`、`data_object_id` 和 `updated_at`。首批 Demo 建议统一：

- `status = ACTIVE`；它只表示该叙事蓝图仍可接收 Event，不表示当前信号方向为正。
- `data_object_id = null`、`updated_at = null`；未来正式值必须来自 Data Service，不能在 Reasoning Server 发明。
- `macro_type` 只选择仓库枚举：`MONETARY`、`FISCAL`、`TRADE_POLICY`、`REGULATORY`、`DATA_ECONOMIC`。
- 下文的“定义”即建议写入 `description` 的内容；来源和“对中国投研关键性”不属于当前 Pydantic 实体字段，不应混写进 `description`。
- `MacroEconomic` 当前没有 Country/Region 边，因此国家名称写进蓝图名称与定义用于划定边界，但初始化不应暗中创建未声明关系。

## 推荐候选数据

### 中国

#### 1. 中国货币政策与信用周期

- `name_en`: `China Monetary Policy and Credit Cycle`
- `macro_type`: `MONETARY`
- 定义：人民银行通过政策利率、存款准备金、公开市场操作、再贷款及其他结构性工具影响人民币流动性、社会融资、银行信用和融资成本的长期政策与传导框架。单次降准、降息或工具额度调整属于该蓝图下的 Event。
- 对中国投研关键：直接影响 A 股估值折现率、银行与非银负债成本、地产与基建融资、科技和绿色产业的结构性信贷可得性。
- 官方依据：[中国人民银行货币政策工具说明](https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125437/4634692/4634697/5412489/index.html)、[中国人民银行现代货币政策框架](https://www.pbc.gov.cn/en/3935690/3935759/2025080817513075572/2021021018411552829.pdf)

#### 2. 中国积极财政、政府债务与基建投资

- `name_en`: `China Fiscal Expansion, Government Debt and Infrastructure Investment`
- `macro_type`: `FISCAL`
- 定义：中央和地方财政支出、国债与地方专项债发行、转移支付、债务置换及政府投资共同形成的逆周期财政与债务管理框架。年度预算数字或某批债券发行属于 Event/Observation，不是新蓝图。
- 对中国投研关键：决定基建、建筑材料、公共事业、设备投资和地方财政相关需求，同时影响利率供给、城投和银行资产质量预期。
- 官方依据：[中国财政部财政政策执行报告目录](https://www.mof.gov.cn/en/reports/)、[2025 年财政政策执行报告](https://www.mof.gov.cn/en/reports/202605/t20260520_3990222.htm)

#### 3. 中国房地产政策与地产信用修复

- `name_en`: `China Property Policy and Real-Estate Credit Repair`
- `macro_type`: `REGULATORY`
- 定义：围绕住房信贷、首付与利率、项目融资白名单、保交房、库存消化、保障房收储和房地产发展模式调整形成的持续政策框架。某城市限购调整或一次住房信贷参数变化属于 Event。
- 对中国投研关键：房地产通过居民资产负债表、地方财政、银行信贷以及建材、家居、工程机械等链条广泛影响 A 股风险偏好与盈利预期。
- 官方依据：[人民银行住房贷款首付政策](https://www.pbc.gov.cn/en/3688253/3689009/4180845/2025112115005182356/index.html)、[国务院关于稳定房地产市场的官方信息](https://english.www.gov.cn/news/202503/09/content_WS67cd9f43c6d0868f4e8f0a66.html)

#### 4. 中国内需、价格与库存周期

- `name_en`: `China Domestic Demand, Price and Inventory Cycle`
- `macro_type`: `DATA_ECONOMIC`
- 定义：由消费、固定资产投资、工业生产、产成品库存、CPI、PPI 与 PMI 等连续宏观数据共同刻画的中国需求—价格—生产循环。每月数据发布是 Observation/Event，蓝图本身不预设扩张或收缩方向。
- 对中国投研关键：是判断企业收入、利润率、补库存和行业景气扩散的基础宏观锚点，可承接消费、周期品和制造业的方向性信号。
- 官方依据：[国家统计局年度国民经济发布](https://www.stats.gov.cn/english/PressRelease/202601/t20260119_1962328.html)、[国家统计局最新数据发布目录](https://www.stats.gov.cn/english/PressRelease/index_7.html)

#### 5. 中国外贸与出口景气周期

- `name_en`: `China Foreign Trade and Export Cycle`
- `macro_type`: `DATA_ECONOMIC`
- 定义：由进出口总量、主要商品量价、贸易伙伴和贸易方式变化共同刻画的中国外需与供应链景气循环。月度出口增速、单一商品或国别数据属于 Observation/Event，蓝图不预设上行或下行。
- 对中国投研关键：直接影响电子、机械、汽车、轻工、化工、航运港口和人民币供求，也是海外需求 Event 能否传导至国内产业链的重要验证锚点。
- 官方依据：[中国海关统计入口](https://english.customs.gov.cn/Statistics/Statistics)、[中国海关国别/地区贸易数据](https://english.customs.gov.cn/Statics/2af25ac9-0058-451e-88e7-db2ebb40eacf.html)

### 美国

#### 6. 美联储货币政策与美元金融条件

- `name_en`: `Federal Reserve Policy and U.S. Dollar Financial Conditions`
- `macro_type`: `MONETARY`
- 定义：美联储围绕就业与价格稳定目标，通过联邦基金利率、资产负债表和流动性工具影响美元利率、信用条件及全球美元流动性的持续政策框架。某次 FOMC 决议属于 Event。
- 对中国投研关键：影响人民币汇率压力、外资风险偏好、港股与 A 股估值、美元融资成本以及全球大宗商品定价。
- 官方依据：[美联储货币政策目标与传导](https://www.federalreserve.gov/monetarypolicy/monetary-policy-what-are-its-goals-how-does-it-work.htm)、[FOMC 长期目标与政策战略](https://www.federalreserve.gov/monetarypolicy/files/FOMC_LongerRunGoals.pdf)

#### 7. 美国通胀、就业与需求周期

- `name_en`: `United States Inflation, Labor and Demand Cycle`
- `macro_type`: `DATA_ECONOMIC`
- 定义：由美国通胀、就业、工资、消费和生产数据共同刻画的价格压力、劳动力需求与经济景气循环。单次 CPI、非农就业或零售数据属于 Observation/Event，蓝图本身不保存某期读数。
- 对中国投研关键：这些数据决定美联储路径和美元利率预期，也影响中国出口需求、全球科技资本开支、大宗商品和风险偏好。
- 官方依据：[美国劳工统计局 CPI](https://www.bls.gov/cpi/)、[美国劳工统计局就业形势](https://www.bls.gov/news.release/empsit.toc.htm)

#### 8. 美国财政赤字、国债供给与全球流动性

- `name_en`: `U.S. Fiscal Deficit, Treasury Supply and Global Liquidity`
- `macro_type`: `FISCAL`
- 定义：美国财政收支、联邦融资需求、国债期限结构和季度再融资安排共同作用于美债供给、期限溢价和市场流动性的长期财政—融资框架。债务上限事件或单次再融资公告属于 Event。
- 对中国投研关键：美债收益率是全球估值基准；国债供给和期限溢价变化会传导至美元、黄金、成长股估值和跨境资本流动。
- 官方依据：[美国财政部季度再融资机制](https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding/)、[美国财政部国内金融与债务管理职责](https://home.treasury.gov/policy-issues/financial-markets-financial-institutions-and-fiscal-service)

#### 9. 美国对华关税与贸易限制

- `name_en`: `United States Tariffs and Trade Restrictions on China`
- `macro_type`: `TRADE_POLICY`
- 定义：美国通过 Section 301 等贸易政策工具，对中国商品设置、调整或豁免关税并推动进口来源替代的持续政策框架。具体产品税率调整、调查启动或豁免延期属于 Event。
- 对中国投研关键：直接改变中国出口价格、订单与产能布局，并影响新能源、机械、消费电子、航运和替代供应链相关板块。
- 官方依据：[USTR Section 301 四年评估](https://ustr.gov/sites/default/files/05.14.2024%20Four%20Year%20Review%20of%20China%20Tech%20Transfer%20Section%20301%20%28Final%29.pdf)、[USTR 关税行动说明](https://ustr.gov/about-us/policy-offices/press-office/press-releases/2024/september/ustr-finalizes-action-china-tariffs-following-statutory-four-year-review)

#### 10. 美国对华先进计算与半导体出口管制

- `name_en`: `United States Advanced Computing and Semiconductor Export Controls on China`
- `macro_type`: `REGULATORY`
- 定义：美国出口管理规则对面向中国的先进计算芯片、半导体制造设备、相关最终用途和美国人员支持设置许可及限制的持续监管框架。规则修订、实体清单调整或许可证政策变化属于 Event。
- 对中国投研关键：直接影响中国 AI 算力、晶圆制造、设备、材料、先进封装和国产替代的供给约束与投资节奏。
- 官方依据：[美国商务部 BIS 对华先进计算与半导体管制专题](https://www.bis.gov/press-release/bis-updated-public-information-page-export-controls-imposed-advanced-computing-semiconductor)、[BIS 规则背景材料](https://www.bis.gov/media/1381)

### 日本

#### 11. 日本银行政策正常化与日元金融条件

- `name_en`: `Bank of Japan Policy Normalization and Yen Financial Conditions`
- `macro_type`: `MONETARY`
- 定义：日本银行围绕价格稳定目标，通过短期政策利率、国债购买和市场操作调整金融条件的长期框架，包含从非常规宽松向常规利率工具演变的政策周期。单次利率或购债决定属于 Event。
- 对中国投研关键：日元利率和汇率会影响全球套息交易、亚洲资金流、人民币相对汇率，以及中日汽车、机械、材料和出口企业的竞争条件。
- 官方依据：[日本银行货币政策框架](https://www.boj.or.jp/en/mopo/outline/)、[日本银行货币政策资料入口](https://www.boj.or.jp/en/mopo/index.htm)

#### 12. 日本工资、物价与内需循环

- `name_en`: `Japan Wage, Price and Domestic Demand Cycle`
- `macro_type`: `DATA_ECONOMIC`
- 定义：工资增长、服务与商品价格、居民实际收入、消费和企业定价行为共同构成的日本工资—物价—内需循环。春斗结果、月度工资或 CPI 数据属于 Observation/Event，蓝图不预设循环方向。
- 对中国投研关键：影响日本货币政策的持续性、日元方向、中国赴日消费，并改变中日制造业在价格、工资和出口上的相对竞争力。
- 官方依据：[日本银行价格稳定目标与政策传导](https://www.boj.or.jp/en/mopo/outline/)、[日本银行关于工资伴随下实现价格目标的说明](https://www.boj.or.jp/en/about/press/koen_2022/data/ko221226a1.pdf)

#### 13. 日本战略产业财政与产业支持

- `name_en`: `Japan Strategic-Industry Fiscal and Industrial Support`
- `macro_type`: `FISCAL`
- 定义：日本通过预算、补贴、政策融资和研发支持，强化半导体、AI、绿色转型及供应链韧性的中长期产业财政框架。单个项目拨款、企业补助或工厂审批属于 Event。
- 对中国投研关键：日本在半导体设备、材料、汽车和精密制造领域具有关键地位，政策投入会改变中国相关产业链的供给、竞争和合作格局。
- 官方依据：[日本财务省预算资料](https://www.mof.go.jp/english/policy/budget/budget/)、[日本经产省未来半导体战略](https://www.meti.go.jp/english/policy/0704_001.pdf)

### 欧盟与欧元区

#### 14. 欧洲央行政策与欧元区金融条件

- `name_en`: `ECB Policy and Euro-Area Financial Conditions`
- `macro_type`: `MONETARY`
- 定义：欧洲央行围绕中期价格稳定目标，通过关键利率、资产负债表和流动性工具影响欧元区融资、需求与欧元汇率的统一货币政策框架。单次管委会决议属于 Event。
- 对中国投研关键：欧盟是中国重要出口市场，欧元区需求、欧元汇率和融资条件会传导至中国机械、汽车、光伏、消费品和航运链。
- 官方依据：[欧洲央行 2% 价格稳定目标](https://www.ecb.europa.eu/mopo/strategy/pricestab/html/index.en.html)、[欧洲央行货币政策概览](https://www.ecb.europa.eu/mopo/html/index.en.html)

#### 15. 欧盟对华贸易救济与产业竞争政策

- `name_en`: `European Union Trade Defence and Industrial Competition Policy toward China`
- `macro_type`: `TRADE_POLICY`
- 定义：欧盟针对中国商品运用反补贴、反倾销、保障措施及其他贸易防御工具，并围绕关键产业竞争条件调整市场准入的持续政策框架。针对某一产品的立案、临时税或终裁属于 Event。
- 对中国投研关键：直接影响中国新能源汽车、光伏、钢铁、化工及装备企业的欧洲销量、价格和海外产能配置。
- 官方依据：[欧盟委员会对中国电动汽车反补贴措施](https://ec.europa.eu/commission/presscorner/api/files/document/print/en/ip_24_3630/IP_24_3630_EN.pdf)、[欧盟贸易与中国制造业专题分析](https://ec.europa.eu/economy_finance/forecasts/2024/spring/spring_forecast-2024_special%20issue_china_en.pdf)

#### 16. 欧盟碳边境与绿色产业监管

- `name_en`: `European Union Carbon Border and Green-Industry Regulation`
- `macro_type`: `REGULATORY`
- 定义：欧盟通过碳边境调节机制及配套排放核算、申报和碳价规则，使特定进口商品承担嵌入排放成本的长期监管框架。覆盖范围、默认值、证书价格或实施细则变化属于 Event。
- 对中国投研关键：影响中国钢铁、铝、水泥、化肥、氢能及后续可能扩展行业的出口成本、绿电需求与碳核算投资。
- 官方依据：[欧盟委员会 CBAM 官方说明](https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en?prefLang=pl)、[CBAM 覆盖行业](https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-sectors_en)

### 韩国

#### 17. 韩国货币政策、韩元与金融稳定

- `name_en`: `Korea Monetary Policy, Won and Financial Stability`
- `macro_type`: `MONETARY`
- 定义：韩国银行在中期通胀目标下，通过基准利率、流动性操作并兼顾汇率、家庭债务和资产价格风险来调整金融条件的持续政策框架。单次利率决议属于 Event。
- 对中国投研关键：韩元与韩国利率是亚洲出口与科技周期的重要金融变量，也会影响中韩制造业竞争、外资区域配置和人民币相对汇率。
- 官方依据：[韩国银行通胀目标框架](https://www.bok.or.kr/eng/main/contents.do?menuNo=400015)、[韩国银行货币政策一般原则](https://www.bok.or.kr/eng/main/contents.do?menuNo=400001)

#### 18. 韩国半导体出口与制造业周期

- `name_en`: `Korea Semiconductor Exports and Manufacturing Cycle`
- `macro_type`: `DATA_ECONOMIC`
- 定义：由存储及其他半导体价格、出口、产量、资本开支和贸易条件共同刻画的韩国电子制造景气周期。月度出口、库存或价格数据是 Observation/Event，蓝图不等同于某一轮 AI 行情。
- 对中国投研关键：韩国是全球存储芯片和电子制造重镇，其周期可为中国 HBM、DRAM/NAND、封装、设备、材料和消费电子需求提供领先或交叉验证信号。
- 官方依据：[韩国银行半导体上行周期及宏观传导研究](https://www.bok.or.kr/eng/bbs/B0000354/view.do?depth=400409&menuNo=400409&nttId=11063486&programType=newsDataEng&relate=Y)、[韩国银行关于新经济产业竞争力的研究](https://www.bok.or.kr/eng/bbs/E0000828/view.do?menuNo=400207&nttId=10070267)

### 印度

#### 19. 印度货币政策与内需增长周期

- `name_en`: `India Monetary Policy and Domestic-Demand Growth Cycle`
- `macro_type`: `MONETARY`
- 定义：印度储备银行在灵活通胀目标框架下，以回购利率和流动性管理影响价格、信用和内需，同时兼顾增长的持续政策与传导周期。MPC 单次决定或通胀目标修订属于 Event。
- 对中国投研关键：印度是大型需求增量市场，其利率、通胀与内需影响中国机械、电子、化工、新能源和消费品企业的出口机会与区域竞争。
- 官方依据：[印度储备银行货币政策框架](https://systemhealth.rbi.org.in/Scripts/FS_Overview2752.aspx.html)、[印度储备银行对灵活通胀目标的说明](https://www.rbi.org.in/commonperson/English/Scripts/speeches.aspx?Id=3161)

#### 20. 印度制造业激励与供应链承接

- `name_en`: `India Manufacturing Incentives and Supply-Chain Reallocation`
- `macro_type`: `FISCAL`
- 定义：印度通过生产挂钩激励、预算支持和产业基础设施政策吸引电子、汽车、电池、光伏等制造业投资并提升本地产能的中长期政策框架。某行业额度、企业获批或项目投产属于 Event。
- 对中国投研关键：该框架既创造中国设备、零部件和资本品需求，也构成电子、汽车、新能源等行业产能迁移与出口替代风险。
- 官方依据：[印度预算中制造业 PLI 支持](https://www.indiabudget.gov.in/budget2025-26/doc/eb/allsbe.pdf)、[印度经济调查关于制造业转型与 PLI](https://www.indiabudget.gov.in/economicsurvey/doc/eschapter/echap08.pdf)

## 建议暂不初始化的候选

| 候选 | 暂不初始化原因 | 建议归属 |
|---|---|---|
| 全球经济增长 | 范围过宽，容易把不同国家的相反周期压成一个节点 | 后续用 IMF 数据做全局检索过滤器，或单独建全球 `DATA_ECONOMIC` 二期蓝图 |
| 全球贸易周期 | 有价值，但一期可先由美国、欧盟、韩国、中国各自蓝图验证传导 | 二期使用 WTO 贸易量数据建立跨区域蓝图 |
| ASEAN 宏观政策 | ASEAN 没有统一央行或财政政策，成员经济结构差异大 | 按越南、印尼等国家在二期分别建立 |
| 美元走强、人民币贬值 | 是宏观变量的方向性状态，不是稳定叙事蓝图 | `Variable + Signal Fact` |
| 中国降准 50bp | 是一次现实政策动作 | Event，归入“中国货币政策与信用周期” |
| 日本央行本月加息 | 是一次政策动作 | Event，归入“日本银行政策正常化与日元金融条件” |
| 韩国半导体出口同比上升 | 是一条 Observation/Event | 归入“韩国半导体出口与制造业周期”并派生 Signal |

## 上图前门禁

1. 先由用户审阅 20 个候选的边界和命名，再制作初始化 catalog；本文件不是可直接执行的 seed。
2. 首批 Demo 不写 PG、不设置 `data_object_id`；正式 `MEC...` ID 只能由 Data Service 产生。
3. 不把官方来源 URL、投研意义或推断结论塞进 `description`；这些应保存在初始化 catalog 的 provenance 或研究文档中。
4. `MacroEconomic` 是分类/叙事锚点，不进入 Event 原生 `add_episode()` 的开放实体提取范围。Event 对蓝图的归属应由后续宏观分类和信号提炼工序受控建立。
5. 不把 `MacroEconomic` 当前状态与市场方向混淆：蓝图保持稳定，升温、降温、宽松、收紧等方向由 Event 派生的 Variable 与 Signal Fact 表达。
6. 对中国投研关键性的文字是基于官方制度、贸易和产业结构信息作出的研究推断；它是候选优先级依据，不是官方机构结论。

## 跨经济体选择依据

- 中国海关公开的国别/地区贸易数据覆盖美国、欧盟、日本、韩国和印度，显示这些经济体均是中国对外贸易和供应链分析中的直接对象：[中国海关国别/地区贸易数据](https://english.customs.gov.cn/Statics/2af25ac9-0058-451e-88e7-db2ebb40eacf.html)。
- IMF 的世界经济展望把中国、美国、欧元区、日本和印度作为主要经济体单列，并将贸易政策和金融条件列为全球增长的重要扰动来源：[IMF World Economic Outlook](https://www.imf.org/en/publications/weo/issues/2025/04/22/world-economic-outlook-april-2025)。
- WTO 的贸易画像按经济体提供主要出口、进口和贸易伙伴，可作为后续核验蓝图覆盖范围与优先级的官方统一入口：[WTO Trade Profiles](https://www.wto.org/english/res_e/statis_e/trade_profiles_list_e.htm)。

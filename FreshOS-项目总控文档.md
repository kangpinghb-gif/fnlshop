# FreshOS 项目总控文档

更新时间：2026-05-27

本文件是 FreshOS 项目的统一入口，用于把产品总纲、V1 实施计划、数据库与导入设计、当前开发进度合并到同一个工作上下文。原始文档继续保留，本文件负责承接后续讨论、开发和交接。

工具实际使用方式详见：

```text
FreshOS-V1工具使用方式与业务操作流程.md
```

## 一、项目定位

FreshOS 是生鲜 AI 经营操作系统，目标是让生鲜门店从“经验经营”升级为“系统经营”。

系统长期目标：

- 自动订货
- 库存预测
- 动态控损
- 自动出清
- 动态定价
- 门店协同运营
- 经营经验沉淀和 AI 学习

生鲜经营的核心矛盾是：

```text
断货成本 vs 损耗成本
```

系统的核心任务是在两者之间动态平衡。

## 二、核心理念

### 1. 不相信 ERP 库存

ERP 库存不等于实际库存。FreshOS 必须建立三层库存体系：

- ERP / 大表哥原始库存
- 理论库存
- 修正后主库存

库存主口径优先级：

```text
实时库存快照 > 期末库存 > 理论库存
```

人工盘点只作为修正值，不直接替代主库存。

### 2. V1 不以复杂 AI 为核心

第一阶段先跑通：

- 数据闭环
- 规则引擎
- 库存口径
- 订货建议
- 风险提醒

复杂 AI、动态定价、员工任务、供应商评分放到后续版本。

### 3. 生鲜核心是库存控制

销量预测重要，但不是 V1 的唯一核心。系统必须关注：

- 库存年龄
- 动销速度
- 损耗风险
- 商品生命周期
- 可售天数

### 4. 必须允许人工干预

V1 必须允许采购、店长或运营人员修改建议，并记录修改原因和执行结果。生鲜经营存在临时天气、活动、客流和本地经验，系统不能假设自动建议永远正确。

## 三、版本路线

| 版本 | 目标 | 范围 |
| --- | --- | --- |
| V1 | 跑通多门店库存经营闭环 | 数据同步、库存修正、订货建议、风险提醒 |
| V2 | 增强预测 | 天气、节假日、基础预测因子 |
| V3 | 控损执行 | 动态出清、动态调价、员工任务 |
| V4 | 经营优化 | AI 学习、多门店调拨、供应商评分 |
| V5 | 最终形态 | AI 生鲜经营操作系统 |

当前阶段聚焦 V1。

## 四、V1 形态

V1 不优先做完整 Web 后台，先做云端自动订货助手。

```text
云服务器 freshos-worker
  ↓
Hermes 定时执行
  ↓
自动抓取/导入大表哥和订单数据
  ↓
FreshOS 计算订货建议和库存风险
  ↓
生成 Excel/CSV 明细
  ↓
企业微信/飞书推送摘要和附件
```

职责划分：

| 模块 | 职责 |
| --- | --- |
| Hermes | 定时调度和执行任务 |
| freshos-worker | 抓取、导入、清洗、匹配、计算、生成文件、推送 |
| PostgreSQL | 存储基础数据、导入数据、计算结果、任务日志 |
| 企业微信/飞书 | 推送每日结果、异常提醒、附件 |
| Excel/CSV | 承载订货建议、库存风险、导入异常明细 |

## 五、V1 最小闭环

```text
抓取或导入基础数据
  ↓
抓取或导入销售 / 库存 / 到货 / 盘点修正
  ↓
匹配门店和商品
  ↓
计算库存口径
  ↓
计算销量预测
  ↓
生成订货建议
  ↓
输出库存风险
  ↓
生成明细文件
  ↓
企业微信 / 飞书推送
```

V1 验收标准：

- 能获取门店、商品、门店商品关系。
- 能获取最近 30 天销售数据。
- 能获取库存、损耗、订货 / 收货数据。
- 能导入订单到货数据。
- 能导入人工盘点修正。
- 能生成门店商品维度的订货建议。
- 能提示负库存、缺货、积压、临期、过期、数据缺失等风险。
- 能生成每日订货建议和库存风险明细。
- 能通过企业微信或飞书推送每日结果。

## 六、V1 工具使用方式

V1 第一阶段不是页面工具，而是阿里云服务器上的自动订货助手。

日常使用入口：

- Hermes 自动导出大表哥 40/42 数据并触发 freshos-worker。
- systemd timer 仅作为阿里云服务器兜底调度方式。
- 企业微信 / 飞书查看摘要和附件。
- 服务器报表目录查看 CSV / Excel。
- 服务器命令行用于补跑任务和排查异常。

业务流程：

```text
Hermes 自动导出大表哥 40/42 数据
  ↓
freshos-worker 导入订单 / 盘点 / Hermes 导出文件
  ↓
系统生成订货建议和库存风险
  ↓
采购 / 店长查看报表
  ↓
人工确认或调整订货
  ↓
运营 / 督导处理库存风险
  ↓
系统维护人员处理导入异常
```

## 七、试点范围

建议 V1 第一阶段控制范围：

- 3 到 5 家门店。
- 门店商品结构相似。
- 使用同一套 ERP / POS / 大表哥数据源。
- 先选 1 到 3 个生鲜品类，例如叶菜、水果、鲜奶、肉禽、水产。
- 暂不覆盖全部商品。

大表哥当前筛选口径：

```text
大分类编码 = 40,42
40 = 现制加工品
42 = 日配生鲜
```

## 八、数据来源

### 1. 大表哥

V1 历史经营数据主来源，用于提供：

- 门店基础数据
- 商品基础数据
- 商品分类
- 门店商品关系
- 销售历史
- 库存数据
- 报损数量 / 金额
- 订货 / 收货汇总
- 商品订货参数

### 2. 生鲜订单 Excel

用于补充：

- 到货日期
- 当日到货值
- 订单商品名称
- 发货数量 / 净果数量 / 门店实收重量

入库数量优先级：

```text
门店实收重量
  ↓
净果数量
  ↓
发货数量
  ↓
供货量
  ↓
订货数量
```

### 3. 人工盘点修正

人工盘点不作为主要库存值，只作为修正值，用于：

- 修正实时库存或理论库存
- 提升 / 降低库存可信度
- 记录异常库存纠偏

## 九、核心数据表

V1 已落成 PostgreSQL schema 草案，核心表包括：

| 表 | 用途 |
| --- | --- |
| `stores` | 门店基础信息 |
| `products` | 商品主档 |
| `store_products` | 门店商品经营关系和订货参数 |
| `sales_daily` | 门店商品每日销售 |
| `inventory_snapshots` | 实时库存或库存时点快照 |
| `inventory_loss_daily` | 库存、损耗、盘盈盘亏日汇总 |
| `purchase_receipts_daily` | 订货、收货、退货日汇总 |
| `fresh_order_imports` | 生鲜订单 Excel 导入明细 |
| `stock_count_adjustments` | 人工盘点修正 |
| `import_exceptions` | 导入异常 |
| `inventory_positions` | 修正后库存口径 |
| `inventory_age_batches` | V1 计算批次和库存年龄 |
| `sales_forecasts` | 销量预测 |
| `order_suggestions` | 订货建议 |
| `inventory_risks` | 库存风险 |
| `job_runs` | 任务运行日志 |

关键唯一约束：

- `stores.store_code`
- `products.product_code`
- `store_products(store_id, product_id)`
- `sales_daily(store_id, product_id, business_date)`
- `fresh_order_imports(source_file_name, source_sheet_name, raw_row_number)`
- `inventory_positions(store_id, product_id, business_date)`
- `order_suggestions(store_id, product_id, suggestion_date, arrival_date)`

## 十、匹配规则

门店匹配：

```text
优先 store_name，其次 store_code
```

商品匹配：

```text
优先 product_code，其次订单商品名称
```

订单商品名称匹配时清洗前缀：

- `C-`
- `Z-`
- `JPZ-`
- `R-`

无法匹配的数据写入 `import_exceptions`。

常见异常类型：

- `unmatched_store`
- `store_code_name_conflict`
- `unmatched_product`
- `missing_product_code`
- `missing_arrival_date`
- `missing_arrival_quantity`
- `quantity_greater_than_order`
- `negative_inventory`
- `unit_conflict`

## 十一、计算逻辑

### 1. 库存口径

```text
理论库存 = 昨日库存 + 入库 - 销售 - 预计损耗
```

主库存优先级：

```text
实时库存快照 > 期末库存 > 理论库存
```

人工盘点修正叠加到主库存，生成 `corrected_inventory_qty`。

### 2. 库存年龄

V1 使用“计算批次”，不代表真实物理批次：

```text
同一门店 + 同一商品 + 同一到货日期 = 一个计算批次
```

到货日期在 V1 中视为生产日期等价口径。

```text
expiry_date = arrival_date + sellable_days
```

批次状态：

- `sellable`
- `near_expiry`
- `expired`

### 3. 销量预测

V1 默认规则：

1. 最近 7 天有效销售日均销量。
2. 不足 3 天时，使用最近 14 天有效销售日均销量。
3. 仍不足时，使用 `store_products.recent_daily_sales`。
4. 仍无数据时，预测为 0，并写风险提示。

### 4. 订货建议

基础公式：

```text
建议订货量 = 预测销量 + 安全库存 - 修正库存
```

V1 需要支持：

- 安全库存天数
- 已订 / 已发未到
- 可卖库存
- 积压库存
- MOQ / 订货批量圆整
- 最小订货量
- 可解释的 `suggestion_reason`

## 十二、报表与推送

V1 先输出文件，不先做页面。

每日文件：

- `订货建议明细.xlsx`
- `库存风险明细.xlsx`
- `导入异常明细.xlsx`

订货建议明细至少包含：

- 门店
- 商品
- 当前库存
- 预测销量
- 安全库存
- 已订未到
- 建议订货量
- 订货原因
- 风险标记

库存风险明细至少包含：

- 门店
- 商品
- 风险类型
- 风险等级
- 风险说明
- 相关数量
- 处理状态

企业微信 / 飞书推送先支持 webhook：

- 每日摘要
- 高风险清单摘要
- 订货建议附件
- 库存风险附件
- 任务失败提醒

## 十三、当前代码状态

项目目录：

```text
freshos-worker/
  config/
  jobs/
  freshos/
  migrations/
  scripts/
  tests/
```

已建立任务入口：

- `fetch_dabiaoge`
- `import_dabiaoge_base`
- `import_dabiaoge_daily`
- `import_orders`
- `match_order_imports`
- `import_stock_adjustments`
- `calculate_inventory`
- `forecast_sales`
- `generate_order_suggestions`
- `generate_inventory_risks`
- `export_reports`
- `notify`
- `run_daily`

已完成：

- worker 项目骨架。
- 数据库 schema 草案。
- job 运行日志机制。
- 订单 Excel 解析。
- `fresh_order_imports` 入库 / CSV 输出。
- 门店和商品匹配回填逻辑。
- 人工盘点修正模板导入，写入 `stock_count_adjustments` 或输出 CSV。
- 大表哥基础数据导入解析和 CSV 输出。
- 大表哥日数据导入解析和 CSV 输出。
- `calculate_inventory` 已接入 `inventory_positions` 数据库计算入口。
- `calculate_inventory` 已接入 `inventory_age_batches` 计算批次 / FIFO 消耗估算。
- `generate_order_suggestions` 已接入 `order_suggestions` 数据库计算入口。
- `generate_inventory_risks` 已接入 `inventory_risks` 数据库计算入口。
- `export_reports` 已接入数据库读取，数据库开启时导出真实订货建议、库存风险和导入异常，数据库关闭时输出空模板。
- `notify` 已接入每日摘要，推送订货、风险、异常和报表路径。
- 已新增最小闭环种子数据和应用脚本，用于 PostgreSQL 集成验证。
- 已新增本地 PostgreSQL 配置模板和一键最小闭环脚本。
- 已新增阿里云 ECS 部署指南、服务器配置模板和 systemd 定时任务模板。
- 基础报表 CSV 输出。
- 核心计算规则单元测试。

当前测试结果：

```text
python3 -m pytest -q
27 passed
```

## 十四、大表哥基础数据导入状态

`import_dabiaoge_base` 当前支持：

- 无表头 DOM CSV。
- 带表头 CSV。
- XLSX / XLSM。
- 表头别名兼容。
- 默认只导入大分类编码 `40/42`。
- 输出 `stores.csv`、`products.csv`、`store_products.csv`。
- 多输入文件合并时按门店、商品、门店商品关系去重。

已支持的别名示例：

- `门店编号` / `店铺编号`
- `门店名称` / `店铺名称`
- `大类编码` / `大分类编码`
- `产品编码` / `商品编码`
- `品名` / `商品名称`
- `保质期` / `保质期限(天)`

当前 DOM 样本：

- 文件：`data_samples/dabiaoge_stores_products_base_dom.csv`
- 100 行均为大分类 `01`
- 默认 `40/42` 过滤后输出 0 行，这是正常结果，不是解析失败。

## 十五、大表哥日数据导入状态

`import_dabiaoge_daily` 当前支持：

- 带表头 CSV。
- XLSX / XLSM。
- 表头别名兼容。
- 缺少日期字段时使用 `--business-date`。
- 同一门店、商品、日期的重复行先合并为日汇总。

当前支持的 `--report-type`：

| report-type | 目标表 | 说明 |
| --- | --- | --- |
| `sales` | `sales_daily` | 销售数量、销售金额 |
| `inventory_loss` | `inventory_loss_daily` | 期末库存、报损、盘盈盘亏 |
| `purchase_receipts` | `purchase_receipts_daily` | 订货、收货、退货 / 调出 |
| `inventory_snapshot` | `inventory_snapshots` | 实时库存快照 |
 
日汇总合并规则：

- 销售数量、销售金额：求和。
- 报损数量、报损金额、盘盈盘亏数量：求和。
- 订货、收货、总收货、总退货 / 调出：求和。
- 期末库存、实时库存：保留后出现的值。

## 十六、当前限制

还没有接入真实 PostgreSQL，因此以下能力虽然已有代码，但未做真实连库验证：

- `fresh_order_imports` 入库
- `job_runs` 任务日志
- `match_order_imports` 数据库回填
- `import_exceptions` 写入
- `stores` / `products` / `store_products` upsert
- `inventory_positions` 计算落库
- `order_suggestions` 计算落库
- `inventory_risks` 计算落库

还没有正式大表哥 `40/42` 导出数据，因此以下能力尚未用真实数据验证：

- 门店基础数据导入
- 商品基础数据导入
- 门店商品关系导入
- 销售日汇总导入
- 库存 / 损耗导入
- 订货 / 收货导入

## 十七、下一步优先级

### P0：阿里云 ECS 部署准备

目标部署环境是阿里云服务器。

部署文档：

```text
freshos-worker/deploy/ALIYUN_ECS_DEPLOY.md
```

服务器配置模板：

```text
freshos-worker/config/settings.aliyun.example.toml
```

systemd 模板：

```text
freshos-worker/deploy/systemd/freshos-worker.service
freshos-worker/deploy/systemd/freshos-worker.timer
```

安全原则：

- PostgreSQL 默认只监听 `127.0.0.1`。
- 阿里云安全组不开放 `5432`。
- SSH 只允许可信公网 IP。
- `/etc/freshos/settings.toml` 权限使用 `600`。

### P1：拿到正式大表哥 40/42 基础数据后验证基础导入

命令：

```bash
cd /Users/kangping/Documents/生鲜AI自动订货系统/freshos-worker

python3 -m jobs.import_dabiaoge_base \
  --config config/settings.example.toml \
  --business-date 2026-05-26 \
  --input ../data_samples/正式大表哥40_42基础数据.xlsx \
  --output /private/tmp/freshos_dabiaoge_base_check
```

验证目标：

- `stores.csv` 有门店。
- `products.csv` 有 `40/42` 商品。
- `store_products.csv` 有门店商品关系。
- 商品名称能用于后续订单匹配。

### P2：接入 PostgreSQL 验证 upsert

验证表：

- `stores`
- `products`
- `store_products`
- `fresh_order_imports`
- `import_exceptions`
- `job_runs`
- `inventory_positions`
- `sales_forecasts`
- `order_suggestions`
- `inventory_risks`

可使用内置种子数据先跑最小闭环：

```bash
cd /Users/kangping/Documents/生鲜AI自动订货系统/freshos-worker

cp config/settings.local.example.toml config/settings.toml
python scripts/run_minimal_closure.py --config config/settings.toml --business-date 2026-05-26
```

也可以分步执行：

```bash
python scripts/apply_migrations.py --config config/settings.toml
python scripts/apply_seed_data.py --config config/settings.toml

python -m jobs.calculate_inventory --config config/settings.toml --business-date 2026-05-26
python -m jobs.forecast_sales --config config/settings.toml --business-date 2026-05-26
python -m jobs.generate_order_suggestions --config config/settings.toml --business-date 2026-05-26
python -m jobs.generate_inventory_risks --config config/settings.toml --business-date 2026-05-26
python -m jobs.export_reports --config config/settings.toml --business-date 2026-05-26
```

种子数据文件：

```text
freshos-worker/seeds/001_minimal_closure.sql
```

包含：

- 1 个门店
- 1 个商品
- 1 条门店商品关系
- 14 天销售
- 1 条库存快照
- 1 条损耗记录
- 1 条次日到货记录

### P3：用正式基础数据回测订单匹配

命令：

```bash
python3 -m jobs.import_orders \
  --config config/settings.example.toml \
  --business-date 2026-05-25 \
  --input ../样表/宝信润山店.xlsx \
  --input '../样表/5.25水果订单(2).xlsx'

python3 -m jobs.match_order_imports \
  --config config/settings.example.toml \
  --business-date 2026-05-25
```

验证目标：

- 订单门店能匹配到 `stores`。
- 订单商品能匹配到 `products`。
- 失败项进入 `import_exceptions`。

### P4：继续日数据导入

下一组导入来源：

- 大表哥销售日汇总。
- 大表哥库存 / 损耗。
- 大表哥订货 / 收货。

## 十八、常用命令

进入项目：

```bash
cd /Users/kangping/Documents/生鲜AI自动订货系统/freshos-worker
```

运行测试：

```bash
python3 -m pytest -q
```

运行每日任务链：

```bash
python3 -m jobs.run_daily \
  --config config/settings.example.toml \
  --business-date 2026-05-26
```

解析订单样表：

```bash
python3 -m jobs.import_orders \
  --config config/settings.example.toml \
  --business-date 2026-05-25 \
  --input ../样表/宝信润山店.xlsx \
  --input '../样表/5.25水果订单(2).xlsx' \
  --output /private/tmp/freshos_order_imports.csv
```

导入大表哥基础数据：

```bash
python3 -m jobs.import_dabiaoge_base \
  --config config/settings.example.toml \
  --business-date 2026-05-26 \
  --input ../data_samples/dabiaoge_stores_products_base_dom.csv \
  --output /private/tmp/freshos_dabiaoge_base_check
```

导入大表哥销售日汇总：

```bash
python3 -m jobs.import_dabiaoge_daily \
  --config config/settings.example.toml \
  --business-date 2026-05-26 \
  --report-type sales \
  --input ../data_samples/sales_daily.csv \
  --output /private/tmp/freshos_daily_sales_check.csv
```

## 十九、原始文档索引

- `FreshOS-生鲜AI经营系统总纲.md`
- `FreshOS-V1多门店产品需求与数据表设计.md`
- `FreshOS-V1数据库与导入设计.md`
- `FreshOS-V1开发实施计划.md`
- `FreshOS-V1开发进度与下次继续.md`
- `freshos-worker/README.md`

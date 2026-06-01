# FreshOS V1 / V1.1 开发进度与下次继续

更新时间：2026-06-02

## 一、当前实现方向

V1.1 采用云端自动订货助手形态，核心口径已从“早晨出建议”调整为“每天12:00生成次日订货建议”：

```text
云服务器 freshos-worker
  ↓
Hermes 12:00 自动导出/抓取大表哥 40/42 数据和实时销售数据
  ↓
Hermes 触发 freshos-worker 导入订单 / 盘点 / 大表哥导出文件
  ↓
FreshOS 计算12点趋势修正预测、预计到货前库存、订货建议和库存风险
  ↓
生成 Excel/CSV 明细
  ↓
企业微信/飞书推送摘要和附件
```

第一阶段不优先做完整 Web 后台。当前以 `freshos-worker`、PostgreSQL、Hermes、CSV/XLSX 报表、企业微信/飞书 webhook 组成最小闭环。

## 二、当前状态快照

当前代码已经进入 V1.1：

```text
v1.1
```

当前主线提交：

```text
0329ea5 feat: add v1.1 noon trend ordering
```

当前已完成的闭环能力：

- PostgreSQL schema 草案和迁移脚本。
- Hermes / systemd 可执行任务入口。
- 生鲜订单 Excel 解析、导入、幂等写入。
- 人工盘点修正模板解析和导入。
- 大表哥基础数据导入：
  - `stores`
  - `products`
  - `store_products`
- 大表哥日数据导入：
  - `sales_daily`
  - `inventory_loss_daily`
  - `purchase_receipts_daily`
  - `inventory_snapshots`
  - `sales_cutoff_snapshots`
- 门店 / 商品匹配回填和导入异常记录。
- 库存口径计算：
  - 实时库存快照
  - 期末库存
  - 理论库存
  - 人工盘点修正
- 库存年龄批次计算：
  - 到货批次
  - FIFO 消耗
  - 可售天数
  - 临期 / 过期状态
- 销量预测：
  - 最近7天有效日均
  - 最近14天有效日均
  - 大表哥 recent_daily_sales 回退
  - 12点实时销售趋势修正
- 订货建议：
  - 安全库存
  - 已订未到
  - 最小订货量
  - 订货批量圆整
  - 预计到货前库存
  - 商品名称包含 `折` 或等于 `D系统用代表商品` 时不计入常规订货
- 库存风险：
  - 负库存
  - 缺货
  - 高库存
  - 临期 / 过期
  - 高损耗
- 每日报表导出：
  - 订货建议明细
  - 库存风险明细
  - 导入异常明细
- 企业微信 / 飞书 webhook 推送摘要。
- 阿里云 ECS 部署文档、配置样例和 systemd 文件。

当前开发重点已经从“补齐代码骨架”转为：

```text
云服务器部署 + Hermes 拉齐 v1.1 + 正式大表哥数据验证
```

## 三、最新验证命令

进入项目目录：

```bash
cd /Users/kangping/Documents/生鲜AI自动订货系统/freshos-worker
```

运行测试：

```bash
python3 -m pytest -q
```

当前结果：

```text
36 passed
```

本地无数据库时，仍可用示例配置跑任务链，数据库任务会安全跳过：

```bash
python3 -m jobs.run_daily \
  --config config/settings.example.toml \
  --business-date 2026-05-26
```

生产环境完整任务链使用：

```bash
python3 -m jobs.run_daily \
  --config /etc/freshos/settings.toml \
  --business-date YYYY-MM-DD
```

## 四、当前限制和待验证项

当前代码逻辑已经完成到 V1.1，但仍未用正式线上大表哥数据和真实 PostgreSQL 环境完成端到端验证。

仍待验证：

1. PostgreSQL 生产库迁移是否能在阿里云 ECS 上完整执行。
2. 大表哥 `40/42` 基础导出是否能完整导入：
   - `stores`
   - `products`
   - `store_products`
3. 最近30天销售日汇总是否能稳定导入 `sales_daily`。
4. 历史0-12点实时销售是否能写入 `sales_cutoff_snapshots`，并形成可靠 `historical_noon_ratio`。
5. 今日0-12点销售、12点库存、今日在途数量是否能支持 `expected_inventory_at_arrival`。
6. 生鲜订单 Excel 和大表哥商品主档的商品匹配率是否足够高。
7. 订货建议是否能和人工订货量、次日实际销量做回测对比。
8. 企业微信 / 飞书 webhook 是否能在正式环境推送摘要和报表路径。

当前已知风险：

- 大表哥正式导出字段可能和样本字段不同，需要补字段别名。
- `40/42` 分类口径需要用正式数据确认，避免漏导或误导商品。
- 12点趋势修正依赖历史0-12点销售，如果历史样本不足，会退回基础预测。
- 商品可售天数仍需要按商品属性维护，否则库存年龄和积压判断只能按默认口径估算。
- 损耗率数据暂不稳定，V1.1 损耗补偿和预计今日损耗先按0处理。

## 五、下次继续的第一步

下次优先做：

```text
在云服务器部署 PostgreSQL 和 freshos-worker，并让 Hermes 拉齐 GitHub v1.1
```

原因：

- 本地代码和单元测试已经通过。
- V1.1 的核心公式和任务入口已经完成。
- 下一步的真实风险不在代码骨架，而在正式数据字段、云服务器配置、Hermes 执行链路和推送链路。

## 六、下次建议执行顺序

1. 在阿里云 ECS 安装并初始化 PostgreSQL。
2. 部署 `freshos-worker`。
3. 配置 `/etc/freshos/settings.toml`。
4. 执行迁移：

```bash
python3 scripts/apply_migrations.py \
  --config /etc/freshos/settings.toml
```

5. 配置 Hermes 拉取 GitHub `v1.1`。
6. 用正式大表哥 `40/42` 基础导出跑 `import_dabiaoge_base`。
7. 用正式日销售、库存、到货、12点实时销售跑 `import_dabiaoge_daily`。
8. 导入生鲜订单和人工盘点修正。
9. 跑完整每日任务链。
10. 检查三份报表：
    - `order_suggestions_YYYY-MM-DD.csv`
    - `inventory_risks_YYYY-MM-DD.csv`
    - `import_exceptions_YYYY-MM-DD.csv`
11. 根据导入异常补字段别名和商品匹配规则。
12. 将第一轮订货建议和人工订货、次日实际销量做回测。

## 七、历史开发记录说明

以下内容为 2026-05-27 起的逐步开发流水，保留用于追溯每一步从骨架到 V1.1 的演进。若与上方“当前状态快照”冲突，以上方当前状态为准。

## 八、2026-05-27 初始开发记录

### 1. freshos-worker 项目骨架

目录：

```text
freshos-worker/
  config/
  jobs/
  freshos/
  migrations/
  scripts/
  tests/
```

主要文件：

- `freshos-worker/README.md`
- `freshos-worker/config/settings.example.toml`
- `freshos-worker/migrations/001_initial_schema.sql`
- `freshos-worker/scripts/apply_migrations.py`

### 2. 数据库 schema 草案

已建立 V1 主要表结构：

- `stores`
- `products`
- `store_products`
- `sales_daily`
- `inventory_snapshots`
- `inventory_loss_daily`
- `purchase_receipts_daily`
- `fresh_order_imports`
- `stock_count_adjustments`
- `import_exceptions`
- `inventory_positions`
- `inventory_age_batches`
- `sales_forecasts`
- `order_suggestions`
- `inventory_risks`
- `job_runs`

### 3. Hermes 任务入口

已建立任务入口：

- `fetch_dabiaoge`
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

本地无数据库时：

```toml
[database]
enabled = false
```

生产开启数据库后，每个任务会写入 `job_runs`。

### 4. 订单 Excel 解析

已支持两个真实样表：

- `样表/宝信润山店.xlsx`
- `样表/5.25水果订单(2).xlsx`

解析结果：

```text
宝信润山店.xlsx：22 行
5.25水果订单(2).xlsx：29 行
合计：51 行
```

已实现统一字段输出，目标表为：

```text
fresh_order_imports
```

到货数量优先级：

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

### 5. 订单入库逻辑

`import_orders` 已支持：

- 数据库开启时写入 PostgreSQL `fresh_order_imports`
- 数据库关闭时输出 CSV
- 通过 `(source_file_name, source_sheet_name, raw_row_number)` 保证幂等

### 6. 门店/商品匹配回填

已实现：

- `match_order_imports` 任务
- 门店按名称匹配
- 商品按订单商品名称匹配
- 商品名前缀清洗：
  - `C-`
  - `Z-`
  - `JPZ-`
  - `R-`
- 回填：
  - `fresh_order_imports.store_id`
  - `fresh_order_imports.product_id`
  - `fresh_order_imports.match_status`
- 匹配失败写入：
  - `import_exceptions`

## 九、2026-05-27 初始验证命令

进入项目目录：

```bash
cd /Users/kangping/Documents/生鲜AI自动订货系统/freshos-worker
```

运行测试：

```bash
python3 -m pytest -q
```

当前结果：

```text
14 passed
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

运行每日任务链：

```bash
python3 -m jobs.run_daily \
  --config config/settings.example.toml \
  --business-date 2026-05-26
```

## 十、2026-05-27 当时限制

当前还没有接入真实 PostgreSQL。

因此以下能力已经写好代码，但没有真实连库验证：

- `fresh_order_imports` 入库
- `job_runs` 任务日志
- `match_order_imports` 数据库回填
- `import_exceptions` 数据库写入

当前还没有正式大表哥 40/42 导出数据。

因此以下能力已完成本地解析和 CSV 输出，但还没用正式 `40/42` 数据做真实验证：

- `stores` 导入
- `products` 导入
- `store_products` 导入

以下能力还没开始：

- 大表哥销售日汇总导入
- 大表哥库存/损耗导入
- 大表哥订货/收货导入

## 十一、2026-05-27 当时下次继续的第一步

下次优先做：

```text
大表哥基础数据导入
```

目标表：

```text
stores
products
store_products
```

原因：

- 订单解析和入库已经完成。
- 订单匹配逻辑已经完成。
- 但数据库里还没有门店和商品档案可匹配。
- 必须先导入基础档案，后续库存、销量、订货建议才能继续。

## 十二、2026-05-27 当时建议开发顺序

1. 读取大表哥 DOM 样本或正式导出文件。
2. 建立带表头字段映射。
3. 实现 `import_dabiaoge_base`：
   - 写入 `stores`
   - 写入 `products`
   - 写入 `store_products`
4. 用 40/42 正式数据验证。
5. 再测试：
   - `import_orders`
   - `match_order_imports`
6. 确认订单商品能匹配到 `products`。

## 十三、2026-05-27 大表哥基础数据导入记录

已按“大表哥基础数据导入”方向继续补齐：

- `import_dabiaoge_base` 支持 CSV、无表头 DOM 样本、带表头正式导出和 XLSX/XLSM 文件。
- 基础字段增加表头别名兼容，例如：
  - `门店编号` / `店铺编号`
  - `门店名称` / `店铺名称`
  - `大类编码` / `大分类编码`
  - `产品编码` / `商品编码`
  - `品名` / `商品名称`
  - `保质期` / `保质期限(天)`
- 多个输入文件合并导出时，按：
  - `store_code`
  - `product_code`
  - `(store_code, product_code)`
  去重输出 `stores.csv`、`products.csv`、`store_products.csv`。
- 新增测试覆盖：
  - 40/42 生鲜分类过滤
  - 表头别名解析
  - XLSX 基础数据解析

验证结果：

```text
python3 -m pytest -q
当前结果：14 passed
```

用当前 DOM 样本试跑：

```bash
python3 -m jobs.import_dabiaoge_base \
  --config config/settings.example.toml \
  --business-date 2026-05-26 \
  --input ../data_samples/dabiaoge_stores_products_base_dom.csv \
  --output /private/tmp/freshos_dabiaoge_base_check
```

当前样本 100 行的大分类编码全部为 `01`，默认只导入 `40/42` 时结果为：

```text
stores=0 products=0 store_products=0
```

这是过滤规则导致的正常结果，不是解析失败。

下一步建议：

1. 等正式大表哥 `40/42` 基础数据导出后，直接跑 `import_dabiaoge_base` 验证真实落库。
2. 接入 PostgreSQL 后验证：
   - `stores`
   - `products`
   - `store_products`
   upsert。
3. 用正式基础数据再跑：
   - `import_orders`
   - `match_order_imports`
   确认订单商品能匹配到 `products`。

## 十四、2026-05-27 日数据导入继续开发记录

在没有正式大表哥 `40/42` 导出文件的情况下，继续推进不依赖正式数据的 P3 开发：大表哥日数据导入。

已完成：

- `import_dabiaoge_daily` 支持带表头 CSV、XLSX/XLSM。
- 缺少日期字段时，使用命令行 `--business-date` 作为默认营业日期。
- 同一门店、商品、日期的重复行会先合并为日汇总，再输出 CSV 或入库。
- 当前支持的 `--report-type`：
  - `sales`
  - `inventory_loss`
  - `purchase_receipts`
  - `inventory_snapshot`
- 日汇总合并规则：
  - 销售数量、销售金额：求和。
  - 报损数量、报损金额、盘盈盘亏数量：求和。
  - 订货、收货、总收货、总退货/调出：求和。
  - 期末库存、实时库存：保留后出现的值。
- 新增测试覆盖：
  - 缺日期时使用 `--business-date`
  - XLSX 库存快照解析
  - 重复销售行合并为日汇总

验证结果：

```text
python3 -m pytest -q
当前结果：17 passed
```

临时 CSV 试跑结果：

```text
2 行销售明细合并为 1 行日汇总
sales_quantity=10.0
sales_amount=50.0
```

## 十五、2026-05-27 计算链路继续开发记录

继续推进 V1 最小闭环中不依赖正式导出文件的计算任务，将原占位 job 接入真实数据库计算入口。

已完成：

- `calculate_inventory`
  - 接入 `freshos.db.inventory.calculate_inventory_positions`
  - 目标表：`inventory_positions`
  - 主库存优先级：实时库存快照 > 期末库存 > 理论库存
  - 理论库存：昨日修正库存 + 当日到货 - 当日销售 - 当日报损
  - 支持人工盘点修正值叠加
- `generate_order_suggestions`
  - 接入 `freshos.db.order_suggestions.generate_order_suggestions`
  - 目标表：`order_suggestions`
  - 基于销量预测、修正库存、安全库存、已订未到、最小订货量、订货批量计算建议量
- `generate_inventory_risks`
  - 接入 `freshos.db.inventory_risks.generate_inventory_risks`
  - 目标表：`inventory_risks`
  - 生成负库存、缺货、高库存、临期/过期、高损耗等风险

本地无数据库时：

```text
database.enabled=false
```

上述任务会安全跳过，不中断每日任务链。

验证结果：

```text
python3 -m pytest -q
当前结果：17 passed

python3 -m jobs.run_daily --config config/settings.example.toml --business-date 2026-05-26
当前结果：任务链跑通，本地无数据库时 DB 计算任务安全跳过
```

## 十六、2026-05-27 报表导出继续开发记录

继续补齐 V1 最小闭环最后一段：将计算结果导出为每日文件。

已完成：

- `export_reports` 接入数据库读取：
  - `order_suggestions`
  - `inventory_risks`
- 数据库开启时：
  - 导出真实订货建议明细 CSV。
  - 导出真实库存风险明细 CSV。
  - 订货建议明细会根据当天高风险库存记录标记“高风险”。
- 数据库关闭时：
  - 保持原有行为，输出空报表模板，不中断每日任务链。
- 新增报表读取单元测试：
  - 订货建议字段映射。
  - 库存风险字段映射。
  - 高风险标记逻辑。

验证结果：

```text
python3 -m pytest -q
当前结果：19 passed

python3 -m jobs.export_reports --config config/settings.example.toml --business-date 2026-05-26
当前结果：本地无数据库时成功输出空模板
```

## 十七、2026-05-27 最小闭环种子数据记录

为下一步 PostgreSQL 集成验证补齐可重复执行的最小闭环数据。

已新增：

- `freshos-worker/seeds/001_minimal_closure.sql`
- `freshos-worker/scripts/apply_seed_data.py`

种子数据包含：

- 1 个门店：宝信润山店
- 1 个商品：海南香蕉
- 1 条门店商品关系
- 14 天销售数据
- 1 条 2026-05-26 实时库存快照
- 1 条 2026-05-26 损耗记录
- 1 条 2026-05-27 到货记录

用途：

- 验证 `inventory_positions`
- 验证 `sales_forecasts`
- 验证 `order_suggestions`
- 验证 `inventory_risks`
- 验证每日 CSV 报表导出

新增依赖：

```text
psycopg[binary]>=3.2
```

验证结果：

```text
python3 -m pytest -q
当前结果：19 passed

PYTHONPYCACHEPREFIX=/private/tmp/freshos_pycache python3 -m py_compile \
  scripts/apply_seed_data.py \
  freshos/db/inventory.py \
  freshos/db/order_suggestions.py \
  freshos/db/inventory_risks.py \
  freshos/db/reports.py
当前结果：通过
```

## 十八、2026-05-27 阿里云部署准备记录

确认目标部署环境为阿里云 ECS 服务器，不按本机 Docker 作为主要部署路径。

已新增：

- `freshos-worker/deploy/ALIYUN_ECS_DEPLOY.md`
- `freshos-worker/config/settings.aliyun.example.toml`
- `freshos-worker/deploy/systemd/freshos-worker.service`
- `freshos-worker/deploy/systemd/freshos-worker.timer`
- `freshos-worker/requirements.txt`

部署原则：

- PostgreSQL 安装在同一台 ECS。
- PostgreSQL 默认只监听 `127.0.0.1`。
- 阿里云安全组不开放 `5432`。
- SSH 只允许可信公网 IP。
- FreshOS 配置文件放在 `/etc/freshos/settings.toml`。
- 数据和报表目录放在 `/var/lib/freshos/`。
- systemd timer 可作为 Hermes 之外的服务器定时任务方案。

验证结果：

```text
python3 -m pytest -q
当前结果：19 passed

PYTHONPYCACHEPREFIX=/private/tmp/freshos_pycache python3 -m py_compile \
  scripts/apply_seed_data.py \
  scripts/run_minimal_closure.py
当前结果：通过
```

## 十九、2026-05-27 工具使用方式补齐记录

检查《FreshOS-V1开发实施计划.md》后确认：原计划说明了 V1 形态、Hermes 调度、任务清单、报表和推送，但没有完整说明业务人员和系统维护人员如何使用工具。

已新增：

- `FreshOS-V1工具使用方式与业务操作流程.md`

已同步引用：

- `FreshOS-V1开发实施计划.md`
- `FreshOS-项目总控文档.md`

新增文档覆盖：

- V1 工具形态
- 角色分工
- 每日自动流程
- 业务人员怎么看订货建议和库存风险
- 系统维护人员如何补跑任务和查看日志
- 人工介入流程
- 输入 / 输出文件流转
- 当前 V1 不做的使用方式
- 判断工具是否正常运行的检查清单

## 二十、2026-05-27 人工盘点修正导入开发记录

按 V1 最小闭环继续补齐 `import_stock_adjustments`，该任务原先仍是占位。

已完成：

- 新增 `freshos.importers.stock_adjustments`
  - 支持人工盘点修正模板 XLSX/XLSM。
  - 支持 CSV。
  - 支持中文表头别名。
  - 缺少盘点时间时，可使用 `--business-date` 生成默认时间。
- 新增 `freshos.db.stock_adjustments`
  - 按门店编码/名称匹配 `stores`。
  - 按商品编码/名称匹配 `products`。
  - 匹配成功写入 `stock_count_adjustments`。
  - 匹配失败写入 `import_exceptions`。
- 更新 `jobs.import_stock_adjustments`
  - 数据库开启时写入 PostgreSQL。
  - 数据库关闭时输出 CSV。
- 更新数据库 schema
  - 为 `stock_count_adjustments(store_id, product_id, count_time)` 增加唯一索引，支持幂等重跑。
- 新增测试覆盖：
  - 真实人工盘点修正模板解析。
  - CSV 中文别名解析。
  - XLSX 中文别名解析。

验证结果：

```text
python3 -m pytest -q
当前结果：22 passed

python3 -m jobs.import_stock_adjustments \
  --config config/settings.example.toml \
  --business-date 2026-05-26 \
  --input ../data_templates/人工盘点修正模板.xlsx \
  --output /private/tmp/freshos_stock_adjustments_check.csv
当前结果：解析 1 行并成功输出 CSV
```

## 二十一、2026-05-27 库存年龄计算开发记录

按总纲“库存数量不重要，库存年龄更重要”的方向，补齐 `inventory_age_batches` 计算入口。

已完成：

- 新增 `freshos.db.inventory_age`
  - 从 `fresh_order_imports` 汇总同一门店、商品、到货日期的到货批次。
  - 使用 `store_products.sellable_days_override`、`products.sellable_days`、`products.shelf_life_days` 推导可售天数。
  - 按门店商品维度汇总销售数量。
  - 使用 FIFO 规则估算批次消耗。
  - 计算：
    - `batch_quantity`
    - `consumed_quantity`
    - `remaining_quantity`
    - `expiry_date`
    - `remaining_sellable_days`
    - `batch_status`
- 更新 `calculate_inventory`
  - 同时计算 `inventory_positions`
  - 同时计算 `inventory_age_batches`
- 新增测试覆盖：
  - FIFO 优先消耗最早到货批次。
  - 过期批次状态识别。

验证结果：

```text
python3 -m pytest -q
当前结果：24 passed

python3 -m jobs.calculate_inventory --config config/settings.example.toml --business-date 2026-05-26
当前结果：本地无数据库时安全跳过
```

## 二十二、2026-05-27 导入异常报表开发记录

继续补齐 V1 每日报表输出，增加“导入异常明细”。

已完成：

- `export_reports` 新增导出：
  - `import_exceptions_YYYY-MM-DD.csv`
- 数据库开启时：
  - 从 `import_exceptions` 读取 `status='open'` 的异常。
  - 输出来源文件、来源表、原始行号、异常类型、异常说明、处理状态、创建时间。
- 数据库关闭时：
  - 输出空模板，不中断每日任务链。
- 新增测试覆盖：
  - 导入异常报表字段映射。

验证结果：

```text
python3 -m pytest -q
当前结果：25 passed

python3 -m jobs.export_reports --config config/settings.example.toml --business-date 2026-05-26
当前结果：成功生成三份空模板
  - order_suggestions_2026-05-26.csv
  - inventory_risks_2026-05-26.csv
  - import_exceptions_2026-05-26.csv
```

## 二十三、2026-05-27 每日推送摘要开发记录

继续补齐 V1 最小闭环最后一步：企业微信 / 飞书推送摘要。

已完成：

- 新增 `freshos.db.summary`
  - 查询需订商品数。
  - 查询建议订货总量。
  - 查询高风险商品数。
  - 查询缺货风险数。
  - 查询临期 / 过期风险数。
  - 查询待处理导入异常数。
- 更新 `jobs.notify`
  - 数据库开启时读取真实摘要。
  - 数据库关闭时输出本地模板模式摘要。
  - 摘要中列出三份报表路径：
    - 订货建议
    - 库存风险
    - 导入异常
- 新增测试覆盖：
  - 每日摘要查询映射。
  - 推送文本生成。

验证结果：

```text
python3 -m pytest -q
当前结果：27 passed

python3 -m jobs.notify --config config/settings.example.toml --business-date 2026-05-26
当前结果：本地 provider=none 时打印每日摘要，不发送 webhook
```

## 二十四、相关文档

- `FreshOS-生鲜AI经营系统总纲.md`
- `FreshOS-V1多门店产品需求与数据表设计.md`
- `FreshOS-V1数据库与导入设计.md`
- `FreshOS-V1开发实施计划.md`
- `FreshOS-V1工具使用方式与业务操作流程.md`
- `FreshOS-项目总控文档.md`
- `freshos-worker/README.md`

## 二十五、2026-06-02 V1.1 开发进度更新

本阶段已按最新总纲完成 V1.1 口径调整：每天12:00出次日订货建议，使用实时销售做轻量趋势修正，并使用预计到货前库存替代简单当前库存参与订货计算。

### 1. 当前版本状态

当前代码版本：

```text
v1.1
```

GitHub 当前主分支记录：

```text
0329ea5 feat: add v1.1 noon trend ordering
```

当前重点已经从“补齐最小闭环代码”转为“用正式大表哥数据和云服务器环境验证闭环”。

### 2. V1.1 已完成内容

已完成：

- 新增 `sales_cutoff_snapshots`，用于保存12点实时销售、12点库存和在途数量。
- 大表哥日数据导入支持 `cutoff_snapshot` / 12点实时快照类数据。
- 销量预测支持12点趋势修正：
  - 先按最近7天有效销售均值预测。
  - 不足时回退最近14天。
  - 再不足时回退大表哥 recent_daily_sales。
  - 历史12点占比低于20%时，不启用趋势修正。
  - 启用趋势修正时，修正幅度限制在 0.9 到 1.1。
- 订货建议支持预计到货前库存：
  - 当前12点库存。
  - 减去预计今日剩余销售。
  - 减去预计今日损耗。
  - 加上今日在途/到货。
- `order_suggestions` 增加 `expected_inventory_at_arrival` 口径。
- 单元测试覆盖：
  - 12点趋势修正启用。
  - 历史12点占比过低时跳过修正。
  - 预计到货前库存参与订货量计算。
  - 12点实时快照导入解析。

### 3. 最新验证结果

已重新运行测试：

```text
cd /Users/kangping/Documents/生鲜AI自动订货系统/freshos-worker
python3 -m pytest -q
```

当前结果：

```text
36 passed
```

### 4. 当前仍待正式数据验证

代码逻辑已经完成，但还没有用正式线上大表哥数据做完整验证。下一步需要验证：

1. 大表哥 40/42 商品基础导出是否能完整导入 `stores`、`products`、`store_products`。
2. 最近30天销售日汇总是否能稳定导入 `sales_daily`。
3. 历史0-12点实时销售是否能形成可靠 `historical_noon_ratio`。
4. 今日0-12点实时销售是否能写入 `sales_cutoff_snapshots`。
5. 昨日期末库存、12点实时库存、今日在途数量是否能支持 `expected_inventory_at_arrival`。
6. 订货建议是否能和人工订货、次日实际销量做回测对比。
7. 企业微信/飞书 webhook 是否能发送正式摘要和附件路径。

### 5. 下一步继续任务

下一步优先级：

1. 在云服务器部署 PostgreSQL 和 `freshos-worker`。
2. 配置 Hermes 拉取 GitHub `v1.1` 版本。
3. 配置生产 `/etc/freshos/settings.toml`。
4. 用正式大表哥 40/42 基础数据跑通导入。
5. 用大表哥实时销售数据跑通12点快照导入。
6. 跑完整每日任务链：

```bash
python3 -m jobs.run_daily \
  --config /etc/freshos/settings.toml \
  --business-date YYYY-MM-DD
```

7. 检查三份输出：
   - `order_suggestions_YYYY-MM-DD.csv`
   - `inventory_risks_YYYY-MM-DD.csv`
   - `import_exceptions_YYYY-MM-DD.csv`

8. 根据首轮正式数据结果补字段别名、修正匹配规则、调整商品参数。

## 二十六、2026-06-02 文档归拢和清理记录

本次检查了项目根目录、`data_samples/`、`freshos-worker/`、`freshos-worker/deploy/` 和 `freshos-worker/workspace/` 下的 Markdown 文件。

### 1. 保留为主入口的文档

以下文档保留，作为后续工作入口：

- `FreshOS-项目总控文档.md`
- `FreshOS-生鲜AI经营系统总纲.md`
- `FreshOS-V1开发进度与下次继续.md`
- `FreshOS-V1开发实施计划.md`
- `FreshOS-V1工具使用方式与业务操作流程.md`

其中：

- 总控文档负责统一入口。
- 总纲负责产品和公式口径。
- 开发进度负责当前状态和下一步。
- 实施计划负责执行顺序。
- 工具使用流程负责业务和维护人员怎么操作。

### 2. 保留为技术设计 / 操作依据的文档

以下文档仍有独立价值，暂不删除：

- `FreshOS-V1数据库与导入设计.md`
- `FreshOS-V1多门店产品需求与数据表设计.md`
- `FreshOS-V1阿里云服务器部署实操记录.md`
- `freshos-worker/README.md`
- `freshos-worker/deploy/ALIYUN_ECS_DEPLOY.md`
- `data_samples/大表哥导出预设清单.md`
- `data_samples/dabiaoge_stores_products_base_dom说明.md`
- `skills/dabiaoge/SKILL.md`
- `skills/dabiaoge/TEST_PLAN.md`
- `skills/dabiaoge/GITHUB_DOWNLOAD.md`

保留原因：

- 数据库与多门店设计仍包含字段级历史设计。
- 阿里云实操记录包含真实服务器踩坑。
- worker README 和部署指南直接服务上线。
- 大表哥样本说明和导出预设仍服务 Hermes 字段校验。
- `skills/dabiaoge` 是自动化抓取能力说明，不属于 FreshOS 业务文档冗余。

### 3. 已删除的无用 / 重复文档

已删除：

- `FreshOS-V1数据整理回顾.md`
- `freshos-worker/workspace/order_qty_test_2026-05-28/README.md`

删除原因：

- `FreshOS-V1数据整理回顾.md` 是早期阶段性回顾，核心结论已经被总控、总纲、开发进度吸收。
- `order_qty_test_2026-05-28/README.md` 是一次性测试暂存目录说明，测试口径已过期，当前 V1.1 以 12点实时销售和正式大表哥数据验证为准。

### 4. 当前文档口径

归拢后统一口径：

- 当前版本为 `v1.1`。
- 每天 12:00 生成次日订货建议。
- 使用 0-12 点实时销售做轻量趋势修正。
- 使用预计到货前库存参与订货。
- 商品名称包含 `折` 或等于 `D系统用代表商品` 时，不计入常规订货建议。
- 下一步是云服务器部署、Hermes 拉齐 `v1.1`、正式大表哥数据验证。

## 二十七、2026-06-02 Hermes 导出文件检查开发记录

检查已确定但未开发的项目后，确认 `jobs.fetch_dabiaoge` 仍是占位入口。由于大表哥登录、筛选和导出由 Hermes 负责，worker 不直接实现浏览器抓取；本次将该入口改成“当日必需导出文件检查”。

已完成：

- 新增 `freshos.importers.dabiaoge_fetch`。
- `jobs.fetch_dabiaoge` 会检查 `settings.paths.data_dir` 下是否存在当日必需文件。
- `jobs.run_daily` 会自动按业务日期从 `settings.paths.data_dir` 匹配大表哥文件，并传给对应导入任务。
- 当前必需文件类型：
  - 基础数据
  - 销售日汇总
  - 库存 / 损耗
  - 订货 / 收货
  - 12点实时销售
- 如果缺文件，任务直接失败，并列出缺少的报表类型和期望文件名模式。
- 更新 `freshos-worker/README.md`，同步 V1.1 的 12:00 Hermes 调度和 `cutoff_sales` 导入。

验证结果：

```text
python3 -m pytest -q
当前结果：39 passed
```

注意：

```text
fetch_dabiaoge 不负责登录大表哥。
Hermes 负责导出文件。
freshos-worker 负责检查文件是否齐全、导入、计算、报表和推送。
```

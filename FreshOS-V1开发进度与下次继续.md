# FreshOS V1 开发进度与下次继续

更新时间：2026-05-27

## 一、当前实现方向

V1 采用云端自动订货助手形态：

```text
云服务器 freshos-worker
  ↓
Hermes 自动导出大表哥 40/42 数据
  ↓
Hermes 触发 freshos-worker 导入订单 / 盘点 / 大表哥导出文件
  ↓
FreshOS 计算订货建议和库存风险
  ↓
生成 Excel/CSV 明细
  ↓
企业微信/飞书推送摘要和附件
```

第一阶段不优先做完整 Web 后台。

## 二、今天完成的开发

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

## 三、验证命令

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

## 四、当前限制

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

## 五、下次继续的第一步

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

## 六、下次建议开发顺序

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

## 八、2026-05-27 继续开发记录

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

## 九、2026-05-27 日数据导入继续开发记录

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

## 十、2026-05-27 计算链路继续开发记录

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

## 十一、2026-05-27 报表导出继续开发记录

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

## 十二、2026-05-27 最小闭环种子数据记录

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

## 十三、2026-05-27 阿里云部署准备记录

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

## 十四、2026-05-27 工具使用方式补齐记录

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

## 十五、2026-05-27 人工盘点修正导入开发记录

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

## 十六、2026-05-27 库存年龄计算开发记录

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

## 十七、2026-05-27 导入异常报表开发记录

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

## 十八、2026-05-27 每日推送摘要开发记录

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

## 十九、相关文档

- `FreshOS-生鲜AI经营系统总纲.md`
- `FreshOS-V1多门店产品需求与数据表设计.md`
- `FreshOS-V1数据库与导入设计.md`
- `FreshOS-V1开发实施计划.md`
- `FreshOS-V1工具使用方式与业务操作流程.md`
- `FreshOS-项目总控文档.md`
- `freshos-worker/README.md`

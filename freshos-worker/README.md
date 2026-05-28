# freshos-worker

FreshOS V1 云端自动订货助手。

第一版目标：

```text
Hermes 自动导出大表哥 40/42 数据
  ↓
Hermes 触发 freshos-worker
  ↓
导入订单 / 盘点 / Hermes 导出文件
  ↓
计算库存口径、销量预测、订货建议、库存风险
  ↓
生成报表
  ↓
企业微信/飞书推送
```

## 目录

```text
config/       配置模板
jobs/         Hermes 可调用任务入口
freshos/      业务模块
migrations/   PostgreSQL schema
tests/        核心规则测试
```

## 初始化数据库

```bash
python scripts/apply_migrations.py --config config/settings.toml
```

本地没有 PostgreSQL 时，可以先保持：

```toml
[database]
enabled = false
```

生产环境打开后，所有 job 会写入 `job_runs`，记录开始时间、结束时间、状态和错误信息。

`import_orders` 在 `database.enabled = true` 时会写入 PostgreSQL `fresh_order_imports`；本地关闭数据库时会输出 CSV。

## 最小闭环验证数据

配置好 PostgreSQL 后，可以先用内置种子数据跑一遍 V1 最小闭环。

阿里云 ECS 部署请先看：

```text
deploy/ALIYUN_ECS_DEPLOY.md
```

先复制配置模板并修改 DSN：

```bash
cp config/settings.local.example.toml config/settings.toml
```

一键执行：

```bash
python scripts/run_minimal_closure.py --config config/settings.toml --business-date 2026-05-26
```

或分步执行：

```bash
python scripts/apply_migrations.py --config config/settings.toml
python scripts/apply_seed_data.py --config config/settings.toml

python -m jobs.calculate_inventory --config config/settings.toml --business-date 2026-05-26
python -m jobs.forecast_sales --config config/settings.toml --business-date 2026-05-26
python -m jobs.generate_order_suggestions --config config/settings.toml --business-date 2026-05-26
python -m jobs.generate_inventory_risks --config config/settings.toml --business-date 2026-05-26
python -m jobs.export_reports --config config/settings.toml --business-date 2026-05-26
```

种子数据包含 1 个门店、1 个商品、14 天销售、1 条库存快照、1 条损耗记录和 1 条次日到货记录，用于验证：

- `inventory_positions`
- `sales_forecasts`
- `order_suggestions`
- `inventory_risks`
- 每日报表 CSV：订货建议、库存风险、导入异常

## 本地运行每日任务链

```bash
python -m jobs.run_daily --config config/settings.example.toml --business-date 2026-05-25
```

当前版本是骨架实现：会生成空报表并打印占位任务。接入真实数据后，job 会逐步替换为真实抓取、导入、计算和推送。

## 单独运行任务

```bash
python -m jobs.fetch_dabiaoge --business-date 2026-05-25
python -m jobs.import_dabiaoge_base --business-date 2026-05-25 --input "../data_samples/dabiaoge_stores_products_base_dom.csv"
python -m jobs.import_dabiaoge_daily --business-date 2026-05-25 --report-type sales --input "../data_samples/sales_daily.csv"
python -m jobs.import_orders --business-date 2026-05-25 --input "../样表/宝信润山店.xlsx" --input "../样表/5.25水果订单(2).xlsx"
python -m jobs.match_order_imports --business-date 2026-05-25
python -m jobs.calculate_inventory --business-date 2026-05-25
python -m jobs.forecast_sales --business-date 2026-05-25
python -m jobs.generate_order_suggestions --business-date 2026-05-25
python -m jobs.generate_inventory_risks --business-date 2026-05-25
python -m jobs.export_reports --business-date 2026-05-25
python -m jobs.notify --business-date 2026-05-25
```

`import_dabiaoge_base` 支持无表头 DOM CSV、带表头 CSV、XLSX/XLSM，默认只导入大分类编码 `40/42`。

`import_dabiaoge_daily` 支持带表头 CSV、XLSX/XLSM，可导入 `sales`、`inventory_loss`、`purchase_receipts`、`inventory_snapshot`。如果原始文件缺少日期字段，会使用 `--business-date`；同一门店、商品、日期的重复行会先合并为日汇总再输出或入库。

`import_stock_adjustments` 支持人工盘点修正模板 CSV、XLSX/XLSM。数据库开启时会按门店编码/名称、商品编码/名称匹配并写入 `stock_count_adjustments`；无法匹配的数据写入 `import_exceptions`。数据库关闭时输出 CSV。

`notify` 会推送每日摘要，包括需订商品数、建议订货总量、高风险商品数、缺货风险、临期/过期和待处理导入异常，并列出三份报表路径。

## Hermes 调度建议

| 时间 | 任务 |
| --- | --- |
| 06:00 | `python -m jobs.fetch_dabiaoge` |
| 06:10 | `python -m jobs.import_dabiaoge_base` |
| 06:15 | `python -m jobs.import_dabiaoge_daily --report-type sales` |
| 06:16 | `python -m jobs.import_dabiaoge_daily --report-type inventory_loss` |
| 06:17 | `python -m jobs.import_dabiaoge_daily --report-type purchase_receipts` |
| 06:18 | `python -m jobs.import_dabiaoge_daily --report-type inventory_snapshot` |
| 06:20 | `python -m jobs.import_orders` |
| 06:25 | `python -m jobs.match_order_imports` |
| 06:40 | `python -m jobs.calculate_inventory` |
| 06:50 | `python -m jobs.forecast_sales` |
| 07:00 | `python -m jobs.generate_order_suggestions` |
| 07:05 | `python -m jobs.generate_inventory_risks` |
| 07:10 | `python -m jobs.export_reports && python -m jobs.notify` |

## 下一步

1. 配置 Hermes 将大表哥 40/42 导出文件写入 `/var/lib/freshos/data/`。
2. 用正式 Hermes 导出文件补齐日数据字段别名。
3. 验证正式门店 / 商品 / 门店商品关系导入。
4. 验证正式销售、库存、订货、收货、订单、盘点数据导入。
5. 将 CSV 报表升级为 XLSX 报表。
6. 接入企业微信/飞书 webhook。

# 大表哥 Skill 测试清单

用途：验证 API-first 大表哥导出是否满足 FreshOS V1 入库要求。

## 1. 安全检查

- `SKILL.md` 不包含账号、密码、Cookie、Session、Token。
- Python 脚本不得硬编码 `USERNAME` / `PASSWORD`。
- 真实业务导出数据不要提交到 GitHub，除非用户明确批准。

## 2. API 路径检查

生产导出应使用 Python requests 调用接口，不依赖浏览器 UI 字段勾选。

必须经过：

```text
/KIT/T10006/initData
/KIT/T10006/businessData
/KIT/T10006/getTableData
```

业务日粒度文件必须使用：

```text
reportType=3
```

base 映射文件可使用：

```text
reportType=4
```

## 3. 文件清单

应生成：

```text
dabiaoge_stores_products_base.xlsx
dabiaoge_sales_daily.xlsx
dabiaoge_inventory_loss_daily.xlsx
dabiaoge_purchase_receipts_daily.xlsx
```

暂不要求：

```text
dabiaoge_inventory_snapshot.xlsx
```

## 4. 表头检查

sales:

```text
店铺编号, 店铺名称, 大分类编码, 商品编码, 商品名称, 日期, 销量, 销售额
```

inventory_loss:

```text
店铺编号, 店铺名称, 大分类编码, 商品编码, 商品名称, 日期, 库存数量（期末）, 报损数量, 报损金额, 盘盈盘亏数量
```

purchase_receipts:

```text
店铺编号, 店铺名称, 大分类编码, 商品编码, 商品名称, 日期, 订货数量, 收货数量, 总收货数量, 总退货+调出数量
```

base:

```text
店铺编号, 店铺名称, 店铺状态, 大分类编码, 大分类名称, 中分类编码, 中分类名称, 商品编码, 商品名称, 销售单位, 保质期限(天)
```

注意：

```text
库存数量（期末）
```

必须使用中文括号。

## 5. 数据范围检查

每个文件检查：

- 大分类编码只包含 `40` 和 `42`。
- 门店包含 `10002`, `10003`, `10008`。
- 必需字段无空值。
- 数值字段不是全部 0。

业务日粒度文件检查：

- 必须有 `日期` 列。
- 日期范围连续。
- 行数 = store-product 行数 * 日期天数。

## 6. FreshOS Importer 检查

在 `freshos-worker` 目录运行：

```bash
PYTHONPATH=. python3 - <<'PY'
from pathlib import Path
from freshos.importers.dabiaoge_base import parse_dabiaoge_base_file
from freshos.importers.dabiaoge_daily import parse_dabiaoge_daily_file, merge_dabiaoge_daily_rows

data_dir = Path("/var/lib/freshos/data")

base = parse_dabiaoge_base_file(data_dir / "dabiaoge_stores_products_base.xlsx")
print("base", len(base.stores), len(base.products), len(base.store_products))

for report_type, filename in [
    ("sales", "dabiaoge_sales_daily.xlsx"),
    ("inventory_loss", "dabiaoge_inventory_loss_daily.xlsx"),
    ("purchase_receipts", "dabiaoge_purchase_receipts_daily.xlsx"),
]:
    rows = parse_dabiaoge_daily_file(data_dir / filename, report_type=report_type, default_business_date="2026-05-28")
    merged = merge_dabiaoge_daily_rows(rows)
    dates = sorted({row.business_date for row in rows})
    stores = sorted({row.store_code for row in rows})
    print(report_type, len(rows), len(merged), dates[0], dates[-1], len(dates), stores)
PY
```

期望样例：

```text
base stores=3 products=865 store_products=2595
sales rows=22092 dates=28 stores=10002/10003/10008
inventory_loss rows=22092 dates=28 stores=10002/10003/10008
purchase_receipts rows=22092 dates=28 stores=10002/10003/10008
```

## 7. 入库方式

业务文件已经有 `日期` 列时，不需要逐日拆文件导入。FreshOS importer 会优先使用文件中的日期。

示例：

```bash
python -m jobs.import_dabiaoge_daily \
  --config /etc/freshos/settings.toml \
  --business-date 2026-05-28 \
  --report-type sales \
  --input /var/lib/freshos/data/dabiaoge_sales_daily.xlsx
```

`--business-date` 只是默认日期；文件里有 `日期` 列时，会按每行日期入库。

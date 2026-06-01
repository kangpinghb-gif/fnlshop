---
name: dabiaoge
description: 盛和 A+ 大表哥数据导出工具。优先使用 Python requests 直接调用 XHR 接口，导出 FreshOS V1 所需的 base/sales/inventory/purchase 日粒度数据；浏览器 UI 仅用于人工排查，不作为生产导出路径。
---

# 盛和 A+ 大表哥数据导出

## Safety Rules

- Do not store usernames, passwords, SMS codes, one-time codes, cookies, session IDs, or tokens in this skill, scripts, sample files, or GitHub.
- Do not commit real credentials or exported production business data unless the user explicitly approves that data for version control.
- If a script needs credentials, read them from environment variables or a server-side secret manager at runtime.
- If `checkLogin` indicates SMS, QR-code, MFA, or another interactive verification is required, stop and ask the user to complete it. Do not bypass verification.
- Use a read-only reporting account whenever possible.
- Do not perform write actions in 盛和 A+.

## Core Strategy

Do not use browser UI clicks to select report fields for production exports.

`changeItemColorBox()` and `changeItemColor()` only switch visual checkbox state. In observed runs, they did not reliably change the `th[colApply='1']` structure used by `customerSearchAll()` to build request parameters. Therefore, UI-selected fields can look correct while exported or queried data is incomplete.

Correct production path:

```text
Python requests
-> authenticated session
-> /KIT/T10006/initData
-> /KIT/T10006/businessData
-> /KIT/T10006/getTableData
-> flatten to FreshOS-compatible XLSX/CSV
```

## API Call Chain

```text
1. GET  /KIT/homePage/login              -> get initial cookie
2. POST /KIT/homePage/checkLogin         -> login pre-check
3. POST /KIT/homePage/doLogin            -> submit login form and get session
4. POST /KIT/T10006/initData             -> initialize report, reportType=3 for daily data
5. POST /KIT/T10006/businessData         -> load business field definitions, required
6. POST /KIT/T10006/getTableData         -> fetch paged data
```

Login notes:

- Passwords are submitted as uppercase MD5 hashes by the site workflow.
- `checkLogin` returning `{code: 2}` has been observed as direct login allowed.
- `checkLogin` returning `{code: 0}` means SMS or another interactive verification may be required; do not automate that path.
- `doLogin` can return `302`; follow the redirect to `/KIT/homePage`.

## Report Types

| type | Name | FreshOS use | Grain |
| --- | --- | --- | --- |
| 1 | 期间查询报表 | Period total only; do not use for FreshOS daily imports | Period aggregate |
| 3 | 期间趋势报表 | sales / inventory_loss / purchase_receipts daily files | Daily |
| 4 | 主档查询报表 | base mapping, store x product | Static mapping |
| 5 | 今日实时报表 | realtime query / intraday replenishment check only | Current point-in-time |

Selection rules:

- `base`: use type=4. It is static store-product mapping and does not need a date column.
- `sales`, `inventory_loss`, `purchase_receipts`: use type=3. FreshOS needs daily rows, and type=1 only returns period totals.
- Morning order quantity calculation must use type=3 historical daily data as the primary source.
- Do not use type=5 today sales as the main forecast input for morning ordering; early-day sales are incomplete and can understate full-day demand.
- Use type=5 only for realtime lookup, exception monitoring, and optional intraday replenishment decisions after sales have materially occurred.

## Type 5 Realtime Data Scope

type=5 今日实时报表 uses a different field set from type=1/type=3. Do not reuse type=1/type=3 field parameters in type=5.

Verified type=5 fields:

| Business meaning | type=1/type=3 field | type=5 field | type=5 biz_type | type=5 biz_type_t | FreshOS use |
| --- | --- | --- | --- | --- | --- |
| Sales quantity | `sales_qty` | `sale_qty` | `96` | `2` | realtime query only |
| Sales amount | `sales_amt` | `sale_amt` | `96` | `2` | realtime query only |
| Period closing stock | `closing_stock_qty` | not available | - | - | use type=3 instead |
| Realtime stock | period inventory fields | `stock_qty` | `97` | `2` | realtime lookup / exception monitoring |
| On-order quantity | not stable in type=3 | `on_order_qty` | `98` | `2` | realtime lookup / intraday replenishment check |

Confirmed behavior:

- `sales_qty`, `sales_amt`, and `closing_stock_qty` do not exist in type=5 `businessData`.
- `sale_qty`, `sale_amt`, `stock_qty`, and `on_order_qty` work in type=5 and can be queried together.
- type=5 can sort by realtime fields, for example `order_column=sale_qty&order_value=DESC`.

FreshOS V1 policy:

- Formal morning ordering: use type=3 historical sales, inventory/loss, and purchase/receipt data.
- Realtime type=5 data: use for dashboards, realtime stock checks, high-sales low-stock monitoring, and manual afternoon replenishment prompts.

## Type 3 Daily Data Shape

type=3 returns one wide row per store-product and multiple value columns by date.

Observed shape for 2026-05-01 through 2026-05-28:

```text
base fields + 28 days * N business fields
```

Example:

```text
sales = 5 base fields + 28 * 2 values
inventory_loss = 5 base fields + 28 * 4 values
purchase_receipts = 5 base fields + 28 * 4 values
```

`title_columns` can be empty. Parse value columns by the requested date list order and the number of business fields per date, then flatten to:

```text
店铺编号, 店铺名称, 大分类编码, 商品编码, 商品名称, 日期, business fields...
```

## Type 3 / Type 4 Field Parameters

Never guess field parameters. Prefer extracting definitions from `businessData`.

The following values have been verified for the FreshOS V1 type=3/type=4 export path. Type=5 has a different field set; use the dedicated type=5 table above for realtime fields.

| data_column | biz_type | biz_type_t | data_type |
| --- | --- | --- | --- |
| `store_id` / `store_name` / `status_desc` | `10` | `0` | `char` |
| `cat_id_01` / `cat_name_01` | `11` | `0` | `char` |
| `cat_id_02` / `cat_name_02` | `11` | `0` | `char` |
| `item_cd` / `item_name_dis` / `sale_unit` / `warranty_days` | `20` | `0` | `char` |
| `sales_qty` / `sales_amt` | `90` | `2` | `dec` |
| `closing_stock_qty` | `91` | `11` | `dec` |
| `loss_qty` / `loss_amt` / `inv_qty` | `91` | `2` | `dec` |
| `order_qty` | `92` | `2` | `dec` |
| `receive_vendor_qty` / `receive_all_qty` | `92` | `2` | `dec` |
| `return_all_qty` | `92` | `2` | `dec` |
| `stock_qty` | `91` | `3` | `dec` |
| `opening_stock_qty` | `91` | `10` | `dec` |

biz_type groups:

| biz_type | Group |
| --- | --- |
| `10` | 店铺信息 / store |
| `11` | 分类信息 / category |
| `20` | 商品信息 / item |
| `90` | 销售数据 / sales |
| `91` | 库存数据 / inventory |
| `92` | 进货数据 / purchase |

## Pagination

- `pageIndex` starts at `0`.
- Each page returns up to 100 rows.
- Stop when the returned row count is less than 100.
- `totalResult` has been observed as always `0`; do not rely on it.
- Re-run `initData` + `businessData` before each page if the session report context is lost.

## Fresh Category Filter

Use category filter parameters:

```text
data_column_list=cat_id_01
compare1_list=1
value1_list=40,42
```

Expected data scope:

```text
40 = 现制加工品
42 = 日配生鲜
```

## FreshOS Output Files

| Data type | Filename | Content | Date column |
| --- | --- | --- | --- |
| base | `dabiaoge_stores_products_base.xlsx` | store-product mapping | no |
| sales | `dabiaoge_sales_daily.xlsx` | daily sales | yes |
| inventory_loss | `dabiaoge_inventory_loss_daily.xlsx` | daily closing stock + loss | yes |
| purchase_receipts | `dabiaoge_purchase_receipts_daily.xlsx` | daily order + receipt | yes |

For a 28-day run with 789 store-product rows:

```text
daily rows = 789 * 28 = 22092
```

## FreshOS-Compatible Headers

Use these exact output headers for current FreshOS importers:

sales:

```text
店铺编号, 店铺名称, 大分类编码, 商品编码, 商品名称, 日期, 销量, 销售额
```

inventory_loss:

```text
店铺编号, 店铺名称, 大分类编码, 商品编码, 商品名称, 日期, 库存数量（期末）, 报损数量, 报损金额, 盘盈盘亏数量
```

Important: `库存数量（期末）` must use full-width Chinese parentheses `（` and `）`, not half-width `(` and `)`.

purchase_receipts:

```text
店铺编号, 店铺名称, 大分类编码, 商品编码, 商品名称, 日期, 订货数量, 收货数量, 总收货数量, 总退货+调出数量
```

base:

```text
店铺编号, 店铺名称, 店铺状态, 大分类编码, 大分类名称, 中分类编码, 中分类名称, 商品编码, 商品名称, 销售单位, 保质期限(天)
```

## Script Guidance

The working exporter is the type=3 daily version of the Python requests script.

Do not commit a script containing real values for:

```text
USERNAME
PASSWORD
cookies
session IDs
tokens
```

If the script is committed later, it must read these from environment variables or server-side secrets, for example:

```text
DABIAOGE_USERNAME
DABIAOGE_PASSWORD
DABIAOGE_OUTPUT_DIR
```

Runtime parameters that commonly change:

1. Date range.
2. Field list and `biz_per_date`.
3. Category filter, usually `40,42`.
4. Output directory.

## Validation Standard

Before treating an export as FreshOS-ready, check:

1. 大分类编码 only contains `40` and `42`.
2. 门店覆盖 includes `10002`, `10003`, and `10008`.
3. Required fields have no empty values or only explicitly allowed empty values.
4. Numeric fields are not all zero.
5. Daily business files contain a `日期` column.
6. Daily row count equals `store-product row count * number of days`.
7. `库存数量（期末）` uses full-width Chinese parentheses.
8. FreshOS importers can parse the files:
   - `import_dabiaoge_base`
   - `import_dabiaoge_daily --report-type sales`
   - `import_dabiaoge_daily --report-type inventory_loss`
   - `import_dabiaoge_daily --report-type purchase_receipts`

Verified sample from the API-first type=3 path:

```text
base: stores=3, products=865, store_products=2595
sales: 22092 rows, 28 dates, stores=10002/10003/10008
inventory_loss: 22092 rows, 28 dates, stores=10002/10003/10008
purchase_receipts: 22092 rows, 28 dates, stores=10002/10003/10008
```

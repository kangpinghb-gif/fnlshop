---
name: dabiaoge
description: Use when working with the 盛和 A+ 数据分析系统 / 大表哥 custom reports, including logged-in browser navigation, report type switching, safe field selection, filtering, XLSX export, DOM/XHR extraction fallback, and mapping exported sales/inventory fields into FreshOS data samples. Do not store credentials or bypass login verification.
---

# 盛和 A+ 大表哥数据导出

## Safety Rules

- Do not store usernames, passwords, SMS codes, one-time codes, cookies, or session tokens in this skill or project files.
- Do not bypass CAPTCHA, verification code, MFA, SSO, or other access controls.
- Ask the user to complete password, CAPTCHA, SMS, QR-code, or MFA steps in the browser.
- If the user explicitly chooses Keychain-based login, retrieve the password from macOS Keychain only after user approval for that task.
- Prefer a temporary read-only account limited to viewing/exporting reports.
- Do not perform write actions such as price changes, order placement, inventory modification, permission changes, or deletion.
- Export only the data needed for the FreshOS task.

## Login Workflow

Supported login modes:

1. Manual login: open the login page and ask the user to enter credentials and verification manually.
2. Keychain-assisted login: read the password from macOS Keychain after user approval, fill username/password, then ask the user to complete CAPTCHA/SMS/MFA if present.

Default Keychain configuration:

- Service name: `freshos-dabiaoge`
- Account name: `kang`
- Password storage: macOS Keychain only, never Markdown or project files.

Keychain helper:

```bash
scripts/get_keychain_password.sh freshos-dabiaoge kang
```

Login steps:

1. Open the 盛和 A+ login page in the browser.
2. If using Keychain mode, request permission to read the password from Keychain, then fill username/password.
3. Ask the user to complete CAPTCHA, SMS, QR-code, or MFA manually when required.
4. Confirm successful login by checking that the page title or visible UI indicates the A+ analysis system.
5. Navigate to the 大表哥/custom report page after login.

Known pages:

- Login: `https://hljxz.info-plus.cn/KIT/homePage/login`
- 大表哥/custom report: `https://hljxz.info-plus.cn/KIT/homePage/main4`

## Page Structure

The system uses a frameset-style layout:

| Frame / Page | URL suffix | Purpose |
| --- | --- | --- |
| main/main1 | `/KIT/homePage/main1` | Top navigation |
| main4 | `/KIT/homePage/main4` | 大表哥 custom reports |
| sceneMenu | `/KIT/homePage/sceneMenu` | Scene menu |
| Info2 | `/KIT/homePage/Info2` | Native reports such as T3000 |

The 大表哥 page has three important regions:

1. Main category checkboxes, such as 店铺信息、分类信息、商品信息、销售数据.
2. Child field checkboxes, which are the specific report columns.
3. Data table, which displays selected columns.

Important rule: never click main category checkboxes. They may select too many fields and can be hard to reverse. Expand a category by clicking its title, then select only child field checkboxes.

## Report Type Switching

Switch report type by clicking `<li>` elements with `text` attributes. Use page JavaScript or jQuery click/trigger where normal browser clicks are unreliable.

Useful report types:

| Type | Name | Notes |
| --- | --- | --- |
| 1 | 期间查询报表 | Default single-period summary |
| 2 | 期间对比报表 | Compares two periods and adds difference/rate columns |
| 3 | 期间趋势报表 | Multiple-day trend, often one column per day |
| 5 | 今日实时报表 | Real-time report with different field names |
| 6 | 时段查询报表 | Time-slot analysis |
| 7 | 支付查询报表 | Payment analysis |

Example:

```javascript
var lis = document.querySelectorAll('li[text]');
for (var i = 0; i < lis.length; i++) {
  if (lis[i].getAttribute('text') === '今日实时报表') {
    if (window.jQuery) {
      jQuery(lis[i]).trigger('click');
    } else {
      lis[i].click();
    }
    break;
  }
}
```

## Date Setting

Date inputs may be readonly and may not respond to normal typing. Set dates through page JavaScript and dispatch events if needed.

For period comparison:

```javascript
$('#startTime1').val('2026/05/07');
$('#endTime1').val('2026/05/07');
$('#startTime2').val('2026/05/08');
$('#endTime2').val('2026/05/08');
```

## Field Selection

Prefer selecting fields by visible label or `data_column`, not by unstable DOM index.

Safe selection pattern:

```javascript
var targets = ['店铺名称', '商品编码', '商品名称', '销售额', '销量'];
var cbs = document.querySelectorAll('input[type="checkbox"]');

for (var i = 0; i < cbs.length; i++) {
  var labels = cbs[i].parentElement.querySelectorAll('label');
  for (var j = 0; j < labels.length; j++) {
    var text = labels[j].textContent.trim();
    if (targets.indexOf(text) !== -1 && !cbs[i].checked) {
      var item = cbs[i].closest('.item');
      if (item && typeof changeItemColorBox === 'function' && window.jQuery) {
        changeItemColorBox(jQuery(item));
      } else {
        cbs[i].click();
      }
      break;
    }
  }
}
```

Stable field identifiers:

| Category | Field | data_column |
| --- | --- | --- |
| 店铺信息 | 店铺名称 | `store_name` |
| 分类信息 | 大分类编码 | `cat_id_01` |
| 分类信息 | 大分类名称 | `cat_name_01` |
| 分类信息 | 中分类编码 | `cat_id_02` |
| 分类信息 | 中分类名称 | `cat_name_02` |
| 商品信息 | 商品编码 | `item_cd` |
| 商品信息 | 商品名称 | `item_name_dis` |
| 商品信息 | 售价 | `sale_price` |
| 销售数据 | 销售额 | `sales_amt` |
| 销售数据 | 销量 | `sales_qty` |
| 销售数据 | 成本金额 | `cost_amt` |
| 销售数据 | 毛利额 | `gross_amt` |
| 销售数据 | 毛利率 | `gross_rate` |
| 库存数据 | 报损金额 | `loss_amt` |
| 库存数据 | 库存金额（期初） | `opening_stock_amt` |
| 库存数据 | 库存金额（期末） | `closing_stock_amt` |
| 进货数据 | 总收货金额 | `receive_all_amt` |
| 进货数据 | 退货金额 | `return_vendor_amt` |

Additional FreshOS-relevant fields observed in 大表哥:

| Category | Field | data_column |
| --- | --- | --- |
| 店铺信息 | 店铺编号 | `store_id` |
| 店铺信息 | 店铺类型 | `store_type_desc` |
| 店铺信息 | 店铺状态 | `status_desc` |
| 店铺信息 | 营业区分 | `biz_type_desc` |
| 店铺信息 | 区域编码 | `zone_cd` |
| 分类信息 | 小分类编码 | `cat_id_03` |
| 分类信息 | 小分类名称 | `cat_name_03` |
| 供应商信息 | 供应商ID | `vendor_id` |
| 供应商信息 | 供应商名称 | `vendor_name` |
| 商品信息 | 商品条码 | `barcode` |
| 商品信息 | 规格 | `spec` |
| 商品信息 | 销售单位 | `sale_unit` |
| 商品信息 | 箱装数 | `order_pack_qty` |
| 商品信息 | 订货批量 | `order_batch_qty` |
| 商品信息 | 保质期限(天) | `warranty_days` |
| 商品信息 | 配送类型 | `delivery_type_name` |
| 商品信息 | 店铺订货标识 | `store_order_flg_desc` |
| 商品信息 | 店铺销售标识 | `store_sale_flg_desc` |
| 商品信息 | 近期日均销量 | `store_dms` |
| 商品信息 | 门店库存数量(昨日) | `store_stock_qty` |
| 商品信息 | 门店订货上限 | `store_upper_qty` |
| 商品信息 | 门店订货下限 | `store_lower_qty` |
| 库存数据 | 库存数量（期初） | `opening_stock_qty` |
| 库存数据 | 库存数量（期末） | `closing_stock_qty` |
| 库存数据 | 库存数量(日均) | `stock_qty` |
| 库存数据 | 报损数量(正值代表亏损) | `loss_qty` |
| 库存数据 | 盘盈盘亏数量 | `inv_qty` |
| 库存数据 | 周转天数 | `turnover_days_d` |
| 进货数据 | 订货数量 | `order_qty` |
| 进货数据 | 订货金额 | `order_amt` |
| 进货数据 | 收货数量 | `receive_vendor_qty` |
| 进货数据 | 总收货数量 | `receive_all_qty` |
| 进货数据 | 退货数量 | `return_vendor_qty` |
| 进货数据 | 总退货+调出数量 | `return_all_qty` |

今日实时报表 field differences:

| Business field | Period report type=1 | Real-time report type=5 |
| --- | --- | --- |
| 销售数量 | `sales_qty` | `sale_qty` |
| 销售金额 | `sales_amt` | `sale_amt` |
| 库存数量 | Period summary | `stock_qty` |
| 在途数量 | Not available | `on_order_qty` |

## Filtering

Use column-header filtering when report volume is too large. For FreshOS V1, only export 大分类编码 `40` and `42`.

Category codes:

| Code | Name |
| --- | --- |
| 01 | 冷冻 |
| 02 | 日配冷藏 |
| 03 | 常温乳品 |
| 04 | 酒 |
| 05 | 饮料 |
| 06 | 粮油副食 |
| 07-09 | 百货/日化 |
| 10 | 休闲零食 |
| 12 | 香烟 |
| 40 | 现制加工品 |
| 42 | 日配生鲜 |
| 44 | 特殊分类 |

Fresh category subcodes:

| Code | Name |
| --- | --- |
| 4201 + 4202 | 水果（预包装 + 散装） |
| 4203 + 4204 | 蔬菜（预包装 + 散装） |
| 4205 + 4206 | 鲜肉 |
| 4207 | 海鲜 |
| 4208 | 鲜蛋 |
| 4209 | 日配半加工 |

Column filter pattern:

```javascript
var ths = document.querySelectorAll('#customer_table_title th');
for (var i = 0; i < ths.length; i++) {
  if (ths[i].textContent.trim() === '大分类编码') {
    openCustomerDialog(ths[i]);
    break;
  }
}

var inputs = document.querySelectorAll('.customer_dialog_left input[type="text"]');
for (var i = 0; i < inputs.length; i++) {
  if (inputs[i].offsetParent !== null) {
    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(inputs[i], '40,42');
    inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
    break;
  }
}

var btns = document.querySelectorAll('.customer_button');
for (var i = 0; i < btns.length; i++) {
  if (btns[i].textContent.trim() === '确定' && btns[i].offsetParent !== null) {
    btns[i].click();
    break;
  }
}
```

## Query And Export

Use page functions where visible buttons are unreliable:

```javascript
customerSearchAll();
```

For export, capture the generated file path before triggering export:

```javascript
window._capturedFileUrl = null;
if (typeof downloadfile === 'function') {
  var originalDownloadfile = downloadfile;
  downloadfile = function (filePath) {
    window._capturedFileUrl = filePath;
    return originalDownloadfile.apply(this, arguments);
  };
}

exportByDownloadCenter();
```

Export notes:

- Keep exports to roughly 10 to 12 columns to avoid silent truncation.
- If the export dialog says the system is generating the file, wait.
- Closing the dialog may not cancel backend generation.
- If export fails, use DOM/XHR extraction fallback.

## Extraction Fallbacks

DOM table extraction:

```javascript
var t = document.querySelectorAll('table')[2];
var csvRows = [];
for (var r = 0; r < t.rows.length; r++) {
  var cells = [];
  for (var c = 0; c < t.rows[r].cells.length; c++) {
    cells.push(t.rows[r].cells[c].textContent.trim());
  }
  csvRows.push(cells.join('|'));
}
window._csvData = csvRows.join('\n');
```

XHR interception:

```javascript
window._capturedData = null;
var originalOpen = XMLHttpRequest.prototype.open;
var originalSend = XMLHttpRequest.prototype.send;

XMLHttpRequest.prototype.open = function (method, url) {
  this._url = url;
  return originalOpen.apply(this, arguments);
};

XMLHttpRequest.prototype.send = function (body) {
  var xhr = this;
  xhr.onload = function () {
    if (xhr._url && xhr._url.indexOf('getTableData') !== -1) {
      window._capturedData = JSON.parse(xhr.responseText);
    }
  };
  return originalSend.apply(this, arguments);
};

customerSearchAll();
```

Full-table interception:

```javascript
if (typeof initTableBodys === 'function') {
  var originalInitTableBodys = initTableBodys;
  window._allTableData = null;
  initTableBodys = function (data) {
    window._allTableData = data;
    return originalInitTableBodys.apply(this, arguments);
  };
}
customerSearchAll(1);
```

## FreshOS Data Mapping

When exporting for FreshOS V1, use these lean presets. Keep exports small; do not include fields that are not used by V1 ordering, inventory, or matching.

Default date range: last 30 days.

Default category filter: 大分类编码 in `40,42`. The system supports multi-select / multi-value filtering for these two categories.

Historical data source priority: use 大表哥 as the primary source for historical sales, inventory, loss, purchase, and receipt data. Order files are used for arrival date and actual daily arrival quantity.

### FreshOS Export Presets

#### Preset A: stores_products_base

Purpose: build `stores`, `products`, and `store_products` base mapping.

Report type: `期间查询报表`

Date range: one recent business day is enough.

Fields:

- 店铺编号
- 店铺名称
- 店铺状态
- 商品编码
- 商品名称
- 大分类编码
- 大分类名称
- 中分类编码
- 中分类名称
- 销售单位
- 保质期限(天)

Recommended output:

- `data_samples/dabiaoge_stores_products_base.xlsx`

#### Preset B: product_order_params

Purpose: get order constraints and store-product parameters.

Report type: `期间查询报表`

Date range: one recent business day is enough.

Fields:

- 店铺编号
- 店铺名称
- 商品编码
- 商品名称
- 箱装数
- 订货批量
- 店铺订货标识
- 近期日均销量
- 门店库存数量(昨日)

Recommended output:

- `data_samples/dabiaoge_product_order_params.xlsx`

#### Preset C: sales_daily

Purpose: build sales history and baseline forecast.

Report type: prefer `期间趋势报表` / 期间推移 when daily granularity is needed. Use `期间查询报表` only for period totals.

Date range: last 7-30 days.

Fields:

- 店铺编号
- 店铺名称
- 商品编码
- 商品名称
- 大分类编码
- 销量
- 销售额

Recommended output:

- `data_samples/dabiaoge_sales_daily.xlsx`

#### Preset D: inventory_loss_daily

Purpose: build inventory snapshots, loss summary, and stock risk signals.

Report type: `期间查询报表`

Date range: same as sales export if possible.

Fields:

- 店铺编号
- 店铺名称
- 商品编码
- 商品名称
- 库存数量（期末）
- 报损数量(正值代表亏损)
- 报损金额(正值代表亏损)
- 盘盈盘亏数量

Recommended output:

- `data_samples/dabiaoge_inventory_loss_daily.xlsx`

#### Preset E: purchase_receipts_daily

Purpose: build order/receipt summaries.

Report type: `期间查询报表`

Date range: same as sales export if possible.

Fields:

- 店铺编号
- 店铺名称
- 商品编码
- 商品名称
- 订货数量
- 收货数量
- 总收货数量
- 总退货+调出数量

Recommended output:

- `data_samples/dabiaoge_purchase_receipts_daily.xlsx`

#### Preset F: realtime_inventory

Purpose: capture current stock point-in-time.

Report type: `今日实时报表`

Validation: test this directly in 大表哥. If switching to 今日实时报表 is unstable, mark realtime inventory as pending and use `库存数量（期末）` or `门店库存数量(昨日)` temporarily.

Fields:

- 店铺编号
- 店铺名称
- 商品编码
- 商品名称
- 库存数量
- 在途数量

Recommended output:

- `data_samples/dabiaoge_realtime_inventory.xlsx`

### FreshOS Filters

Default FreshOS filter:

- 大分类编码 = `40` 现制加工品
- 大分类编码 = `42` 日配生鲜

Use one multi-value filter when possible. If the page does not apply `40,42` correctly, export `40` and `42` separately and merge locally.

Optional subcategory filters:

- 水果: 中分类编码 `4201` + `4202`
- 蔬菜: 中分类编码 `4203` + `4204`
- 鲜肉: 中分类编码 `4205` + `4206`
- 海鲜: 中分类编码 `4207`
- 鲜蛋: 中分类编码 `4208`
- 日配半加工: 中分类编码 `4209`

### FreshOS Field Mapping

For sales samples:

- 店铺名称
- 店铺编号
- 商品编码
- 商品名称
- 大分类编码
- 大分类名称
- 中分类编码
- 中分类名称
- 销售额
- 销量

For real-time inventory samples:

- 店铺编号
- 店铺名称
- 商品编码
- 商品名称
- 库存数量
- 在途数量

Suggested FreshOS file outputs:

- `data_samples/sales_records.xlsx`
- `data_samples/products.xlsx`
- `data_samples/stores.xlsx`
- `data_samples/inventory.xlsx`
- `data_samples/field_mapping.md`

### Export Workflow For FreshOS

1. Confirm user is logged in. If not, open login page and ask the user to complete verification.
2. Navigate to `/KIT/homePage/main4`.
3. Reset report fields using `customerReset()` if the current report has prior selections.
4. Set date range.
5. Select only the fields in one preset. Never click main category checkboxes.
6. Apply category filter: 大分类编码 in `40,42`.
7. Run `customerSearchAll()`.
8. Export with `exportByDownloadCenter()`.
9. Save or move exported file into `data_samples/` with the preset filename.
10. If export fails, use DOM/XHR fallback and save CSV/XLSX from extracted data.

## Known Traps

1. Do not click main category checkboxes.
2. Some inputs are readonly; normal typing may not work.
3. Visible 查询 buttons may be unreliable; use `customerSearchAll()`.
4. Export can silently truncate too many columns.
5. Category panels can be mutually exclusive when expanded, but selected fields remain.
6. Checkbox DOM indexes are unstable; use label text or `data_column`.
7. Browser sessions can expire; ask the user to log in again.
8. Gross margin rate can be a decimal, for example `0.0133` means `1.33%`.
9. Listed 售价 may be marked price, not actual transaction price; calculate actual average price as 销售额 / 销量 when needed.
10. Mid-month closing inventory amount may be zero before accounting close.

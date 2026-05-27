# FreshOS V1 数据库与导入设计

## 一、设计目标

本文件用于把 FreshOS V1 的数据需求落成可开发的数据表和导入规则。

V1只解决三件事：

1. 多门店商品、销售、库存、到货数据统一。
2. 基于实时库存、销售历史、到货数据生成订货建议。
3. 通过理论库存、实时库存、人工盘点修正值判断库存可信度。

V1暂不做：

- 复杂AI预测
- 自动动态定价
- 员工任务系统
- 供应商评分
- 批次精细化成本核算
- 报损原因分析

## 二、数据来源

### 1. 大表哥

大表哥是 V1 的历史经营数据主来源。

用于提供：

- 门店基础数据
- 商品基础数据
- 商品分类
- 销售历史
- 库存数据
- 报损数量/金额
- 订货/收货汇总
- 商品订货参数

筛选口径：

```text
大分类编码 = 40,42
40 = 现制加工品
42 = 日配生鲜
```

日期范围：

```text
最近30天
```

销售日粒度：

```text
如需要按日销售历史，使用大表哥期间趋势/期间推移导出。
```

### 2. 生鲜订单Excel

订单文件用于补充：

- 到货日期
- 当日到货值
- 订单商品名称
- 发货数量/净果数量/门店实收重量

当前支持两种格式：

- 水果订单标准明细格式
- 蔬菜供应商模板格式

### 3. 人工盘点修正

人工盘点不作为主要库存值，只作为库存修正值。

用于：

- 修正实时库存或理论库存
- 提升/降低库存可信度
- 记录异常库存纠偏

## 三、核心数据口径

### 1. 编码口径

| 项目 | 结论 |
| --- | --- |
| 商品编码是否全系统唯一 | 是 |
| 门店编码是否全系统唯一 | 是 |
| 门店编码和门店名称不一致 | 以门店名称为准 |
| 订单商品编码为空 | 按订单商品名称匹配 |

### 2. 单位口径

| 项目 | 结论 |
| --- | --- |
| 销售数量单位是否统一 | 是 |
| 称重商品单位 | 看销售单位 |
| 系统是否保留单位字段 | 是 |

### 3. 库存口径

| 项目 | 结论 |
| --- | --- |
| 库存数量是否允许负数 | 是 |
| 实时库存 | 大表哥时点库存 |
| 人工盘点数量 | 修正值，不是主要库存值 |

库存主口径优先级：

```text
实时库存快照 > 期末库存 > 理论库存
```

人工盘点数量只作为修正值，叠加到当前主库存，不作为独立库存来源。

### 4. 到货口径

| 项目 | 结论 |
| --- | --- |
| 到货日期 | 订单导入值 |
| 入库数量 | 当日到货值 |
| 历史收货数据 | 以大表哥为主 |
| 到货数量大于订货数量 | 允许 |

入库数量取值优先级：

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

### 5. 配送口径

```text
V1默认每日配送
delivery_cycle_days = 1
```

不维护：

- 默认配送日
- 门店订货负责人

## 四、V1数据表

## 1. 门店表：stores

用途：记录门店基础信息。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_code | varchar | 是 | 大表哥店铺编号 | 门店唯一编码 |
| store_name | varchar | 是 | 大表哥店铺名称 | 门店名称 |
| store_status | varchar | 否 | 大表哥店铺状态 | 正常/关闭等 |
| store_type | varchar | 否 | 大表哥店铺类型 | 可后续补充 |
| delivery_cycle_days | numeric | 是 | 系统默认 | V1固定为1 |
| is_active | boolean | 是 | 系统生成 | 是否启用 |
| created_at | timestamp | 是 | 系统生成 | 创建时间 |
| updated_at | timestamp | 是 | 系统生成 | 更新时间 |

唯一约束：

```text
unique(store_code)
```

导入规则：

- 优先使用 `store_code` 匹配。
- 如果订单文件中 `store_code` 和 `store_name` 不一致，以 `store_name` 匹配为准。
- 编码和名称不一致时写入导入异常表。

## 2. 商品表：products

用途：记录系统统一商品档案。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| product_code | varchar | 是 | 大表哥商品编码 | 商品唯一编码 |
| product_name | varchar | 是 | 大表哥商品名称 | 商品名称 |
| barcode | varchar | 否 | 大表哥商品条码 | 辅助识别 |
| cat_id_01 | varchar | 是 | 大表哥大分类编码 | 只保留40/42 |
| cat_name_01 | varchar | 是 | 大表哥大分类名称 | 现制加工品/日配生鲜 |
| cat_id_02 | varchar | 否 | 大表哥中分类编码 | 商品细分 |
| cat_name_02 | varchar | 否 | 大表哥中分类名称 | 商品细分 |
| sale_unit | varchar | 是 | 大表哥销售单位 | kg/个/盒等 |
| fresh_attribute | varchar | 否 | 网上查询/人工维护 | 商品属性，如叶菜/根茎/鲜切/普通水果/耐储水果 |
| storage_condition | varchar | 否 | 网上查询/人工维护 | 常温/冷藏/冷冻/避光等 |
| shelf_life_days | numeric | 否 | 大表哥保质期限(天) | 用于剩余寿命计算 |
| sellable_days | numeric | 否 | 网上查询/人工维护 | V1订货计算采用的可售天数 |
| sellable_days_source | varchar | 否 | 系统生成 | online/manual/category_default/shelf_life/default |
| sellable_days_reference | text | 否 | 网上查询 | 可售天数参考来源或备注 |
| sellable_days_review_status | varchar | 是 | 系统生成 | pending/confirmed/rejected |
| is_active | boolean | 是 | 系统生成 | 是否启用 |
| created_at | timestamp | 是 | 系统生成 | 创建时间 |
| updated_at | timestamp | 是 | 系统生成 | 更新时间 |

唯一约束：

```text
unique(product_code)
```

导入规则：

- 只导入大分类编码为 `40` 或 `42` 的商品。
- 商品编码为空的订单商品不直接写入 `products`，先进入商品匹配表。
- 商品名称前缀如 `Z-`、`C-`、`JPZ-` 可用于匹配时清洗，但不直接覆盖原始名称。
- `sellable_days` 按商品属性写入系统，初始值可通过网上公开资料查询生成。
- 网上查询得到的 `sellable_days` 必须记录参考来源，并默认标记为 `pending`，经人工确认后改为 `confirmed`。
- `sellable_days` 为空时使用 `shelf_life_days`；仍为空时使用品类默认值；仍无法判断时按1天处理并写入风险提示。

## 3. 门店商品表：store_products

用途：记录门店和商品的经营关系及订货参数。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| store_order_status | varchar | 否 | 大表哥店铺订货标识 | 是否可订 |
| store_sale_status | varchar | 否 | 大表哥店铺销售标识 | 是否可销售 |
| is_orderable | boolean | 是 | 系统计算/人工维护 | 是否允许订货 |
| is_sellable | boolean | 是 | 系统计算/人工维护 | 是否允许销售 |
| package_size | numeric | 否 | 大表哥箱装数 | 包装规格 |
| order_batch_qty | numeric | 否 | 大表哥订货批量 | MOQ/订货批量 |
| min_order_qty | numeric | 否 | 大表哥/人工维护 | 最小订货量 |
| safety_stock_days | numeric | 是 | 系统默认/人工维护 | 安全库存天数，V1默认1 |
| sellable_days_override | numeric | 否 | 人工维护 | 门店商品可售天数覆盖值 |
| recent_daily_sales | numeric | 否 | 大表哥近期日均销量 | 基础预测参考 |
| store_stock_qty_yesterday | numeric | 否 | 大表哥门店库存数量(昨日) | 临时库存参考 |
| is_active | boolean | 是 | 系统生成 | 是否启用 |
| created_at | timestamp | 是 | 系统生成 | 创建时间 |
| updated_at | timestamp | 是 | 系统生成 | 更新时间 |

唯一约束：

```text
unique(store_id, product_id)
```

导入规则：

- 从大表哥商品基础和订货参数导入。
- 如果同一门店商品重复出现，保留最新导入值。
- `is_orderable` 优先根据大表哥店铺订货标识生成，可人工关闭。
- `is_sellable` 优先根据大表哥店铺销售标识生成，可人工关闭。
- `safety_stock_days` V1默认填1，后续按品类或门店商品人工调整。
- `sellable_days_override` 为空时使用 `products.sellable_days`。
- `min_order_qty` 为空时按0处理。
- `order_batch_qty` 为空或小于等于0时，不做批量取整。

## 4. 销售日汇总表：sales_daily

用途：记录门店商品每日销售，用于基础预测和动销判断。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| business_date | date | 是 | 大表哥期间趋势/期间推移 | 营业日期 |
| sales_quantity | numeric | 是 | 大表哥销量 | 当日销量 |
| sales_amount | numeric | 是 | 大表哥销售额 | 当日销售额 |
| unit | varchar | 是 | products.sale_unit | 单位 |
| source_file | varchar | 否 | 导入文件 | 来源文件 |
| imported_at | timestamp | 是 | 系统生成 | 导入时间 |

唯一约束：

```text
unique(store_id, product_id, business_date)
```

导入规则：

- 历史销售以大表哥为主。
- 如果原始数据同一天同店同商品有多条，先按日汇总后写入本表。
- 如果重新导入同一天数据，覆盖旧值或按导入批次重算。

## 5. 库存快照表：inventory_snapshots

用途：记录实时库存或大表哥库存时点数据。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| snapshot_time | timestamp | 是 | 大表哥导出时间 | 库存时点 |
| business_date | date | 是 | 系统生成 | 营业日期 |
| inventory_quantity | numeric | 是 | 大表哥实时库存/期末库存 | 库存数量 |
| inventory_source | varchar | 是 | 系统生成 | realtime/closing/yesterday |
| unit | varchar | 是 | products.sale_unit | 单位 |
| source_file | varchar | 否 | 导入文件 | 来源文件 |
| imported_at | timestamp | 是 | 系统生成 | 导入时间 |

索引建议：

```text
index(store_id, product_id, snapshot_time)
index(business_date)
```

导入规则：

- 实时库存按时点库存处理，必须记录 `snapshot_time`。
- 库存允许为负数。
- 负库存不改为0，但写入异常表。

## 6. 库存损耗日汇总表：inventory_loss_daily

用途：记录库存、报损、盘盈盘亏的日汇总数据。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| business_date | date | 是 | 大表哥日期 | 营业日期 |
| closing_stock_qty | numeric | 否 | 大表哥库存数量（期末） | 期末库存 |
| loss_quantity | numeric | 否 | 大表哥报损数量 | 报损数量 |
| loss_amount | numeric | 否 | 大表哥报损金额 | 报损金额 |
| inventory_difference_qty | numeric | 否 | 大表哥盘盈盘亏数量 | 库存差异 |
| unit | varchar | 是 | products.sale_unit | 单位 |
| source_file | varchar | 否 | 导入文件 | 来源文件 |
| imported_at | timestamp | 是 | 系统生成 | 导入时间 |

唯一约束：

```text
unique(store_id, product_id, business_date)
```

导入规则：

- 报损原因 V1 暂时忽略。
- 报损数量和金额用于理论库存和损耗判断。
- 盘盈盘亏数量用于库存可信度。

## 7. 订货收货日汇总表：purchase_receipts_daily

用途：记录大表哥历史订货、收货、退货汇总。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| business_date | date | 是 | 大表哥日期 | 营业日期 |
| order_quantity | numeric | 否 | 大表哥订货数量 | 订货数量 |
| receive_quantity | numeric | 否 | 大表哥收货数量 | 收货数量 |
| total_receive_quantity | numeric | 否 | 大表哥总收货数量 | 总收货数量 |
| total_return_quantity | numeric | 否 | 大表哥总退货+调出数量 | 退货/调出数量 |
| unit | varchar | 是 | products.sale_unit | 单位 |
| source_file | varchar | 否 | 导入文件 | 来源文件 |
| imported_at | timestamp | 是 | 系统生成 | 导入时间 |

唯一约束：

```text
unique(store_id, product_id, business_date)
```

导入规则：

- 历史订货、收货以大表哥为主。
- 到货日期和当日到货值以订单导入表为准。
- 大表哥收货数据用于历史复盘和校验。

## 8. 生鲜订单导入表：fresh_order_imports

用途：承接水果、蔬菜等生鲜订单文件，记录到货日期和当日到货值。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| source_file_name | varchar | 是 | 文件名 | 来源文件 |
| source_sheet_name | varchar | 是 | Excel sheet | 来源sheet |
| source_format | varchar | 是 | 系统识别 | fruit_standard / vegetable_supplier |
| supplier_code | varchar | 否 | 订单文件 | 供应商编码 |
| supplier_name | varchar | 否 | 订单文件 | 供应商名称 |
| store_id | uuid / bigint | 否 | 匹配结果 | 门店ID |
| store_name_raw | varchar | 是 | 订单文件 | 原始门店名称 |
| product_id | uuid / bigint | 否 | 匹配结果 | 商品ID |
| product_name_raw | varchar | 是 | 订单文件 | 订单商品名称 |
| order_date | date | 否 | 文件名/人工 | 订单日期 |
| arrival_date | date | 是 | 文件名/表内发货日期 | 到货日期，V1同时作为生产日期口径 |
| ordered_quantity | numeric | 否 | 订单文件 | 订货数量 |
| arrival_quantity | numeric | 是 | 系统计算 | 当日到货值 |
| gross_quantity | numeric | 否 | 订单文件 | 毛重 |
| tare_quantity | numeric | 否 | 订单文件 | 皮重/筐皮 |
| received_quantity | numeric | 否 | 订单文件 | 门店实收重量 |
| unit | varchar | 是 | 系统默认/订单 | 默认kg |
| match_status | varchar | 是 | 系统生成 | matched/pending/failed |
| remark | text | 否 | 订单文件/系统 | 备注 |
| raw_row_number | integer | 是 | Excel行号 | 来源行 |
| imported_at | timestamp | 是 | 系统生成 | 导入时间 |

索引建议：

```text
index(arrival_date)
index(store_id, product_id, arrival_date)
index(match_status)
```

导入规则：

- 商品匹配按订单商品名称进行。
- 门店编码和门店名称不一致时，以门店名称为准。
- 入库数量使用 `arrival_quantity`。
- 到货数量大于订货数量允许，但写入异常表。

## 9. 人工盘点修正表：stock_count_adjustments

用途：记录人工盘点修正值。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| count_time | timestamp | 是 | 人工录入 | 盘点时间 |
| business_date | date | 是 | 系统生成 | 营业日期 |
| adjusted_quantity | numeric | 是 | 人工录入 | 人工盘点修正值 |
| unit | varchar | 是 | products.sale_unit | 单位 |
| count_type | varchar | 否 | 人工录入 | full/random/risk_triggered |
| remark | text | 否 | 人工录入 | 备注 |
| created_at | timestamp | 是 | 系统生成 | 创建时间 |

索引建议：

```text
index(store_id, product_id, count_time)
```

导入规则：

- 人工盘点数量只作为修正值。
- 不直接替代实时库存主口径。
- 最近一次有效修正值参与库存可信度计算。

## 10. 导入异常表：import_exceptions

用途：记录导入过程中的非阻断异常。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| source_file_name | varchar | 是 | 导入文件 | 来源文件 |
| source_table | varchar | 是 | 系统生成 | 来源表/导入类型 |
| raw_row_number | integer | 否 | 导入文件 | 原始行号 |
| exception_type | varchar | 是 | 系统生成 | 异常类型 |
| exception_message | text | 是 | 系统生成 | 异常说明 |
| raw_payload | json | 否 | 系统生成 | 原始数据 |
| status | varchar | 是 | 系统生成 | open/resolved/ignored |
| created_at | timestamp | 是 | 系统生成 | 创建时间 |

常见异常：

| 异常类型 | 说明 |
| --- | --- |
| unmatched_store | 门店无法匹配 |
| store_code_name_conflict | 门店编码和名称不一致 |
| unmatched_product | 商品无法匹配 |
| missing_product_code | 商品编码为空 |
| missing_arrival_date | 到货日期缺失 |
| missing_arrival_quantity | 到货数量缺失 |
| quantity_greater_than_order | 到货数量大于订货数量 |
| negative_inventory | 库存为负 |
| unit_conflict | 同一商品出现多个单位 |

## 11. 库存口径计算表：inventory_positions

用途：按门店、商品、日期沉淀 FreshOS 计算后的库存口径，用于订货建议和库存风险判断。

本表不是外部导入表，由系统每日或每次导入后重算。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| business_date | date | 是 | 系统生成 | 营业日期 |
| realtime_inventory_qty | numeric | 否 | inventory_snapshots | 最新实时库存 |
| closing_inventory_qty | numeric | 否 | inventory_loss_daily | 当日期末库存 |
| theoretical_inventory_qty | numeric | 否 | 系统计算 | 理论库存 |
| manual_adjustment_qty | numeric | 否 | stock_count_adjustments | 最近有效人工修正值 |
| corrected_inventory_qty | numeric | 是 | 系统计算 | 修正后主库存 |
| inventory_confidence | varchar | 是 | 系统计算 | high/medium/low |
| inventory_source | varchar | 是 | 系统计算 | realtime/theoretical/closing/yesterday |
| unit | varchar | 是 | products.sale_unit | 单位 |
| calculated_at | timestamp | 是 | 系统生成 | 计算时间 |

唯一约束：

```text
unique(store_id, product_id, business_date)
```

计算规则：

- 优先使用最新实时库存快照作为主库存。
- 没有实时库存时，使用当日期末库存。
- 没有期末库存时，使用理论库存。
- 人工盘点修正值只作为修正项，不直接覆盖主库存。
- 库存允许为负数，负数不改为0。

## 12. 库存年龄计算表：inventory_age_batches

用途：按门店、商品、到货日期沉淀 FreshOS 估算的库存年龄和可售状态，用于可卖库存、临期库存、积压风险判断。

本表不是外部导入表，也不代表真实物理批次。V1使用“计算批次”：

```text
同一门店 + 同一商品 + 同一到货日期 = 一个计算批次
```

如果同一天同门店同商品有多条订单或收货记录，数量合并为同一个计算批次，原始明细仍保留在 `fresh_order_imports`。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| arrival_date | date | 是 | fresh_order_imports | 到货日期，V1作为生产日期等价口径 |
| batch_quantity | numeric | 是 | fresh_order_imports | 该计算批次到货数量 |
| consumed_quantity | numeric | 是 | 系统计算 | FIFO估算已消耗数量 |
| remaining_quantity | numeric | 是 | 系统计算 | FIFO估算剩余数量 |
| sellable_days | numeric | 是 | store_products/products | 可售天数 |
| expiry_date | date | 是 | 系统计算 | 预计下架日 |
| remaining_sellable_days | numeric | 是 | 系统计算 | 剩余可售天数 |
| batch_status | varchar | 是 | 系统计算 | sellable/near_expiry/expired |
| unit | varchar | 是 | products.sale_unit | 单位 |
| calculated_at | timestamp | 是 | 系统生成 | 计算时间 |

唯一约束：

```text
unique(store_id, product_id, arrival_date)
```

计算规则：

- `arrival_date` 在 V1 中视为生产日期等价口径。
- 批次消耗使用 FIFO 估算：销售优先扣减最早到货批次。
- `expiry_date = arrival_date + sellable_days`。
- `remaining_sellable_days > 1` 时，状态为 `sellable`。
- `remaining_sellable_days <= 1` 且 `remaining_sellable_days > 0` 时，状态为 `near_expiry`。
- `remaining_sellable_days <= 0` 时，状态为 `expired`。

## 13. 销量预测表：sales_forecasts

用途：记录门店商品每日预测销量，用于订货建议。

本表不是外部导入表，由系统根据销售历史计算。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| forecast_date | date | 是 | 系统生成 | 预测日期 |
| forecast_quantity | numeric | 是 | 系统计算 | 预测销量 |
| forecast_method | varchar | 是 | 系统生成 | moving_average_7d / moving_average_14d / fallback_recent_daily_sales |
| sales_days_used | integer | 是 | 系统计算 | 实际参与计算的销售天数 |
| recent_daily_sales | numeric | 否 | store_products/sales_daily | 参考日均销量 |
| unit | varchar | 是 | products.sale_unit | 单位 |
| calculated_at | timestamp | 是 | 系统生成 | 计算时间 |

唯一约束：

```text
unique(store_id, product_id, forecast_date)
```

计算规则：

- V1默认使用最近7天有效销售日均销量。
- 最近7天销售数据不足3天时，使用最近14天有效销售日均销量。
- 最近14天仍不足3天时，使用 `store_products.recent_daily_sales`。
- 仍无可用数据时，预测销量为0，并可写入风险提示。

## 14. 订货建议表：order_suggestions

用途：记录 FreshOS 计算出的门店商品订货建议。

本表不是外部导入表，由系统根据库存口径、销量预测、到货、订货参数计算。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| suggestion_date | date | 是 | 系统生成 | 建议日期 |
| arrival_date | date | 是 | 系统生成/人工选择 | 预计到货日期 |
| forecast_quantity | numeric | 是 | sales_forecasts | 预测销量 |
| corrected_inventory_qty | numeric | 是 | inventory_positions | 修正后主库存 |
| sellable_inventory_qty | numeric | 否 | inventory_age_batches | 预计可卖库存 |
| overstock_qty | numeric | 否 | inventory_age_batches | 预计积压库存 |
| safety_stock_qty | numeric | 是 | 系统计算 | 安全库存数量 |
| pending_arrival_qty | numeric | 是 | fresh_order_imports | 已订/已发未到数量，V1可先为0 |
| raw_suggested_qty | numeric | 是 | 系统计算 | 未取整建议量 |
| suggested_order_qty | numeric | 是 | 系统计算 | 最终建议订货量 |
| order_batch_qty | numeric | 否 | store_products | 订货批量 |
| min_order_qty | numeric | 否 | store_products | 最小订货量 |
| suggestion_reason | text | 否 | 系统生成 | 建议原因 |
| status | varchar | 是 | 系统生成 | draft/confirmed/ignored/exported |
| unit | varchar | 是 | products.sale_unit | 单位 |
| calculated_at | timestamp | 是 | 系统生成 | 计算时间 |

唯一约束：

```text
unique(store_id, product_id, suggestion_date, arrival_date)
```

计算规则：

- 不可订货商品 `is_orderable = false` 时，建议订货量为0。
- 不可销售商品 `is_sellable = false` 时，建议订货量为0。
- 可卖库存数据不足时，使用修正后主库存计算订货建议。
- 可卖库存明显低于修正后主库存时，写入库存风险，V1不自动丢弃账面库存。
- 安全库存数量 = 预测销量 × 安全库存天数。
- 原始建议量 = 预测销量 + 安全库存数量 - 修正后主库存 - 已订未到数量。
- 原始建议量小于0时，按0处理。
- 如果有最小订货量，且原始建议量大于0但小于最小订货量，按最小订货量处理。
- 如果有订货批量，最终建议量向上取整到订货批量。

## 15. 库存风险表：inventory_risks

用途：记录系统识别出的库存和订货风险，供门店或总部复核。

本表不是外部导入表，由系统根据销售、库存、损耗、订货建议计算。

| 字段名 | 类型建议 | 必填 | 来源 | 说明 |
| --- | --- | --- | --- | --- |
| id | uuid / bigint | 是 | 系统生成 | 主键 |
| store_id | uuid / bigint | 是 | stores | 门店ID |
| product_id | uuid / bigint | 是 | products | 商品ID |
| business_date | date | 是 | 系统生成 | 营业日期 |
| risk_type | varchar | 是 | 系统计算 | stockout/overstock/near_expiry/expired/negative_inventory/no_sales/high_loss/data_missing |
| risk_level | varchar | 是 | 系统计算 | high/medium/low |
| risk_message | text | 是 | 系统生成 | 风险说明 |
| related_quantity | numeric | 否 | 系统计算 | 相关数量 |
| status | varchar | 是 | 系统生成 | open/resolved/ignored |
| calculated_at | timestamp | 是 | 系统生成 | 计算时间 |

索引建议：

```text
index(store_id, product_id, business_date)
index(risk_type, risk_level)
```

V1风险规则：

- 修正库存小于0：`negative_inventory`，高风险。
- 修正库存小于预测销量：`stockout`，高风险。
- 修正库存小于预测销量 + 安全库存数量：`stockout`，中风险。
- 修正库存大于预测销量 × 3，且商品仍有销量：`overstock`，中风险。
- 计算批次剩余可售天数小于等于1天且仍有库存：`near_expiry`，中风险。
- 计算批次已超过可售天数且仍有库存：`expired`，高风险。
- 连续7天无销量但库存大于0：`no_sales`，中风险。
- 报损数量明显高于近期日均销量：`high_loss`，中风险。
- 缺少销售、库存或商品参数：`data_missing`，低/中风险。

## 五、导入流程

### 1. 大表哥导入流程

```text
导出大表哥文件
  ↓
识别导出类型
  ↓
校验字段
  ↓
过滤大分类 40/42
  ↓
匹配门店
  ↓
匹配商品
  ↓
写入对应日汇总表
  ↓
记录异常
```

### 2. 订单导入流程

```text
上传订单Excel
  ↓
识别订单格式
  ↓
解析供应商、门店、到货日期
  ↓
解析商品明细
  ↓
按订单商品名称匹配商品
  ↓
按门店名称匹配门店
  ↓
计算 arrival_quantity
  ↓
写入 fresh_order_imports
  ↓
记录异常
```

### 3. 人工盘点修正导入流程

```text
上传盘点修正表
  ↓
匹配门店
  ↓
匹配商品
  ↓
写入 stock_count_adjustments
  ↓
参与库存可信度计算
```

## 六、核心计算用数据

### 1. 计算顺序

V1按以下顺序计算：

```text
导入原始数据
  ↓
计算 inventory_positions
  ↓
计算 inventory_age_batches
  ↓
计算 sales_forecasts
  ↓
计算 order_suggestions
  ↓
计算 inventory_risks
```

### 2. 理论库存

```text
理论库存 =
上一时点修正库存
+ 当日到货数量
- 当日销售数量
- 当日报损数量
```

字段来源：

| 数据 | 来源表 |
| --- | --- |
| 上一时点修正库存 | 库存计算结果 |
| 当日到货数量 | fresh_order_imports.arrival_quantity |
| 当日销售数量 | sales_daily.sales_quantity |
| 当日报损数量 | inventory_loss_daily.loss_quantity |

### 3. 修正后主库存

```text
当前主库存 = 最新实时库存快照
```

如果实时库存暂时不可用：

```text
当前主库存 = 最新期末库存 或 门店库存数量(昨日)
```

```text
修正后主库存 = 当前主库存 + 最近有效人工盘点修正值
```

如果没有人工盘点修正值：

```text
修正后主库存 = 当前主库存
```

### 4. 销量预测

```text
预测销量 = 最近7天有效销售日均销量
```

回退规则：

```text
最近7天有效销售天数不足3天
  ↓
最近14天有效销售日均销量
  ↓
store_products.recent_daily_sales
  ↓
0
```

### 5. 安全库存

```text
安全库存数量 = 预测销量 × safety_stock_days
```

V1默认：

```text
safety_stock_days = 1
```

### 6. 在架期和计算批次

V1不做真实物理批次，先做计算批次：

```text
计算批次 = 同一门店 + 同一商品 + 同一到货日期
```

同一天同门店同商品多条订单或收货记录，合并为一个计算批次。

```text
可售天数 = store_products.sellable_days_override
```

如果门店商品没有覆盖值：

```text
可售天数 = products.sellable_days
```

如果商品没有维护可售天数：

```text
可售天数 = products.shelf_life_days
```

仍为空时：

```text
可售天数 = 品类默认值
```

仍无法判断时：

```text
可售天数 = 1
```

预计下架日：

```text
expiry_date = arrival_date + sellable_days
```

批次消耗规则：

```text
销售优先扣减最早到货批次
```

### 7. 可卖库存和积压库存

V1使用估算口径，不作为财务库存。

```text
预计可卖库存 = 状态为 sellable 或 near_expiry 的计算批次剩余数量之和
```

```text
预计过期库存 = 状态为 expired 的计算批次剩余数量之和
```

```text
预计有效期内可消化数量 = 预测销量 × 剩余可售天数
```

```text
预计积压库存 = max(计算批次剩余数量 - 预计有效期内可消化数量, 0)
```

积压库存按每个计算批次分别计算后汇总，避免不同到货日期的剩余可售天数混在一起。

如果没有到货批次数据：

```text
预计可卖库存 = 空
预计积压库存 = 空
```

订货建议仍以修正后主库存为主，库存年龄只做风险提示和辅助判断。

### 8. 订货建议

```text
原始建议量 =
预测销量
+ 安全库存数量
- 修正后主库存
- 已订未到数量
```

V1初期如果无法准确取得已订未到：

```text
已订未到数量 = 0
```

取整规则：

```text
原始建议量小于0 → 0
有最小订货量 → 不低于 min_order_qty
有订货批量 → 向上取整到 order_batch_qty
```

### 9. 库存可信度

影响因素：

- 实时库存与理论库存差异
- 是否存在负库存
- 最近人工盘点修正时间
- 盘盈盘亏数量
- 报损数量是否异常

V1先使用简单分级：

| 等级 | 判断规则 |
| --- | --- |
| high | 有实时库存，且与理论库存差异不大 |
| medium | 无实时库存，但有期末库存或近期人工修正 |
| low | 只有理论库存、库存为负、或关键数据缺失 |

### 10. 风险判断

V1先输出风险提示，不自动处理库存。

| 风险 | 判断规则 |
| --- | --- |
| 缺货高风险 | 修正后主库存 < 预测销量 |
| 缺货中风险 | 修正后主库存 < 预测销量 + 安全库存数量 |
| 负库存 | 修正后主库存 < 0 |
| 积压 | 修正后主库存 > 预测销量 × 3 |
| 临期 | 计算批次剩余可售天数 <= 1 且剩余数量 > 0 |
| 过期 | 计算批次剩余可售天数 <= 0 且剩余数量 > 0 |
| 滞销 | 连续7天无销量且库存大于0 |
| 高损耗 | 报损数量明显高于近期日均销量 |
| 数据缺失 | 缺少销售、库存或门店商品参数 |

## 七、下一步开发任务

1. 根据本文件创建数据库 schema。
2. 开发基础导入解析器：
   - 大表哥导入解析器
   - 水果订单解析器
   - 蔬菜订单解析器
   - 人工盘点修正导入
3. 开发门店和商品匹配逻辑。
4. 建立商品属性和可售天数基础资料：
   - 按商品名称查询网上公开资料
   - 写入 `fresh_attribute`、`storage_condition`、`sellable_days`
   - 保留 `sellable_days_reference`
   - 初始状态为 `pending`，人工确认后改为 `confirmed`
5. 开发计算任务：
   - 库存口径计算 `inventory_positions`
   - 库存年龄计算 `inventory_age_batches`
   - 销量预测计算 `sales_forecasts`
   - 订货建议计算 `order_suggestions`
   - 库存风险计算 `inventory_risks`
6. 开发最小页面：
   - 导入页面
   - 导入异常处理页面
   - 订货建议页面
   - 库存风险页面
7. 用最近30天大表哥数据和订单样本跑通一条完整链路。

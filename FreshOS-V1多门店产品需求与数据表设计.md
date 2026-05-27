# FreshOS V1 多门店产品需求与数据表设计

## 一、V1定位

FreshOS V1的目标不是完整AI经营系统，而是先跑通多门店的库存经营闭环。

V1核心定位：

```text
多门店商品数据统一
  ↓
销售、库存、入库、报损数据汇总
  ↓
计算理论库存与库存可信度
  ↓
生成订货建议
  ↓
识别库存风险
  ↓
门店确认、修改、执行
  ↓
结果回收
```

## 二、V1适用范围

### 使用对象

- 总部运营
- 采购负责人
- 区域督导
- 门店店长
- 门店生鲜主管

### 门店范围

V1支持多个门店，但建议第一阶段先选择：

- 3到5家门店试点
- 每家门店商品结构相似
- 使用同一套ERP或POS数据源
- 有稳定的销售、库存、采购、报损数据

### 商品范围

建议先选择1到3个生鲜品类试点，例如：

- 叶菜
- 水果
- 鲜奶
- 肉禽
- 水产

不建议V1一开始覆盖全部商品。

## 三、V1核心功能

### 1. 多门店管理

系统需要支持：

- 门店基础信息维护
- 门店分组
- 门店营业状态
- 门店订货规则差异
- 门店安全库存差异
- 门店配送周期差异

### 2. 商品主数据管理

系统需要支持：

- 总部统一商品档案
- 不同门店可售商品差异
- 不同门店安全库存差异
- 不同门店订货规格差异

V1先不管理复杂商品属性，例如品牌、产地、等级、供应商权重、价格体系等。只有真正影响库存、订货、风险判断的字段才保留。

### 3. 数据导入

V1建议先支持文件导入和数据库/API接入二选一。

最低要求：

- 每日销售数据
- 当前ERP库存
- 入库数据
- 报损数据
- 人工盘点数据

### 4. 库存可信度计算

每个门店、每个商品都需要独立计算库存可信度。

示例：

| 门店 | 商品 | ERP库存 | 理论库存 | 盘点库存 | 可信度 |
| --- | --- | ---: | ---: | ---: | ---: |
| A店 | 香菜 | 12kg | 8kg | 7kg | 45% |
| B店 | 土豆 | 80kg | 78kg | 79kg | 94% |

### 5. 订货建议

系统按“门店 + 商品”生成订货建议。

基础公式：

```text
建议订货量 = 预测销量 + 安全库存 - 修正库存
```

V1可增加：

```text
最终订货量 =
建议订货量
× 简单损耗修正系数
```

然后根据MOQ、包装规格、整箱规则进行圆整。

### 6. 风险提醒

V1至少支持以下风险：

- 缺货风险
- 高库存风险
- 库存可信度低
- 临期风险
- 滞销风险

### 7. 人工修改与结果回收

系统建议必须允许店长或采购修改。

必须记录：

- 系统建议值
- 人工修改值
- 修改原因
- 最终确认值
- 实际执行结果
- 次日销售结果
- 次日库存结果

## 四、核心数据表字段要求

以下为V1建议数据表。字段类型仅作开发建议，后续可按实际技术栈调整。

## 1. 门店表：stores

用于记录门店基础信息。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 门店ID |
| store_code | varchar | 是 | 门店编码，对接ERP/POS |
| store_name | varchar | 是 | 门店名称 |
| store_type | varchar | 否 | 门店类型，如社区店、商超店、仓店 |
| region_id | bigint / uuid | 否 | 区域ID |
| region_name | varchar | 否 | 区域名称 |
| address | varchar | 否 | 门店地址 |
| city | varchar | 否 | 城市 |
| district | varchar | 否 | 区县 |
| business_status | varchar | 是 | 营业状态：open/closed/suspended |
| opening_date | date | 否 | 开业日期 |
| business_hours | json | 否 | 营业时间 |
| default_delivery_cycle_days | numeric | 否 | 默认配送周期 |
| created_at | timestamp | 是 | 创建时间 |
| updated_at | timestamp | 是 | 更新时间 |

## 2. 商品主表：products

用于记录总部统一商品档案。V1只保留最基础字段，避免商品资料维护过重。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 商品ID |
| product_code | varchar | 是 | 商品编码 |
| product_name | varchar | 是 | 商品名称 |
| category_name | varchar | 否 | 分类名称 |
| unit | varchar | 是 | 基础单位，如kg、袋、盒、个 |
| shelf_life_days | numeric | 否 | 保鲜期天数 |
| is_weighing_item | boolean | 否 | 是否称重商品 |
| is_active | boolean | 是 | 是否启用 |
| created_at | timestamp | 是 | 创建时间 |
| updated_at | timestamp | 是 | 更新时间 |

暂时移除的后期字段：

- 商品类型
- 分类ID
- 标准损耗率
- 默认安全库存
- 默认起订量
- 包装单位
- 默认包装规格

这些字段等V1跑通后，再根据真实数据质量和业务需要补充。

## 3. 门店商品表：store_products

用于记录不同门店的商品差异化配置。V1只保留会影响订货建议的字段。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 主键ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| store_product_code | varchar | 否 | 门店侧商品编码 |
| sale_status | varchar | 是 | 销售状态：on_sale/off_sale/suspended |
| safety_stock | numeric | 否 | 门店安全库存 |
| moq | numeric | 否 | 门店起订量 |
| package_size | numeric | 否 | 门店包装规格，如20kg/箱 |
| delivery_cycle_days | numeric | 否 | 门店配送周期 |
| created_at | timestamp | 是 | 创建时间 |
| updated_at | timestamp | 是 | 更新时间 |

暂时移除的后期字段：

- 门店零售价
- 默认供应商ID
- 商品优先级

V1订货建议先不依赖售价和供应商评分，避免数据维护过重。

## 4. 销售明细表：sales_records

用于记录门店商品销售。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 销售记录ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| sale_time | timestamp | 是 | 销售时间 |
| business_date | date | 是 | 营业日期 |
| quantity | numeric | 是 | 销售数量 |
| unit | varchar | 是 | 销售单位 |
| sale_amount | numeric | 是 | 销售金额 |
| discount_amount | numeric | 否 | 优惠金额 |
| actual_price | numeric | 否 | 实际成交单价 |
| channel | varchar | 是 | 渠道：pos/meituan/eleme/online |
| order_no | varchar | 否 | 订单号 |
| source_system | varchar | 否 | 来源系统 |
| imported_at | timestamp | 是 | 导入时间 |

## 5. ERP库存快照表：erp_inventory_snapshots

用于记录ERP库存原始数据。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 库存快照ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| snapshot_time | timestamp | 是 | 快照时间 |
| business_date | date | 是 | 营业日期 |
| erp_quantity | numeric | 是 | ERP库存数量 |
| unit | varchar | 是 | 单位 |
| source_system | varchar | 否 | 来源系统 |
| imported_at | timestamp | 是 | 导入时间 |

## 6. 入库记录表：purchase_receipts

用于记录采购到货和门店收货。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 入库记录ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| supplier_id | bigint / uuid | 否 | 供应商ID |
| receipt_no | varchar | 否 | 入库单号 |
| receipt_time | timestamp | 是 | 入库时间 |
| business_date | date | 是 | 营业日期 |
| quantity | numeric | 是 | 入库数量 |
| unit | varchar | 是 | 单位 |
| purchase_price | numeric | 否 | 采购单价 |
| total_cost | numeric | 否 | 总成本 |
| batch_no | varchar | 否 | 批次号 |
| arrival_date | date | 是 | 到货日期，V1同时作为生产日期口径 |
| source_system | varchar | 否 | 来源系统 |
| imported_at | timestamp | 是 | 导入时间 |

## 7. 报损记录表：loss_records

用于记录报损、丢弃、过期、破损等损耗。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 报损记录ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| loss_time | timestamp | 是 | 报损时间 |
| business_date | date | 是 | 营业日期 |
| quantity | numeric | 是 | 报损数量 |
| unit | varchar | 是 | 单位 |
| loss_reason | varchar | 否 | 报损原因，V1暂时忽略 |
| estimated_cost | numeric | 否 | 估算损耗成本 |
| operator_id | bigint / uuid | 否 | 操作人ID |
| source_system | varchar | 否 | 来源系统 |
| imported_at | timestamp | 是 | 导入时间 |

## 8. 人工盘点表：stock_counts

用于记录门店抽盘或全盘结果。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 盘点记录ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| count_time | timestamp | 是 | 盘点时间 |
| business_date | date | 是 | 营业日期 |
| counted_quantity | numeric | 是 | 人工盘点修正值，不作为主要库存值 |
| unit | varchar | 是 | 单位 |
| count_type | varchar | 是 | 盘点类型：full/random/risk_triggered |
| operator_id | bigint / uuid | 否 | 盘点人ID |
| remark | text | 否 | 备注 |
| created_at | timestamp | 是 | 创建时间 |

## 9. 库存计算结果表：inventory_calculations

用于记录理论库存、修正库存和库存可信度。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 计算结果ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| business_date | date | 是 | 营业日期 |
| erp_quantity | numeric | 否 | ERP库存 |
| theoretical_quantity | numeric | 是 | 理论库存 |
| counted_quantity | numeric | 否 | 最近人工盘点修正值 |
| corrected_quantity | numeric | 是 | 修正库存 |
| inventory_confidence | numeric | 是 | 库存可信度，0到100 |
| confidence_level | varchar | 是 | high/medium/low |
| sales_quantity | numeric | 否 | 当日销量 |
| receipt_quantity | numeric | 否 | 当日入库 |
| loss_quantity | numeric | 否 | 当日报损 |
| calculation_version | varchar | 否 | 计算规则版本 |
| calculated_at | timestamp | 是 | 计算时间 |

## 10. 批次库存表：inventory_batches

用于管理库存年龄和剩余寿命。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 批次ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| batch_no | varchar | 是 | 批次号 |
| arrival_date | date | 是 | 到货日期，V1同时作为生产日期口径 |
| shelf_life_days | numeric | 否 | 保鲜期天数 |
| remaining_life_days | numeric | 否 | 剩余寿命天数 |
| initial_quantity | numeric | 是 | 初始入库数量，V1取当日到货值 |
| remaining_quantity | numeric | 是 | 当前剩余数量 |
| unit | varchar | 是 | 单位 |
| batch_cost | numeric | 否 | 批次成本 |
| lifecycle_stage | varchar | 是 | fresh/golden/risk/clearance/expired |
| updated_at | timestamp | 是 | 更新时间 |

## 11. 订货建议表：order_suggestions

用于记录系统生成的订货建议和人工确认结果。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 订货建议ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| business_date | date | 是 | 建议日期 |
| forecast_quantity | numeric | 是 | 预测销量 |
| safety_stock | numeric | 是 | 安全库存 |
| corrected_inventory | numeric | 是 | 修正库存 |
| raw_suggested_quantity | numeric | 是 | 未圆整建议订货量 |
| final_suggested_quantity | numeric | 是 | 系统最终建议订货量 |
| manual_quantity | numeric | 否 | 人工修改订货量 |
| confirmed_quantity | numeric | 否 | 最终确认订货量 |
| moq | numeric | 否 | 起订量 |
| package_size | numeric | 否 | 包装规格 |
| rounding_reason | varchar | 否 | 圆整原因 |
| confidence_score | numeric | 否 | 建议可信度 |
| suggestion_reason | text | 否 | 系统建议原因 |
| manual_reason | text | 否 | 人工修改原因 |
| status | varchar | 是 | pending/confirmed/modified/rejected/executed |
| created_at | timestamp | 是 | 创建时间 |
| confirmed_at | timestamp | 否 | 确认时间 |

## 12. 风险提醒表：inventory_risks

用于记录库存风险。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 风险ID |
| store_id | bigint / uuid | 是 | 门店ID |
| product_id | bigint / uuid | 是 | 商品ID |
| business_date | date | 是 | 风险日期 |
| risk_type | varchar | 是 | stockout/high_stock/low_confidence/slow_moving/near_expiry/high_loss |
| risk_score | numeric | 是 | 风险分，0到100 |
| risk_level | varchar | 是 | low/medium/high/critical |
| current_inventory | numeric | 否 | 当前库存 |
| reference_value | numeric | 否 | 参考值，如安全库存、预测销量 |
| risk_reason | text | 是 | 风险原因 |
| suggested_action | text | 否 | 建议动作 |
| status | varchar | 是 | open/acknowledged/ignored/resolved |
| owner_id | bigint / uuid | 否 | 负责人ID |
| created_at | timestamp | 是 | 创建时间 |
| resolved_at | timestamp | 否 | 处理完成时间 |

## 13. 规则配置表：rule_configs

用于保存不同门店、分类、商品的规则差异。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 规则ID |
| rule_code | varchar | 是 | 规则编码 |
| rule_name | varchar | 是 | 规则名称 |
| rule_type | varchar | 是 | confidence/order/risk/clearance |
| scope_type | varchar | 是 | global/store/category/product |
| store_id | bigint / uuid | 否 | 门店ID |
| category_id | bigint / uuid | 否 | 分类ID |
| product_id | bigint / uuid | 否 | 商品ID |
| rule_params | json | 是 | 规则参数 |
| priority | integer | 是 | 优先级 |
| is_active | boolean | 是 | 是否启用 |
| effective_from | date | 否 | 生效日期 |
| effective_to | date | 否 | 失效日期 |
| created_at | timestamp | 是 | 创建时间 |
| updated_at | timestamp | 是 | 更新时间 |

## 五、V1核心规则建议

### 1. 理论库存计算

```text
今日理论库存 =
昨日修正库存
+ 今日入库
- 今日销售
- 今日报损
- 预计自然损耗
```

建议：

- 如果昨日有人工盘点，用昨日实盘库存作为起点。
- 如果没有人工盘点，用昨日修正库存作为起点。
- 称重商品允许一定误差。

### 2. 修正库存计算

```text
修正库存 =
ERP库存 × ERP权重
+ 理论库存 × 理论权重
+ 最近盘点库存 × 盘点权重
```

建议初始权重：

| 数据来源 | 高可信商品 | 中可信商品 | 低可信商品 |
| --- | ---: | ---: | ---: |
| ERP库存 | 40% | 25% | 10% |
| 理论库存 | 40% | 45% | 40% |
| 最近盘点 | 20% | 30% | 50% |

### 3. 库存可信度评分

建议评分因素：

- ERP库存与理论库存差异
- 最近盘点时间距离
- 历史库存误差频率
- 报损记录完整度
- 商品是否称重
- 商品是否高损耗

建议初始规则：

```text
库存可信度 = 100
- ERP与理论库存差异扣分
- 盘点过期扣分
- 高频误差扣分
- 报损缺失扣分
- 高损耗品类扣分
```

### 4. 订货建议规则

```text
基础订货量 =
预测销量
+ 安全库存
- 修正库存
```

如果结果小于0，则建议订货量为0。

再进行：

- MOQ圆整
- 包装规格圆整
- 高损耗商品下调
- 库存可信度低时提示人工确认

### 5. 风险评分规则

#### 缺货风险

```text
如果 修正库存 < 预测销量 × 缺货阈值
则触发缺货风险
```

#### 高库存风险

```text
如果 修正库存 > 预测销量 × 高库存阈值
则触发高库存风险
```

#### 库存可信度低

```text
如果 库存可信度 < 60
则触发盘点提醒
```

#### 临期风险

```text
如果 批次剩余寿命 <= 临期阈值
且 剩余库存 > 0
则触发临期风险
```

#### 滞销风险

```text
如果 最近N天销量低于最低动销阈值
且 当前库存高于安全库存
则触发滞销风险
```

## 六、V1页面建议

### 1. 总部驾驶舱

展示：

- 门店总数
- 高风险门店数
- 今日订货建议总数
- 库存可信度低商品数
- 高库存风险商品数
- 缺货风险商品数

### 2. 门店经营看板

按门店展示：

- 今日需订货商品
- 今日风险商品
- 库存可信度低商品
- 待盘点商品
- 待确认订货建议

### 3. 订货建议页

字段：

- 门店
- 商品
- 预测销量
- 修正库存
- 安全库存
- 系统建议量
- 人工修改量
- 最终确认量
- 修改原因
- 状态

### 4. 库存风险页

字段：

- 门店
- 商品
- 风险类型
- 风险分
- 风险原因
- 建议动作
- 处理状态
- 负责人

### 5. 库存可信度页

字段：

- 门店
- 商品
- ERP库存
- 理论库存
- 最近盘点库存
- 修正库存
- 可信度
- 建议动作

## 七、需要你确认或修改的关键问题

### 1. 试点门店数量

建议：先用3到5家门店。

你需要确认：

- 第一批试点门店数量
- 是否同城
- 是否同一ERP/POS系统

### 2. 试点品类

建议：先选1到3个高价值品类。

你需要确认：

- 先做叶菜、水果、鲜奶，还是其他品类
- 是否包含称重商品
- 是否包含高损耗短保商品

### 3. 数据来源

你需要确认：

- 销售数据从哪里来
- 库存数据从哪里来
- 入库数据从哪里来
- 报损数据是否完整
- 是否已有人工盘点数据

### 4. 订货执行方式

你需要确认：

- 系统只给建议，还是生成采购单
- 店长确认，还是总部采购确认
- 是否允许门店修改
- 修改是否必须填写原因

### 5. 多门店差异

你需要确认：

- 不同门店安全库存是否不同
- 不同门店配送周期是否不同
- 不同门店售价是否不同
- 不同门店商品编码是否一致

### 6. V1不做什么

建议V1暂时不做：

- 复杂AI预测
- 自动动态定价
- 自动同步外卖平台价格
- 员工任务考核
- 供应商评分
- 多门店自动调拨

## 八、建议下一步

建议你先修改本文件中的以下部分：

1. 试点门店数量
2. 试点品类
3. 现有数据来源
4. 商品、销售、库存字段是否能从现有系统拿到
5. 订货建议由谁确认
6. 哪些字段必须保留，哪些字段可以后置

修改完成后，再进入下一步：

```text
根据确认后的字段设计数据库schema
  ↓
设计API接口
  ↓
设计后台页面
  ↓
开发V1原型
```

## 九、大表哥数据源检核结果

检核日期：2026-05-25

数据源：盛和 A+ 数据分析系统 / 大表哥

### 1. 已确认可从大表哥获取的字段

#### 门店信息

大表哥可提供：

| FreshOS字段 | 大表哥字段 | data_column | 结论 |
| --- | --- | --- | --- |
| 门店编码 | 店铺编号 | store_id | 可直接使用 |
| 门店名称 | 店铺名称 | store_name | 可直接使用 |
| 门店类型 | 店铺类型 | store_type_desc | 可选使用 |
| 区域编码 | 区域编码 | zone_cd | 可选使用 |
| 营业状态 | 店铺状态 | status_desc | 可直接使用 |
| 开店日期 | 开店日期 | open_date | 可选使用 |
| 闭店日期 | 闭店日期 | close_date | 可选使用 |
| 营业区分 | 营业区分 | biz_type_desc | 可选使用 |

V1建议：

- 门店表可以保留 `store_code`、`store_name`、`store_type`、`business_status`。
- `city`、`district`、`address` 大表哥暂未看到，需要人工补充或从其他系统获取。

#### 分类信息

大表哥可提供：

| FreshOS字段 | 大表哥字段 | data_column | 结论 |
| --- | --- | --- | --- |
| 大分类编码 | 大分类编码 | cat_id_01 | 可直接使用 |
| 大分类名称 | 大分类名称 | cat_name_01 | 可直接使用 |
| 中分类编码 | 中分类编码 | cat_id_02 | 可直接使用 |
| 中分类名称 | 中分类名称 | cat_name_02 | 可直接使用 |
| 小分类编码 | 小分类编码 | cat_id_03 | 建议新增 |
| 小分类名称 | 小分类名称 | cat_name_03 | 建议新增 |

V1建议：

- 商品表中原来的 `category_name` 太粗，建议改为大类、中类、小类字段。
- FreshOS V1 数据准备阶段只导出大分类编码 `40` 和 `42`。
- `40` = 现制加工品，`42` = 日配生鲜。

#### 商品信息

大表哥可提供：

| FreshOS字段 | 大表哥字段 | data_column | 结论 |
| --- | --- | --- | --- |
| 商品编码 | 商品编码 | item_cd | 可直接使用 |
| 商品名称 | 商品名称 | item_name_dis | 可直接使用 |
| 商品条码 | 商品条码 | barcode | 建议新增 |
| 单位 | 销售单位 | sale_unit | 可直接使用 |
| 保鲜期 | 保质期限(天) | warranty_days | 可直接使用 |
| 规格 | 规格 | spec | 建议新增 |
| 箱装数 | 箱装数 | order_pack_qty | 可用于包装规格 |
| 起订量 / 订货批量 | 订货批量 | order_batch_qty | 可用于MOQ |
| 可订状态 | 可订标识 | item_flg2_desc | 建议新增 |
| 生命周期 | 生命周期标识 / 生命周期 | dieout_flg_desc / item_label_type_index2 | 建议新增 |
| 配送类型 | 配送类型 | delivery_type_name | 建议新增 |
| 门店销售状态 | 店铺销售标识 | store_sale_flg_desc | 可用于门店商品状态 |
| 门店订货状态 | 店铺订货标识 | store_order_flg_desc | 可用于门店商品状态 |
| 门店售价 | 店铺售价 | store_sale_price | 可选，不作为V1核心 |
| 店铺进价 | 店铺进价 | store_order_price | 可选，不作为V1核心 |
| 近期日均销量 | 近期日均销量 | store_dms | 建议新增，用于订货建议 |
| 门店订货上限 | 门店订货上限 | store_upper_qty | 建议新增 |
| 门店订货下限 | 门店订货下限 | store_lower_qty | 建议新增 |
| 门店昨日库存数量 | 门店库存数量(昨日) | store_stock_qty | 可用于库存快照 |
| 门店昨日库存金额 | 门店库存金额(昨日) | store_stock_amt | 可选 |

V1建议：

- 商品表应适当回加 `barcode`、`spec`、`sale_unit`、`warranty_days`。
- 门店商品表应回加 `order_batch_qty`、`order_pack_qty`、`store_order_flg_desc`、`store_sale_flg_desc`、`store_dms`、`store_upper_qty`、`store_lower_qty`。
- `门店订货上限/下限` 对自动订货很有价值，建议保留。

#### 销售数据

大表哥可提供：

| FreshOS字段 | 大表哥字段 | data_column | 结论 |
| --- | --- | --- | --- |
| 销售数量 | 销量 | sales_qty | 可直接使用 |
| 销售金额 | 销售额 | sales_amt | 可直接使用 |
| 成本金额 | 成本金额 | cost_amt | 可选 |
| 毛利额 | 毛利额 | gross_amt | 可选 |
| 毛利率 | 毛利率 | gross_rate | 可选 |
| 线上销量 | 线上销量 | sales_qty_online | 可选 |
| 线上销售额 | 线上销售额 | sales_amt_online | 可选 |
| 线下销量 | 线下销量 | sales_qty_offline | 可选 |
| 线下销售额 | 线下销售额 | sales_amt_offline | 可选 |
| 销售单价 | 销售单价 | sales_amt_avg | 可选 |
| 动销店数 | 动销店数 | store_sales_count | 可选 |
| 动销SKU数 | 动销SKU数 | item_sales_count | 可选 |
| 动销率 | 动销率 | item_sales_rate | 可选 |

V1建议：

- 销售表 V1 先保留 `sales_qty`、`sales_amt`。
- 如果要做线上/线下差异预测，可后续增加线上、线下销量和销售额。

#### 库存数据

大表哥可提供：

| FreshOS字段 | 大表哥字段 | data_column | 结论 |
| --- | --- | --- | --- |
| 期初库存数量 | 库存数量（期初） | opening_stock_qty | 可直接使用 |
| 期末库存数量 | 库存数量（期末） | closing_stock_qty | 可直接使用 |
| 日均库存数量 | 库存数量(日均) | stock_qty | 可选 |
| 报损数量 | 报损数量 | loss_qty | 可用于损耗 |
| 报损金额 | 报损金额 | loss_amt | 可用于损耗 |
| 盘盈盘亏数量 | 盘盈盘亏数量 | inv_qty | 建议新增 |
| 盘盈盘亏金额 | 盘盈盘亏金额 | inv_amt | 建议新增 |
| 周转天数 | 周转天数 | turnover_days_d | 建议新增 |

V1建议：

- 库存快照可以先用 `closing_stock_qty` 或 `store_stock_qty`。
- 报损数据如果没有明细表，V1可先使用大表哥汇总报损数量/金额。
- `盘盈盘亏数量` 对库存可信度很有价值，建议加入库存可信度计算。

#### 进货数据

大表哥可提供：

| FreshOS字段 | 大表哥字段 | data_column | 结论 |
| --- | --- | --- | --- |
| 订货数量 | 订货数量 | order_qty | 可直接使用 |
| 订货金额 | 订货金额 | order_amt | 可选 |
| 收货数量 | 收货数量 | receive_vendor_qty | 可直接使用 |
| 总收货数量 | 总收货数量 | receive_all_qty | 可直接使用 |
| 收货金额 | 收货金额 | receive_vendor_amt | 可选 |
| 总收货金额 | 总收货金额 | receive_all_amt | 可选 |
| 退货数量 | 退货数量 | return_vendor_qty | 可选 |
| 退货金额 | 退货金额 | return_vendor_amt | 可选 |

V1建议：

- 入库记录如果拿不到明细单据，可先用 `总收货数量` 做日汇总入库。
- 订货建议复盘时，可用 `订货数量` 对比系统建议量。

### 2. 建议新增或调整的数据表字段

#### 商品主表 products 建议调整

在当前精简版基础上，建议新增：

| 字段名 | 来源 | 说明 |
| --- | --- | --- |
| barcode | 大表哥商品条码 | 辅助商品识别 |
| cat_id_01 | 大分类编码 | 用于生鲜筛选 |
| cat_name_01 | 大分类名称 | 用于分类展示 |
| cat_id_02 | 中分类编码 | 用于蔬菜、水果等细分 |
| cat_name_02 | 中分类名称 | 用于分类展示 |
| cat_id_03 | 小分类编码 | 可选，但建议保留 |
| cat_name_03 | 小分类名称 | 可选，但建议保留 |
| spec | 规格 | 用于商品识别 |
| sale_unit | 销售单位 | 比手工维护单位更可靠 |
| warranty_days | 保质期限(天) | 对临期风险有价值 |

#### 门店商品表 store_products 建议调整

在当前精简版基础上，建议新增：

| 字段名 | 来源 | 说明 |
| --- | --- | --- |
| order_pack_qty | 箱装数 | 用于包装规格圆整 |
| order_batch_qty | 订货批量 | 用于MOQ圆整 |
| store_order_flg | 店铺订货标识 | 判断是否可订 |
| store_sale_flg | 店铺销售标识 | 判断是否可售 |
| store_dms | 近期日均销量 | V1可作为基础预测销量 |
| store_upper_qty | 门店订货上限 | 防止订货过量 |
| store_lower_qty | 门店订货下限 | 防止订货过少 |
| store_stock_qty_yesterday | 门店库存数量(昨日) | 可辅助库存快照 |

#### 库存计算表 inventory_calculations 建议新增

| 字段名 | 来源 | 说明 |
| --- | --- | --- |
| opening_stock_qty | 期初库存数量 | 辅助库存推算 |
| closing_stock_qty | 期末库存数量 | 可作为ERP库存快照 |
| loss_qty | 报损数量 | 用于理论库存 |
| inv_qty | 盘盈盘亏数量 | 用于库存可信度 |
| turnover_days | 周转天数 | 用于高库存和滞销风险 |

#### 入库 / 进货表 purchase_receipts 建议简化

如果暂时拿不到入库明细，可先改为日汇总表：

| 字段名 | 来源 | 说明 |
| --- | --- | --- |
| store_id | 店铺编号 | 门店 |
| product_id | 商品编码 | 商品 |
| business_date | 查询日期 | 营业日期 |
| order_qty | 订货数量 | 订货复盘 |
| receive_qty | 总收货数量 | 理论库存入库 |
| return_qty | 总退货+调出数量 | 理论库存扣减 |
| order_amt | 订货金额 | 可选 |
| receive_amt | 总收货金额 | 可选 |

### 3. 大表哥暂未直接确认的数据

以下数据在当前大表哥期间报表里没有直接确认，需要后续通过今日实时报表、其他报表或人工配置补充：

| 数据 | 影响 | 建议 |
| --- | --- | --- |
| 实时库存数量 | 影响当日订货准确性 | 由大表哥今日实时报表验证和导出 |
| 在途数量 | 影响订货建议 | 由大表哥今日实时报表验证和导出 |
| 人工盘点数量 | 用于库存修正 | 作为修正值，不作为主要库存值 |
| 批次到货日期 | 影响生命周期和临期风险 | 使用订单导入的到货日期 |
| 门店地址、城市、区县 | 影响区域分析 | 需要人工维护或其他系统补充 |

### 4. 当前结论

大表哥可以支撑 FreshOS V1 的大部分基础数据：

- 门店基础信息
- 商品基础信息
- 商品分类
- 销售汇总
- 库存汇总
- 报损汇总
- 进货 / 收货汇总
- 门店商品订货参数

但大表哥暂时不能单独支撑完整 V1：

- 人工盘点数量需要作为库存修正值补充
- 到货日期需要从订单导入值获取
- 批次剩余库存可以先由系统按FIFO推算
- 实时库存和在途字段由大表哥今日实时报表导出，后续由系统验证字段稳定性

因此建议 V1 数据来源分两层：

1. 大表哥作为主数据源：销售、库存、进货、商品、门店。
2. 订单导入或人工录入作为补充数据源：到货日期、人工盘点修正值、门店地址。

## 十、补充字段需求与定义

本章节定义大表哥暂时不能完整提供、但 FreshOS V1 建议补充的字段。

字段优先级说明：

- P0：V1核心闭环强依赖，建议必须补。
- P1：能明显提升订货和风险判断质量，建议尽早补。
- P2：后续增强字段，V1可以暂缓。

### 1. 门店资料补充字段

#### store_address：门店地址

| 项目 | 定义 |
| --- | --- |
| 中文名 | 门店地址 |
| 所属表 | stores |
| 类型建议 | varchar |
| 是否必填 | 否 |
| 优先级 | P2 |
| 字段说明 | 门店详细地址，用于区域分析、配送路线分析和门店档案展示。 |
| 示例 | 哈尔滨市南岗区某某路100号 |
| 建议来源 | ERP门店档案 / 人工维护 |

#### city：城市

| 项目 | 定义 |
| --- | --- |
| 中文名 | 城市 |
| 所属表 | stores |
| 类型建议 | varchar |
| 是否必填 | 否 |
| 优先级 | P1 |
| 字段说明 | 门店所在城市，用于多城市经营分析和天气、节假日等外部数据匹配。 |
| 示例 | 哈尔滨 |
| 建议来源 | ERP门店档案 / 人工维护 |

#### district：区县

| 项目 | 定义 |
| --- | --- |
| 中文名 | 区县 |
| 所属表 | stores |
| 类型建议 | varchar |
| 是否必填 | 否 |
| 优先级 | P2 |
| 字段说明 | 门店所在区县，用于区域分组、同区门店对比和配送分析。 |
| 示例 | 南岗区 |
| 建议来源 | ERP门店档案 / 人工维护 |

#### delivery_cycle_days：配送周期

| 项目 | 定义 |
| --- | --- |
| 中文名 | 配送周期 |
| 所属表 | store_products 或 stores |
| 类型建议 | numeric |
| 是否必填 | 是 |
| 优先级 | P0 |
| 字段说明 | 日配生鲜按每日配送处理，V1默认配送周期为1天。 |
| 示例 | 1 |
| 建议来源 | 系统默认值 |

使用规则：

```text
需要覆盖销量天数 = 配送周期 + 安全库存覆盖天数
```

如果同一门店所有商品配送周期一致，可以放在 `stores`。如果不同商品配送周期不同，应放在 `store_products`。

V1业务口径：

```text
所有试点门店默认每日配送。
delivery_cycle_days 默认固定为 1。
暂不需要维护每周配送日。
```

#### default_delivery_days：默认配送日（V1取消）

| 项目 | 定义 |
| --- | --- |
| 中文名 | 默认配送日 |
| 所属表 | stores 或 store_products |
| 类型建议 | json / varchar |
| 是否必填 | 否 |
| 优先级 | V1不需要 |
| 字段说明 | V1按每日配送处理，不再维护默认配送日。 |
| 示例 | 不适用 |
| 建议来源 | 不适用 |

使用规则：

```text
V1默认每日配送，因此不需要判断下一次配送日。
```

#### order_owner：门店订货负责人（V1取消）

| 项目 | 定义 |
| --- | --- |
| 中文名 | 门店订货负责人 |
| 所属表 | stores |
| 类型建议 | varchar 或 user_id |
| 是否必填 | 否 |
| 优先级 | V1不需要 |
| 字段说明 | V1暂不做负责人分配和任务流转，因此不维护门店订货负责人。 |
| 示例 | 不适用 |
| 建议来源 | 不适用 |

### 2. 库存可信度补充字段

#### counted_quantity：人工盘点数量

| 项目 | 定义 |
| --- | --- |
| 中文名 | 人工盘点数量 |
| 所属表 | stock_counts |
| 类型建议 | numeric |
| 是否必填 | 是 |
| 优先级 | P0 |
| 字段说明 | 门店人工实盘得到的库存修正值。只用于修正库存，不作为主要库存来源。 |
| 示例 | 12.5 |
| 建议来源 | 门店人工录入 / 盘点系统 |

使用规则：

```text
主要库存值仍来自大表哥库存或系统理论库存。
人工盘点数量只作为修正值，用于纠偏。
```

#### count_time：盘点时间

| 项目 | 定义 |
| --- | --- |
| 中文名 | 盘点时间 |
| 所属表 | stock_counts |
| 类型建议 | timestamp |
| 是否必填 | 是 |
| 优先级 | P0 |
| 字段说明 | 实际完成盘点的时间。用于判断盘点数据是否过期。 |
| 示例 | 2026-05-25 21:30:00 |
| 建议来源 | 门店人工录入 / 系统自动记录 |

使用规则：

```text
盘点越新，盘点库存权重越高。
盘点超过指定天数后，库存可信度下降。
```

#### count_operator：盘点人

| 项目 | 定义 |
| --- | --- |
| 中文名 | 盘点人 |
| 所属表 | stock_counts |
| 类型建议 | varchar 或 user_id |
| 是否必填 | 否 |
| 优先级 | P1 |
| 字段说明 | 执行盘点的员工。用于责任追踪和异常复核。 |
| 示例 | 李四 / user_2001 |
| 建议来源 | 门店人工录入 / 系统账号 |

#### count_type：盘点类型

| 项目 | 定义 |
| --- | --- |
| 中文名 | 盘点类型 |
| 所属表 | stock_counts |
| 类型建议 | varchar |
| 是否必填 | 是 |
| 优先级 | P0 |
| 字段说明 | 标记盘点是全盘、抽盘还是系统触发的风险盘点。 |
| 可选值 | full、random、risk_triggered |
| 示例 | risk_triggered |
| 建议来源 | 门店人工录入 / 系统自动生成 |

#### count_remark：盘点备注

| 项目 | 定义 |
| --- | --- |
| 中文名 | 盘点备注 |
| 所属表 | stock_counts |
| 类型建议 | text |
| 是否必填 | 否 |
| 优先级 | P2 |
| 字段说明 | 盘点时的补充说明，例如陈列区未盘、仓库未盘、商品混码等。 |
| 示例 | 后仓还有2箱未上架 |
| 建议来源 | 门店人工录入 |

#### inventory_difference_reason：盘盈盘亏原因

| 项目 | 定义 |
| --- | --- |
| 中文名 | 盘盈盘亏原因 |
| 所属表 | stock_counts 或 inventory_calculations |
| 类型建议 | varchar / text |
| 是否必填 | 否 |
| 优先级 | P0 |
| 字段说明 | 解释盘点库存与系统库存差异的原因。用于库存可信度和异常归因。 |
| 示例 | 报损漏录、称重误差、收货未入账、销售串码 |
| 建议来源 | 门店人工录入 |

建议可选值：

| 值 | 含义 |
| --- | --- |
| loss_not_recorded | 报损漏录 |
| receiving_not_recorded | 收货未入账 |
| sales_error | 销售串码/错码 |
| weighing_error | 称重误差 |
| theft_or_unknown_loss | 不明损耗 |
| stocktake_error | 盘点误差 |
| other | 其他 |

### 3. 批次与生命周期补充字段

#### batch_no：批次号

| 项目 | 定义 |
| --- | --- |
| 中文名 | 批次号 |
| 所属表 | inventory_batches |
| 类型建议 | varchar |
| 是否必填 | 否 |
| 优先级 | P1 |
| 字段说明 | 标识一批入库商品。若供应商没有批次号，可由系统按门店、商品、到货日期自动生成。 |
| 示例 | B202605250001 |
| 建议来源 | 入库单 / 系统生成 |

#### arrival_date：到货日期

| 项目 | 定义 |
| --- | --- |
| 中文名 | 到货日期 |
| 所属表 | inventory_batches / purchase_receipts |
| 类型建议 | date |
| 是否必填 | 是 |
| 优先级 | P0 |
| 字段说明 | 商品到达门店或仓库的日期。用于计算库存年龄。 |
| 示例 | 2026-05-25 |
| 建议来源 | 入库记录 / 门店收货记录 |

使用规则：

```text
库存年龄 = 当前日期 - 到货日期
```

#### production_date：生产日期

| 项目 | 定义 |
| --- | --- |
| 中文名 | 生产日期 |
| 所属表 | inventory_batches |
| 类型建议 | date |
| 是否必填 | 否 |
| 优先级 | V1不单独维护 |
| 字段说明 | 本工具主要面向日配生鲜，V1不单独维护生产日期，统一使用到货日期作为生产日期口径。 |
| 示例 | 使用 arrival_date |
| 建议来源 | 到货日期 |

#### initial_batch_quantity：初始入库数量

| 项目 | 定义 |
| --- | --- |
| 中文名 | 初始入库数量 |
| 所属表 | inventory_batches |
| 类型建议 | numeric |
| 是否必填 | 是 |
| 优先级 | P0 |
| 字段说明 | 当日到货数量。V1从订单导入或大表哥收货数据中取当日到货值。 |
| 示例 | 50 |
| 建议来源 | 订单导入 / 当日到货数据 / 大表哥收货数据 |

#### remaining_batch_quantity：当前批次剩余数量

| 项目 | 定义 |
| --- | --- |
| 中文名 | 当前批次剩余数量 |
| 所属表 | inventory_batches |
| 类型建议 | numeric |
| 是否必填 | 否 |
| 优先级 | P1 |
| 字段说明 | 当前批次还剩多少库存。V1可通过FIFO根据销售和报损推算。 |
| 示例 | 18.5 |
| 建议来源 | 系统计算 / 人工盘点 |

#### batch_cost：批次成本

| 项目 | 定义 |
| --- | --- |
| 中文名 | 批次成本 |
| 所属表 | inventory_batches |
| 类型建议 | numeric |
| 是否必填 | 否 |
| 优先级 | P2 |
| 字段说明 | 当前批次商品的采购成本。用于批次毛利和出清决策。 |
| 示例 | 3.20 |
| 建议来源 | 入库记录 / 采购价格 |

#### remaining_life_days：剩余寿命天数

| 项目 | 定义 |
| --- | --- |
| 中文名 | 剩余寿命天数 |
| 所属表 | inventory_batches |
| 类型建议 | numeric |
| 是否必填 | 否 |
| 优先级 | P1 |
| 字段说明 | 当前批次距离失去可售价值还剩多少天。V1按到货日期计算。 |
| 示例 | 2 |
| 建议来源 | 系统计算 |

计算方式：

```text
剩余寿命 = 到货日期 + 保质期天数 - 当前日期
```

#### lifecycle_stage：生命周期阶段

| 项目 | 定义 |
| --- | --- |
| 中文名 | 生命周期阶段 |
| 所属表 | inventory_batches |
| 类型建议 | varchar |
| 是否必填 | 否 |
| 优先级 | P1 |
| 字段说明 | 标记当前批次处于新鲜期、黄金销售期、风险期、临期或过期。 |
| 可选值 | fresh、golden、risk、clearance、expired |
| 示例 | clearance |
| 建议来源 | 系统计算 |

### 4. 报损明细补充字段

#### loss_time：报损时间

| 项目 | 定义 |
| --- | --- |
| 中文名 | 报损时间 |
| 所属表 | loss_records |
| 类型建议 | timestamp |
| 是否必填 | 是 |
| 优先级 | P1 |
| 字段说明 | 实际发生或登记报损的时间。用于理论库存扣减。 |
| 示例 | 2026-05-25 19:20:00 |
| 建议来源 | 报损系统 / 门店录入 |

#### loss_quantity：报损数量

| 项目 | 定义 |
| --- | --- |
| 中文名 | 报损数量 |
| 所属表 | loss_records |
| 类型建议 | numeric |
| 是否必填 | 是 |
| 优先级 | P0 |
| 字段说明 | 报损商品数量。用于理论库存扣减和损耗率计算。 |
| 示例 | 3.5 |
| 建议来源 | 大表哥汇总 / 报损系统 / 门店录入 |

#### loss_reason：报损原因

| 项目 | 定义 |
| --- | --- |
| 中文名 | 报损原因 |
| 所属表 | loss_records |
| 类型建议 | varchar |
| 是否必填 | 否 |
| 优先级 | V1暂缓 |
| 字段说明 | V1暂时忽略报损原因，只使用报损数量和报损金额参与库存、损耗计算。 |
| 示例 | 不适用 |
| 建议来源 | 后续报损系统 / 门店录入 |

建议可选值：

| 值 | 含义 |
| --- | --- |
| expired | 过期 |
| damaged | 破损 |
| quality | 品质问题 |
| shrinkage | 自然损耗 |
| display_loss | 陈列损耗 |
| processing_loss | 加工损耗 |
| other | 其他 |

#### loss_operator：报损操作人

| 项目 | 定义 |
| --- | --- |
| 中文名 | 报损操作人 |
| 所属表 | loss_records |
| 类型建议 | varchar 或 user_id |
| 是否必填 | 否 |
| 优先级 | P1 |
| 字段说明 | 登记报损的员工。用于执行追踪和异常复核。 |
| 示例 | 王五 / user_3001 |
| 建议来源 | 报损系统 / 门店录入 |

#### loss_photo_url：报损照片

| 项目 | 定义 |
| --- | --- |
| 中文名 | 报损照片 |
| 所属表 | loss_records |
| 类型建议 | varchar / text |
| 是否必填 | 否 |
| 优先级 | P2 |
| 字段说明 | 报损商品照片地址。用于后期防虚报和品质复核。 |
| 示例 | https://example.com/loss/xxx.jpg |
| 建议来源 | 门店拍照上传 |

### 5. 最小补充字段清单

按当前业务口径，V1最小补充字段调整如下：

| 字段 | 所属表 | 优先级 | 原因 |
| --- | --- | --- | --- |
| delivery_cycle_days | stores / store_products | P0 | 默认每日配送，固定为1 |
| counted_quantity | stock_counts | P0 | 作为库存修正值 |
| count_time | stock_counts | P0 | 判断盘点有效性 |
| count_type | stock_counts | P0 | 区分全盘、抽盘、风险盘点 |
| inventory_difference_reason | stock_counts | P0 | 解释库存异常 |
| arrival_date | inventory_batches / purchase_receipts | P0 | 订单导入值，同时作为生产日期口径 |
| initial_batch_quantity | inventory_batches | P0 | 取当日到货值 |

### 6. V1落地建议

如果短期内字段收集困难，建议分阶段：

第一阶段必须补：

- 配送周期，默认固定为1天
- 人工盘点数量，作为库存修正值
- 盘点时间
- 到货日期，来自订单导入值
- 入库数量，取当日到货值

第二阶段再补：

- 盘点类型
- 盘盈盘亏原因
- 批次号
- 剩余寿命天数

第三阶段再补：

- 报损照片
- 批次成本
- 门店地址
- 区县

## 十一、数据准备阶段确认口径

本章节记录数据导入前已确认的业务口径。后续数据库设计、导入模板、清洗规则和计算逻辑必须以此为准。

### 1. 编码唯一性

| 问题 | 结论 | 系统处理 |
| --- | --- | --- |
| 商品编码是否全系统唯一 | 是 | `product_code` 可作为商品唯一业务编码 |
| 门店编码是否全系统唯一 | 是 | `store_code` 可作为门店唯一业务编码 |

设计影响：

```text
products.product_code 建议加唯一约束
stores.store_code 建议加唯一约束
导入销售、库存、订单、盘点数据时，优先用编码匹配门店和商品
```

### 2. 单位口径

| 问题 | 结论 | 系统处理 |
| --- | --- | --- |
| 销售数量单位是否统一 | 是 | 销售数量可直接汇总 |
| 称重商品单位是否都是kg | 看销售单位 | 以大表哥或销售数据里的 `sale_unit` / `unit` 为准 |

设计影响：

```text
系统不强制所有称重商品统一为kg。
导入时必须保留 unit 字段。
同一商品如果出现多个单位，需要进入异常清单。
```

### 3. 库存口径

| 问题 | 结论 | 系统处理 |
| --- | --- | --- |
| 库存数量是否允许负数 | 是 | 系统允许负库存，但标记为异常 |
| 大表哥库存是什么口径 | 实时库存为时点库存 | 实时库存按 snapshot_time 记录 |

设计影响：

```text
库存表不能禁止负数。
负库存不自动修正为0。
负库存需要触发库存异常或低可信度提醒。
实时库存必须记录 snapshot_time，不能只记录 business_date。
同一天同门店同商品可以存在多个库存快照。
```

建议库存快照唯一口径：

```text
store_code + product_code + snapshot_time
```

### 4. 到货和订货口径

| 问题 | 结论 | 系统处理 |
| --- | --- | --- |
| 到货数量是否可能大于订货数量 | 是 | 系统允许，不作为导入错误 |

设计影响：

```text
到货数量 > 订货数量 时，不拦截导入。
该情况可标记为采购/收货差异，用于后续复盘。
V1理论库存以当日到货数量为准，而不是以订货数量为准。
```

### 5. 明细重复口径

| 问题 | 结论 | 系统处理 |
| --- | --- | --- |
| 同一天同门店同商品是否可能多条记录 | 是 | 销售、到货、报损等明细表允许多条 |

设计影响：

```text
不能用 store_code + product_code + business_date 作为明细表唯一键。
销售数据按明细导入后，再按日汇总计算。
订货、到货、报损数据也需要先保留明细，再生成日汇总结果。
```

建议日汇总口径：

```text
daily_sales_quantity = sum(sales_records.quantity)
daily_sales_amount = sum(sales_records.sale_amount)
daily_receipt_quantity = sum(purchase_receipts.quantity)
daily_loss_quantity = sum(loss_records.quantity)
```

### 6. 对V1计算逻辑的影响

基于以上口径，V1库存计算建议如下：

```text
理论库存 =
上一时点修正库存
+ 当日到货数量汇总
- 当日销售数量汇总
- 当日报损数量汇总
```

实时库存口径：

```text
实时库存 = 大表哥某一时点库存快照
```

人工盘点口径：

```text
人工盘点数量 = 修正值
不是主要库存来源
```

当存在多个数据来源时，优先级建议：

```text
实时库存快照 > 理论库存 > 人工盘点修正值
```

说明：

- 实时库存是当前主要库存口径。
- 理论库存用于校验实时库存是否异常。
- 人工盘点用于纠偏和提升可信度，不直接替代主库存。

## 十二、生鲜订单导入格式

检核样例：

- `5.25水果订单(2).xlsx`
- `宝信润山店.xlsx`

当前确认存在两种订单格式：

1. 水果订单标准明细格式
2. 蔬菜供应商模板格式

两种格式都可以作为 V1 的“订单/到货数据源”，但字段结构不同，需要分别解析后统一映射到 FreshOS 的订单导入表。

### 1. 统一目标表：fresh_order_imports

建议先建立一张统一订单导入表，用于承接不同格式的生鲜订单。

| 字段名 | 类型建议 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| id | bigint / uuid | 是 | 主键 |
| source_file_name | varchar | 是 | 来源文件名 |
| source_sheet_name | varchar | 是 | 来源sheet |
| source_format | varchar | 是 | fruit_standard / vegetable_supplier |
| supplier_code | varchar | 否 | 供应商编码 |
| supplier_name | varchar | 否 | 供应商名称 |
| store_code | varchar | 否 | 门店编码 |
| store_name | varchar | 是 | 门店名称 |
| product_code | varchar | 否 | 商品编码 |
| product_name | varchar | 是 | 商品名称 |
| order_date | date | 否 | 订单日期 |
| arrival_date | date | 是 | 到货日期，V1同时作为生产日期口径 |
| ordered_quantity | numeric | 否 | 订货数量 |
| gross_quantity | numeric | 否 | 毛重 |
| tare_quantity | numeric | 否 | 皮重 / 筐皮重量 |
| shipped_quantity | numeric | 否 | 发货数量 / 供货量 / 净果数量 |
| received_quantity | numeric | 否 | 门店实收重量 |
| unit | varchar | 是 | 单位，默认kg |
| quoted_price | numeric | 否 | 报价单价 |
| shipped_price | numeric | 否 | 发货单价 |
| received_price | numeric | 否 | 实收单价 |
| shipped_amount | numeric | 否 | 供货金额 / 发货金额 |
| received_amount | numeric | 否 | 实收金额 |
| loss_rate | numeric | 否 | 去损率 |
| remark | text | 否 | 备注 |
| raw_row_number | integer | 是 | 来源文件行号 |
| imported_at | timestamp | 是 | 导入时间 |

V1核心使用字段：

```text
store_code / store_name
product_code / product_name
arrival_date
shipped_quantity 或 received_quantity
unit
```

V1入库数量口径：

```text
如果有门店实收重量 received_quantity：
入库数量 = received_quantity

否则如果有发货数量 / 净果数量 shipped_quantity：
入库数量 = shipped_quantity

否则使用订货数量 ordered_quantity 作为临时值，并标记为待确认。
```

### 2. 水果订单标准明细格式

样例文件：`5.25水果订单(2).xlsx`

#### 表结构

- 第1行为表头。
- 第2行开始为订单明细。
- 每一行包含供应商、门店、商品、订货、发货和金额信息。
- 文件中可能存在大量空行或公式行，导入时必须过滤空商品行。

#### 原始字段

| Excel列 | 原始字段 | 说明 |
| --- | --- | --- |
| A | 供应商编码 | supplier_code |
| B | 供应商名称 | supplier_name |
| C | 门店编码 | store_code |
| D | 门店名称 | store_name |
| E | 商品编码 | product_code |
| F | 商品名称 | product_name |
| G | 订货数量 | ordered_quantity |
| H | 毛重 | gross_quantity |
| I | 皮重 | tare_quantity |
| J | 发货数量 | shipped_quantity，公式通常为毛重 - 皮重 |
| K | 发货单价 | shipped_price |
| L | 未命名金额列 | 原文件未命名，疑似含税或报价金额来源 |
| M | 总金额 | shipped_amount |

#### FreshOS字段映射

| FreshOS字段 | 水果订单字段 | 处理规则 |
| --- | --- | --- |
| source_format | 固定值 | fruit_standard |
| supplier_code | 供应商编码 | 原值转文本 |
| supplier_name | 供应商名称 | 原值 |
| store_code | 门店编码 | 原值转文本 |
| store_name | 门店名称 | 原值 |
| product_code | 商品编码 | 原值转文本 |
| product_name | 商品名称 | 原值 |
| ordered_quantity | 订货数量 | 可为空 |
| gross_quantity | 毛重 | 可为空 |
| tare_quantity | 皮重 | 可为空 |
| shipped_quantity | 发货数量 | 优先读取公式计算值；如无法读取，按毛重 - 皮重计算 |
| shipped_price | 发货单价 | 可为空 |
| shipped_amount | 总金额 | 可为空 |
| arrival_date | 文件名或人工输入 | 例如 `5.25` 对应 2026-05-25，需导入时确认年份 |
| unit | 固定值 | kg |

#### 导入过滤规则

导入时必须满足：

```text
商品编码不为空
商品名称不为空
门店名称不为空
```

以下行不导入：

```text
商品编码、商品名称均为空的行
只有公式但无业务数据的空行
合计行
```

#### 注意点

- 样例中存在 `门店编码=10003` 但 `门店名称=宝信润山店` 的行，需要后续校验门店编码和门店名称是否匹配。
- `发货数量` 是公式列，读取时建议使用 `data_only=True` 获取计算值；如果没有缓存值，需要系统重新计算或按 `毛重 - 皮重` 计算。
- 到货日期不在表头中，建议从文件名或导入时人工指定。

### 3. 蔬菜供应商模板格式

样例文件：`宝信润山店.xlsx`

#### 表结构

- 第1行包含供应商名称和供应商编号。
- 第2行包含门店名称、发货日期、采购专员和联系方式。
- 第4行为字段表头。
- 第5行开始为商品明细。
- 合计行之后存在筐、栈板等周转物，不应作为商品导入。

#### 头部信息解析

| 来源位置 | 示例 | 目标字段 |
| --- | --- | --- |
| A1 | 徐州喜果供应链管理有限公司（蔬菜）供应商编号；200477 | supplier_name / supplier_code |
| A2 | 门店名：丰年- 宝信润山店 | store_name |
| A2 | 发货日期：5.24下午 | arrival_date |
| A2 | 采购专员：果果 15371630360 | remark |

#### 原始字段

| Excel列 | 原始字段 | 说明 |
| --- | --- | --- |
| A | 序号 | 明细序号 |
| B | 商品编码 | product_code，样例中可能为空 |
| C | 产品名称 | product_name |
| D | 去损率 | loss_rate |
| E | 订单量（kg） | ordered_quantity |
| F | 供货量（斤） | 原始供货量，单位斤 |
| G | 系数 | 斤转kg系数，通常为2 |
| H | 供货量 | shipped_quantity，通常为 F / G |
| I | 箱数（箱） | package_count |
| J | 单箱筐皮重量（kg） | basket_tare_per_box |
| K | 筐皮数量（kg） | tare_quantity |
| L | 毛重数量（kg） | gross_quantity |
| M | 净果数量（kg） | net_quantity |
| N | 按报价单价（元/kg） | quoted_price_raw |
| O | 调整后报价单价 | quoted_price，表头为空但公式为 N / 0.95 |
| P | 供货金额 | shipped_amount |
| Q | 门店实收重量（kg） | received_quantity |
| R | 单价（元/kg） | received_price |
| S | 实收金额 | received_amount |
| T | 备注 | remark |

#### FreshOS字段映射

| FreshOS字段 | 蔬菜模板字段 | 处理规则 |
| --- | --- | --- |
| source_format | 固定值 | vegetable_supplier |
| supplier_code | A1解析 | 供应商编号后面的数字 |
| supplier_name | A1解析 | 供应商编号前面的名称 |
| store_name | A2解析 | `门店名：` 后的门店名称 |
| store_code | 暂无 | 通过门店名称匹配；编码和名称不一致时以门店名称为准 |
| product_code | 商品编码 | 可为空，按订单商品名称匹配系统商品 |
| product_name | 产品名称 | 必填 |
| order_date | 暂无 | 可导入时指定 |
| arrival_date | A2解析 | `发货日期`，例如 5.24下午 |
| ordered_quantity | 订单量（kg） | 原值 |
| gross_quantity | 毛重数量（kg） | 原值 |
| tare_quantity | 筐皮数量（kg） | 原值 |
| shipped_quantity | 净果数量（kg）优先，其次供货量 | 用于入库数量 |
| received_quantity | 门店实收重量（kg） | 若填写，优先作为最终入库数量 |
| unit | 固定值 | kg |
| quoted_price | 调整后报价单价 | 可为空 |
| shipped_amount | 供货金额 | 可为空 |
| received_price | 单价（元/kg） | 可为空 |
| received_amount | 实收金额 | 可为空 |
| loss_rate | 去损率 | 可为空 |
| remark | 备注 | 可为空 |

#### 导入过滤规则

导入时必须满足：

```text
产品名称不为空
序号为数字
行号在合计行之前
```

以下行不导入：

```text
合计行
栈板
大框
小筐
空行
```

#### 注意点

- 样例中商品编码大多为空，因此必须支持“订单商品名称匹配商品编码”的补全逻辑。
- 发货日期只有月日和上午/下午，没有年份，导入时需要使用当前年份或由用户确认。
- `供货量（斤）` 需要通过系数转换为kg。
- `门店实收重量` 如果为空，使用 `净果数量` 或 `供货量` 作为入库数量。

### 4. 订单导入的统一校验规则

#### 必填校验

订单导入至少需要：

```text
门店名称
商品名称
到货日期
入库数量
单位
```

如果缺少商品编码，可以先进入待匹配状态。

#### 门店匹配

优先级：

```text
门店名称精确匹配
  ↓
门店名称模糊匹配
  ↓
门店编码精确匹配
  ↓
人工确认
```

如果订单门店编码和订单门店名称不一致，以门店名称为准，同时记录异常用于后续修正源数据。

#### 商品匹配

优先级：

```text
商品编码精确匹配
  ↓
订单商品名称精确匹配
  ↓
订单商品名称去前缀后匹配
  ↓
人工确认
```

商品名称去前缀示例：

```text
Z-油桃 -> 油桃
C-富士苹果（小仅订货） -> 富士苹果
JPZ-海南香蕉 -> 海南香蕉
```

#### 入库数量取值优先级

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

#### 到货日期取值优先级

```text
表内发货日期 / 到货日期
  ↓
文件名日期
  ↓
导入时人工指定
```

#### 异常标记

以下情况不阻断导入，但需要标记：

| 异常 | 说明 |
| --- | --- |
| missing_product_code | 商品编码为空 |
| unmatched_product | 商品无法匹配系统商品 |
| unmatched_store | 门店无法匹配系统门店 |
| missing_arrival_date | 到货日期缺失 |
| missing_receipt_quantity | 入库数量缺失 |
| quantity_greater_than_order | 到货数量大于订货数量 |
| negative_quantity | 数量为负 |
| formula_not_calculated | 公式列没有缓存计算值 |

### 5. 对V1数据准备的影响

基于这两个样例，V1数据准备阶段需要新增：

1. 订单导入解析器需要支持至少两种格式：
   - `fruit_standard`
   - `vegetable_supplier`

2. 需要维护商品名称匹配规则：
   - 去除 `Z-`、`C-`、`JPZ-` 等前缀
   - 去除括号内备注
   - 支持人工确认未匹配商品

3. 到货日期需要允许人工确认：
   - 文件名日期
   - 表内发货日期
   - 当前年份
   - 上午/下午作为备注，不进入日期字段

4. 入库数量不再只看一个字段：
   - 水果订单优先取发货数量
   - 蔬菜订单优先取门店实收重量，其次净果数量

5. 门店编码和门店名称需要做一致性校验：
   - 如果编码和名称不匹配，以门店名称为准。
   - 同时进入异常清单，便于后续修正源数据。

6. 历史销售、库存、进货数据以大表哥为主：
   - 订单文件用于到货日期和当日到货值。
   - 大表哥用于历史销售、库存、报损、进货汇总。

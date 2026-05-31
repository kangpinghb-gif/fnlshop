# 订货数量测试数据暂存目录

用途：Hermes 导出本次订货数量测试所需文件。测试完成后可以删除整个目录。

业务日期：

```text
2026-05-28
```

历史区间：

```text
2026-05-01 至 2026-05-28
```

筛选范围：

```text
大分类编码 = 40,42
```

## 一、Hermes 需要导出的文件

请把以下文件导出到本目录：

```text
freshos-worker/workspace/order_qty_test_2026-05-28/
```

### 1. dabiaoge_stores_products_base.xlsx

字段：

```text
店铺编号
店铺名称
大分类编码
大分类名称
中分类编码
中分类名称
商品编码
商品名称
销售单位
保质期限(天)
店铺订货标识
店铺销售标识
订货批量
近期日均销量
门店库存数量(昨日)
```

### 2. dabiaoge_sales_daily.xlsx

字段：

```text
店铺编号
店铺名称
大分类编码
商品编码
商品名称
日期
销量
销售额
```

### 3. dabiaoge_inventory_loss_daily.xlsx

字段：

```text
店铺编号
店铺名称
大分类编码
商品编码
商品名称
日期
库存数量（期末）
报损数量
报损金额
盘盈盘亏数量
```

注意：`库存数量（期末）` 使用中文全角括号。

### 4. dabiaoge_purchase_receipts_daily.xlsx

字段：

```text
店铺编号
店铺名称
大分类编码
商品编码
商品名称
日期
订货数量
收货数量
总收货数量
总退货+调出数量
```

## 二、可选文件

如果有当天订单或盘点修正，也放到本目录：

```text
fresh_orders_2026-05-28.xlsx
stock_adjustments_2026-05-28.xlsx
```

没有则不用放。

## 三、导出后请反馈

每个文件请反馈：

```text
文件名
行数
门店数
商品数
日期范围
```

## 四、测试完成后删除

在服务器项目目录执行：

```bash
rm -rf /opt/freshos-worker/workspace/order_qty_test_2026-05-28
```


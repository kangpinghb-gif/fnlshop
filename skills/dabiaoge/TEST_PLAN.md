# 大表哥 Skill 测试清单

用途：更新 `skills/dabiaoge/SKILL.md` 后，用这份清单验证 Hermes / 浏览器执行是否按最新实测规则运行。

## 1. 登录校验

- 打开 `https://hljxz.info-plus.cn/KIT/homePage/login`
- 用户完成账号、密码和验证码/MFA
- 登录后检查：

```javascript
document.title
```

期望值：

```text
A+分析系统
```

## 2. type=1/2/3 字段选择

- 切换到目标报表类型
- 先触发字段 DOM：

```javascript
document.querySelectorAll('input[data_column]').length
```

- 等待 1-2 秒
- 使用策略 D：
  - 临时移除 `.option_item` 的 `hide`
  - 用 `data_column` 定位字段
  - 调用 `changeItemColorBox(jQuery(item))`
  - 恢复 `hide`
- 不点击主分类 checkbox

测试字段：

```text
store_name
item_cd
item_name_dis
cat_id_01
sales_qty
sales_amt
```

## 3. type=5 今日实时报表字段选择

- 切换到 `今日实时报表`
- 手动展开 `LabelText` 面板
- 按可见字段名选择，不使用策略 D

测试字段：

```text
店铺编号
店铺名称
商品编码
商品名称
库存数量
在途数量
```

注意字段差异：

```text
sales_qty -> sale_qty
sales_amt -> sale_amt
stock_qty 作为实时库存字段
```

## 4. 查询和导出

- 使用页面函数，不点页面按钮：

```javascript
customerSearchAll();
exportByDownloadCenter();
```

- 导出前必须挂 `downloadfile` 补丁并检查：

```javascript
window._capturedFileUrl
```

期望：

```text
15 秒内出现非空文件 URL
```

如果 15 秒后仍为 `null`：

```javascript
customerSearchAll();
exportByDownloadCenter();
```

## 5. 结果验证

- XLSX 文件存在且大小 > 0
- 表头包含本次预设字段
- 大分类编码只包含 `40` 和 `42`
- 行数不是 0
- 不以浏览器 `table[2]` 行数判断全量，最终以 XLSX 为准

## 6. type=2 期间对比格式

导出后检查：

```text
Row 1 = 期间1标签
Row 2 = 期间2标签
Row 3 = 列头
Row 4+ = 数据
```

如 `customerReset()` 后导出异常，重新切换 type=2 并重新设置两组日期。

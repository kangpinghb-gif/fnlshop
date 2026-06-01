# FreshOS V1 工具使用方式与业务操作流程

更新时间：2026-06-02

本文用于补齐《FreshOS V1 开发实施计划》中缺失的“工具怎么用”。V1.1 的定位不是完整 Web 后台，而是部署在阿里云服务器上的自动订货助手。

## 一、V1.1 工具形态

FreshOS V1.1 的使用方式：

```text
阿里云 ECS 服务器
  ↓
Hermes 12:00 定时触发 freshos-worker
  ↓
Hermes 自动导出 / 抓取大表哥数据，freshos-worker 导入订单 / 盘点 / 实时销售数据
  ↓
计算库存口径、12点趋势修正预测、预计到货前库存、订货建议、库存风险
  ↓
输出 CSV / Excel 文件
  ↓
企业微信 / 飞书推送摘要和附件
```

第一阶段不提供完整 Web 页面。

使用入口：

- 日常自动入口：Hermes。
- 手工补跑入口：服务器命令行。
- 结果查看入口：企业微信 / 飞书消息、服务器报表目录。
- 异常处理入口：导入异常明细文件、服务器日志、后续人工维护模板。

## 二、角色分工

| 角色 | 使用内容 | 主要动作 |
| --- | --- | --- |
| 总部运营 | 每日摘要、库存风险、异常清单 | 判断是否需要干预门店或商品 |
| 采购负责人 | 订货建议明细、已订未到、缺货风险 | 确认或调整订货量 |
| 区域督导 | 门店风险排行、库存可信度低商品 | 跟进门店盘点和执行 |
| 门店店长 / 生鲜主管 | 门店订货建议、风险商品 | 执行订货、反馈异常 |
| Hermes | 大表哥导出、定时触发任务 | 自动获取 40/42 数据并触发 worker |
| 系统维护人员 | 导入异常、任务日志、服务器状态 | 维护 Hermes 配置、重跑任务、处理失败 |

## 三、每日自动流程

建议每日 12:00 到 12:50 自动运行。

| 时间 | 任务 | 业务含义 | 产出 |
| --- | --- | --- | --- |
| 12:00 | Hermes 导出大表哥数据 | 获取实时销售、库存、损耗、订货收货 | `/var/lib/freshos/data/` 下的原始导出文件 |
| 12:10 | 导入基础档案和日汇总 | 更新门店、商品、门店商品、销售历史 | `stores`、`products`、`store_products`、`sales_daily` |
| 12:15 | 导入库存 / 损耗 / 收货 | 形成库存和报损口径 | `inventory_loss_daily`、`purchase_receipts_daily` |
| 12:18 | 导入库存快照和实时销售 | 获取 12 点库存和 0-12 点销售 | `inventory_snapshots`、`sales_cutoff_snapshots` |
| 12:20 | 导入订单 Excel | 获取当日 / 次日到货值 | `fresh_order_imports` |
| 12:25 | 匹配门店商品 | 将订单商品匹配到系统商品 | 匹配结果、异常清单 |
| 12:30 | 计算库存口径 | 生成修正后主库存 | `inventory_positions` |
| 12:35 | 计算销量预测 | 生成 12 点趋势修正预测 | `sales_forecasts` |
| 12:40 | 生成订货建议 | 给出门店商品订货量 | `order_suggestions` |
| 12:45 | 生成库存风险 | 标记缺货、积压、临期、负库存等风险 | `inventory_risks` |
| 12:50 | 导出报表并推送 | 给业务人员看结果 | 订货建议、库存风险、异常摘要 |

## 四、业务人员每天怎么看结果

### 1. 企业微信 / 飞书摘要

推送内容应包含：

```text
FreshOS 订货建议 - 2026-05-26

门店：全部门店
需订商品：N 个
高风险商品：N 个
缺货风险：N 个
临期 / 积压：N 个

附件：
1. 订货建议明细
2. 库存风险明细
3. 导入异常明细
```

### 2. 订货建议明细

采购负责人重点看：

- 门店
- 商品
- 当前库存
- 预测销量
- 安全库存
- 已订未到
- 建议订货量
- 订货原因
- 风险标记

处理原则：

- `建议订货量 > 0`：优先确认是否订货。
- `风险标记 = 高风险`：先看库存风险明细，再决定是否调整。
- 商品单位、规格、订货批量异常：反馈系统维护人员修正商品参数。
- 商品名称包含 `折` 或等于 `D系统用代表商品`：默认不计入常规订货建议。

### 3. 库存风险明细

运营和督导重点看：

- 负库存
- 缺货风险
- 高库存 / 积压
- 临期 / 过期
- 高损耗
- 数据缺失

处理原则：

- 负库存：优先安排门店盘点或检查入库 / 销售数据。
- 缺货风险：确认是否补订或调拨。
- 高库存 / 临期：安排出清、促销或减少订货。
- 数据缺失：交给系统维护人员补导或修复字段。

### 4. 导入异常明细

系统维护人员重点看：

- 门店无法匹配
- 商品无法匹配
- 商品编码缺失
- 门店编码和名称冲突
- 到货日期缺失
- 到货数量缺失
- 到货数量大于订货数量
- 负库存
- 单位冲突

处理原则：

- 能通过商品别名、商品编码、门店名称修复的，优先修复基础数据。
- 订单文件字段缺失的，反馈给供应商或订单整理人员。
- 大表哥字段变化的，更新 Hermes 导出字段配置和 FreshOS 导入字段映射。

## 五、系统维护人员怎么操作

### 1. 阿里云服务器目录

建议路径：

```text
/opt/freshos-worker          代码目录
/etc/freshos/settings.toml   配置文件
/var/lib/freshos/data        导入中间文件
/var/lib/freshos/reports     报表输出
```

### 2. 手工跑每日任务链

```bash
cd /opt/freshos-worker
/opt/freshos-worker/.venv/bin/python -m jobs.run_daily \
  --config /etc/freshos/settings.toml \
  --business-date 2026-05-26
```

### 3. 单独重跑某个任务

重跑库存计算：

```bash
cd /opt/freshos-worker
/opt/freshos-worker/.venv/bin/python -m jobs.calculate_inventory \
  --config /etc/freshos/settings.toml \
  --business-date 2026-05-26
```

重跑订货建议：

```bash
cd /opt/freshos-worker
/opt/freshos-worker/.venv/bin/python -m jobs.generate_order_suggestions \
  --config /etc/freshos/settings.toml \
  --business-date 2026-05-26
```

重跑报表：

```bash
cd /opt/freshos-worker
/opt/freshos-worker/.venv/bin/python -m jobs.export_reports \
  --config /etc/freshos/settings.toml \
  --business-date 2026-05-26
```

### 4. 查看 systemd 日志

```bash
journalctl -u freshos-worker.service -n 200 --no-pager
```

### 5. 最小闭环验证

服务器首次部署后，先用种子数据验证：

```bash
cd /opt/freshos-worker
/opt/freshos-worker/.venv/bin/python scripts/run_minimal_closure.py \
  --config /etc/freshos/settings.toml \
  --business-date 2026-05-26
```

预期结果：

- `inventory_positions rows=1`
- `sales_forecasts rows=1`
- `order_suggestions rows=1`
- `inventory_risks rows>=1`
- 报表目录生成 CSV 文件

### 6. Hermes 大表哥导出配置维护

V1 默认由 Hermes 负责大表哥导出，不要求系统维护人员每天手工导出。

Hermes 每天应导出并放置到：

```text
/var/lib/freshos/data/
```

建议文件命名：

```text
dabiaoge_base_40_42_YYYY-MM-DD.xlsx
dabiaoge_sales_40_42_YYYY-MM-DD.xlsx
dabiaoge_inventory_loss_40_42_YYYY-MM-DD.xlsx
dabiaoge_purchase_receipts_40_42_YYYY-MM-DD.xlsx
dabiaoge_inventory_snapshot_40_42_YYYY-MM-DD.xlsx
```

Hermes 必须保证：

- 登录大表哥使用授权账号。
- 不保存明文密码到项目文件。
- 大分类编码筛选为 `40,42`。
- 字段使用 FreshOS 预设字段。
- 文件导出成功后再触发对应导入任务。
- 导出失败时写入任务日志并推送失败提醒。

系统维护人员只负责：

- 首次授权登录。
- 更新字段预设。
- 处理验证码 / 登录失效。
- 处理导出失败和字段变化。

## 六、人工介入流程

### 1. 订货建议需要调整

V1 当前先通过报表人工调整，不做页面确认。

流程：

```text
采购查看订货建议
  ↓
发现建议不合理
  ↓
记录调整原因
  ↓
按人工确认量执行订货
  ↓
系统维护人员后续补充规则或商品参数
```

后续版本再做：

- 页面确认
- 修改原因回写
- 最终执行量回写
- 次日效果评估

### 2. 库存可信度低

流程：

```text
系统提示库存可信度低 / 负库存
  ↓
督导或店长安排盘点
  ↓
填写人工盘点修正模板
  ↓
导入 stock_count_adjustments
  ↓
重算库存口径和订货建议
```

### 3. 商品无法匹配

流程：

```text
导入异常出现 unmatched_product
  ↓
系统维护人员查看订单商品名
  ↓
确认是否已有系统商品
  ↓
补商品别名 / 修正商品编码 / 补基础档案
  ↓
重跑 match_order_imports
```

## 七、数据文件流转

### 输入

| 文件 | 来源 | 使用任务 |
| --- | --- | --- |
| 大表哥基础数据 | Hermes 自动导出 | `import_dabiaoge_base` |
| 大表哥销售日汇总 | Hermes 自动导出 | `import_dabiaoge_daily --report-type sales` |
| 大表哥库存损耗 | Hermes 自动导出 | `import_dabiaoge_daily --report-type inventory_loss` |
| 大表哥订货收货 | Hermes 自动导出 | `import_dabiaoge_daily --report-type purchase_receipts` |
| 大表哥库存快照 | Hermes 自动导出 | `import_dabiaoge_daily --report-type inventory_snapshot` |
| 生鲜订单 Excel | 供应商 / 采购 | `import_orders` |
| 人工盘点修正模板 | 门店 / 督导 | `import_stock_adjustments` |

### 输出

| 文件 | 使用人 | 说明 |
| --- | --- | --- |
| 订货建议明细 | 采购、店长 | 每日订货参考 |
| 库存风险明细 | 运营、督导、店长 | 缺货、积压、临期、负库存处理 |
| 导入异常明细 | 系统维护人员 | 修复数据匹配和字段问题 |

## 八、当前 V1.1 不做的使用方式

以下不是 V1 第一阶段重点：

- 完整 Web 后台。
- 手机端操作页面。
- 复杂审批流。
- 员工任务系统。
- 动态定价执行。
- 供应商评分。
- 复杂 AI 预测解释。

这些能力放到后续版本。

## 九、判断工具是否正常运行

每日检查：

1. 企业微信 / 飞书是否收到摘要。
2. 报表目录是否生成当天文件。
3. `job_runs` 是否有当天任务记录。
4. 是否存在大量 `import_exceptions`。
5. 订货建议是否为空。
6. 库存风险是否异常激增。

最低成功标准：

```text
有基础数据
有销售 / 库存 / 到货数据
能生成订货建议
能生成库存风险
能导出文件
能推送摘要
```

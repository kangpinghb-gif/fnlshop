# FreshOS V1 阿里云服务器部署实操记录

更新时间：2026-05-27

本文整理本次 FreshOS V1 在阿里云 ECS 上的实际部署过程，包含：

- 修正后的正确部署步骤
- 可直接复制执行的命令
- 关键输出示例
- 实际踩过的坑和正确处理方式

目标：

```text
在阿里云 ECS 上完成：
PostgreSQL
Python 3.11 虚拟环境
FreshOS worker 代码部署
数据库迁移
最小闭环验证
报表导出
每日摘要生成
```

## 一、服务器环境

服务器系统：

```bash
cat /etc/os-release
```

输出：

```text
NAME="Alibaba Cloud Linux"
VERSION="3 (OpenAnolis Edition)"
ID="alinux"
VERSION_ID="3"
PRETTY_NAME="Alibaba Cloud Linux 3.2104 U13 (OpenAnolis Edition)"
```

结论：

- 使用 `dnf`
- PostgreSQL 可直接用系统包
- 需要单独安装 Python 3.11，不能使用系统默认 Python 3.6

## 二、安装基础依赖

先更新安全补丁：

```bash
dnf upgrade-minimal --security -y
```

安装基础依赖：

```bash
dnf install -y python3 python3-pip python3-devel gcc postgresql-server postgresql-contrib rsync git
dnf install -y python3.11 python3.11-pip
```

检查版本：

```bash
python3 --version
python3.11 --version
psql --version
git --version
```

关键输出：

```text
Python 3.6.8
Python 3.11.15
psql (PostgreSQL) 13.23
git version 2.43.7
```

结论：

- `python3` 仍然是 3.6.8，不可用于项目运行
- 后续统一使用 `python3.11`

## 三、初始化 PostgreSQL

初始化数据库目录：

```bash
postgresql-setup --initdb
```

启动并设置开机自启：

```bash
systemctl enable --now postgresql
systemctl status postgresql --no-pager
```

关键输出：

```text
Active: active (running)
```

说明：

- PostgreSQL 已正常运行

## 四、创建数据库用户和数据库

进入 PostgreSQL：

```bash
sudo -u postgres psql
```

执行：

```sql
CREATE USER freshos WITH PASSWORD 'FreshOS_2026_change_me';
CREATE DATABASE freshos OWNER freshos;
\q
```

关键输出：

```text
CREATE ROLE
CREATE DATABASE
```

## 五、创建运行用户和目录

创建系统用户和运行目录：

```bash
useradd --system --create-home --home-dir /opt/freshos-worker --shell /usr/sbin/nologin freshos
mkdir -p /etc/freshos /var/lib/freshos/data /var/lib/freshos/reports
chown -R freshos:freshos /var/lib/freshos
```

检查目录：

```bash
ls -ld /opt/freshos-worker /etc/freshos /var/lib/freshos /var/lib/freshos/reports
```

示例输出：

```text
drwxr-xr-x 2 root    root    4096 May 27 16:20 /etc/freshos
drwx------ 2 freshos freshos 4096 May 27 16:20 /opt/freshos-worker
drwxr-xr-x 4 freshos freshos 4096 May 27 16:20 /var/lib/freshos
drwxr-xr-x 2 freshos freshos 4096 May 27 16:20 /var/lib/freshos/reports
```

## 六、上传代码

本次服务器不允许 `root` 密码方式直接 `rsync` 登录，因此最终采用宝塔面板上传 zip。

本地项目目录：

```text
/Users/kangping/Documents/生鲜AI自动订货系统/freshos-worker
```

本地压缩命令：

```bash
cd "/Users/kangping/Documents/生鲜AI自动订货系统"
zip -r /tmp/freshos-worker.zip freshos-worker
```

然后通过宝塔面板上传到服务器 `/opt`，解压。

### 纠正点 1：不要保留多余目录层级

第一次解压后目录结构变成：

```text
/opt/freshos-worker/freshos-worker
```

这是错误的。正确目录应该是：

```text
/opt/freshos-worker
```

修正命令：

```bash
shopt -s dotglob
mv /opt/freshos-worker/freshos-worker/* /opt/freshos-worker/
rmdir /opt/freshos-worker/freshos-worker
rm -rf /opt/freshos-worker/__MACOSX
chown -R freshos:freshos /opt/freshos-worker
```

检查代码目录：

```bash
ls -la /opt/freshos-worker
```

正确输出应至少包含：

```text
README.md
config
deploy
freshos
jobs
migrations
requirements.txt
scripts
seeds
tests
```

## 七、创建虚拟环境并安装依赖

执行：

```bash
cd /opt/freshos-worker
sudo -u freshos python3.11 -m venv .venv
sudo -u freshos /opt/freshos-worker/.venv/bin/python -m pip install --upgrade pip
sudo -u freshos /opt/freshos-worker/.venv/bin/python -m pip install -r requirements.txt
```

检查：

```bash
sudo -u freshos /opt/freshos-worker/.venv/bin/python --version
sudo -u freshos /opt/freshos-worker/.venv/bin/python -m pip show psycopg openpyxl
```

关键输出：

```text
Python 3.11.13
```

```text
Name: psycopg
Version: 3.3.4
```

```text
Name: openpyxl
Version: 3.1.5
```

## 八、配置 FreshOS

服务器配置文件路径：

```text
/etc/freshos/settings.toml
```

正确配置内容：

```toml
[database]
enabled = true
dsn = "postgresql://freshos:FreshOS_2026_change_me@127.0.0.1:5432/freshos"

[paths]
data_dir = "/var/lib/freshos/data"
report_dir = "/var/lib/freshos/reports"

[notify]
provider = "none"
webhook_url = ""

[jobs]
default_business_date = ""
```

### 纠正点 2：`freshos` 用户必须能读取配置文件

如果直接执行：

```bash
sudo -u freshos /opt/freshos-worker/.venv/bin/python scripts/run_minimal_closure.py --config /etc/freshos/settings.toml --business-date 2026-05-26
```

报错：

```text
PermissionError: [Errno 13] Permission denied: '/etc/freshos/settings.toml'
```

需要修正权限：

```bash
chown root:freshos /etc/freshos/settings.toml
chmod 640 /etc/freshos/settings.toml
ls -l /etc/freshos/settings.toml
```

正确权限示例：

```text
-rw-r----- 1 root freshos ...
```

## 九、修正 PostgreSQL 本机密码认证

### 问题表现

迁移时报错：

```text
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 5432 failed: FATAL:  Ident authentication failed for user "freshos"
```

查看认证配置：

```bash
grep -nE '^(local|host)' /var/lib/pgsql/data/pg_hba.conf
```

原始输出：

```text
84:local   all             all                                     peer
86:host    all             all             127.0.0.1/32            ident
88:host    all             all             ::1/128                 ident
91:local   replication     all                                     peer
92:host    replication     all             127.0.0.1/32            ident
93:host    replication     all             ::1/128                 ident
```

### 第一步修正：先从 `ident` 改成密码认证

备份：

```bash
cp /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.bak
```

修改：

```bash
sed -i 's/127\.0\.0\.1\/32[[:space:]]\+ident/127.0.0.1\/32            scram-sha-256/' /var/lib/pgsql/data/pg_hba.conf
sed -i 's/::1\/128[[:space:]]\+ident/::1\/128                 scram-sha-256/' /var/lib/pgsql/data/pg_hba.conf
```

检查：

```bash
grep -nE '^(local|host)' /var/lib/pgsql/data/pg_hba.conf
```

得到：

```text
84:local   all             all                                     peer
86:host    all             all             127.0.0.1/32            scram-sha-256
88:host    all             all             ::1/128                 scram-sha-256
91:local   replication     all                                     peer
92:host    replication     all             127.0.0.1/32            scram-sha-256
93:host    replication     all             ::1/128                 scram-sha-256
```

重启：

```bash
systemctl restart postgresql
```

### 第二步修正：确认数据库用户密码存储格式

虽然执行了：

```bash
sudo -u postgres psql -c "ALTER USER freshos WITH PASSWORD 'FreshOS_2026_change_me';"
```

输出：

```text
ALTER ROLE
```

但登录仍然失败。继续检查：

```bash
sudo -u postgres psql -tAc "SELECT rolname, rolpassword FROM pg_authid WHERE rolname='freshos';"
```

实际输出：

```text
freshos|md54f16e0f5568b7cf0824b7769a7bb5aaf
```

结论：

- 用户密码实际是 `md5`
- `pg_hba.conf` 要求的是 `scram-sha-256`
- 两边不一致，所以认证失败

### 第三步修正：统一改成 `md5`

执行：

```bash
sed -i 's/scram-sha-256/md5/g' /var/lib/pgsql/data/pg_hba.conf
grep -nE '^(local|host)' /var/lib/pgsql/data/pg_hba.conf
```

输出：

```text
84:local   all             all                                     peer
86:host    all             all             127.0.0.1/32            md5
88:host    all             all             ::1/128                 md5
91:local   replication     all                                     peer
92:host    replication     all             127.0.0.1/32            md5
93:host    replication     all             ::1/128                 md5
```

重启 PostgreSQL：

```bash
systemctl restart postgresql
```

再次测试登录：

```bash
PGPASSWORD='FreshOS_2026_change_me' psql -h 127.0.0.1 -U freshos -d freshos -c '\conninfo'
```

正确输出：

```text
You are connected to database "freshos" as user "freshos" on host "127.0.0.1" at port "5432".
```

## 十、执行数据库迁移

执行：

```bash
cd /opt/freshos-worker
sudo -u freshos /opt/freshos-worker/.venv/bin/python scripts/apply_migrations.py --config /etc/freshos/settings.toml
```

输出：

```text
[apply_migrations] applied migrations/001_initial_schema.sql
```

## 十一、执行最小闭环验证

执行：

```bash
cd /opt/freshos-worker
sudo -u freshos /opt/freshos-worker/.venv/bin/python scripts/run_minimal_closure.py --config /etc/freshos/settings.toml --business-date 2026-05-26
```

完整输出：

```text
[minimal_closure] applying migrations
[minimal_closure] applied migration migrations/001_initial_schema.sql
[minimal_closure] applying seed data
[minimal_closure] applied seed seeds/001_minimal_closure.sql
[minimal_closure] calculating inventory positions
[minimal_closure] inventory_positions rows=1
[minimal_closure] forecasting sales
[minimal_closure] sales_forecasts rows=1
[minimal_closure] generating order suggestions
[minimal_closure] order_suggestions rows=1
[minimal_closure] generating inventory risks
[minimal_closure] inventory_risks rows=2
[minimal_closure] exporting reports
[minimal_closure] wrote /var/lib/freshos/reports/order_suggestions_2026-05-26.csv rows=1
[minimal_closure] wrote /var/lib/freshos/reports/inventory_risks_2026-05-26.csv rows=2
```

说明：

- 数据库迁移成功
- 种子数据成功写入
- 库存口径、销量预测、订货建议、库存风险全部跑通
- 报表成功导出

## 十二、检查报表内容

检查订货建议：

```bash
sed -n '1,20p' /var/lib/freshos/reports/order_suggestions_2026-05-26.csv
```

输出：

```text
门店,商品,当前库存,预测销量,安全库存,已订未到,建议订货量,订货原因,风险标记
宝信润山店,海南香蕉,3,9.714,9.714,5,15,rule_based_v1,高风险
```

检查库存风险：

```bash
sed -n '1,20p' /var/lib/freshos/reports/inventory_risks_2026-05-26.csv
```

输出：

```text
门店,商品,风险类型,风险等级,风险说明,相关数量,处理状态
宝信润山店,海南香蕉,stockout,high,库存低于预测销量,3,open
宝信润山店,海南香蕉,high_loss,medium,报损数量高于近期日均销量,12,open
```

## 十三、检查每日摘要

执行：

```bash
sudo -u freshos /opt/freshos-worker/.venv/bin/python -m jobs.notify --config /etc/freshos/settings.toml --business-date 2026-05-26
```

输出：

```text
[notify] provider=none, skip webhook
FreshOS 订货建议 - 2026-05-26

状态：数据库已启用
需订商品：1 个
建议订货总量：15
高风险商品：1 个
缺货风险：1 个
临期/过期：0 个
待处理导入异常：0 个

附件/报表：
1. /var/lib/freshos/reports/order_suggestions_2026-05-26.csv
2. /var/lib/freshos/reports/inventory_risks_2026-05-26.csv
3. /var/lib/freshos/reports/import_exceptions_2026-05-26.csv
```

## 十四、部署成功判定

本次部署成功的标准：

1. PostgreSQL 可以用 `freshos` 用户和密码连接。
2. FreshOS 配置文件可被 `freshos` 用户读取。
3. 数据库迁移成功。
4. 最小闭环脚本成功运行。
5. 报表能生成到 `/var/lib/freshos/reports/`。
6. `notify` 能输出真实摘要。

当前结论：

```text
FreshOS V1 已在阿里云 ECS 上完成基础部署，并成功跑通最小闭环验证。
```

## 十五、常见错误与正确处理

### 错误 1：直接用 `python3`

问题：

- 系统默认 `python3` 是 3.6.8，不满足项目要求

正确做法：

```bash
python3.11 -m venv .venv
```

### 错误 2：代码目录多套一层

问题：

```text
/opt/freshos-worker/freshos-worker
```

正确做法：

```bash
shopt -s dotglob
mv /opt/freshos-worker/freshos-worker/* /opt/freshos-worker/
rmdir /opt/freshos-worker/freshos-worker
rm -rf /opt/freshos-worker/__MACOSX
```

### 错误 3：把 `Ctrl+C` 当命令输入

错误示例：

```bash
Ctrl+C
```

结果：

```text
bash: Ctrl+C: command not found
```

正确做法：

- 直接按键盘组合键 `Ctrl` + `C`
- 不要在终端里输入文字 `Ctrl+C`

### 错误 4：配置文件权限过严

问题：

```text
PermissionError: [Errno 13] Permission denied: '/etc/freshos/settings.toml'
```

正确做法：

```bash
chown root:freshos /etc/freshos/settings.toml
chmod 640 /etc/freshos/settings.toml
```

### 错误 5：`pg_hba.conf` 使用 `ident`

问题：

```text
FATAL:  Ident authentication failed for user "freshos"
```

正确做法：

- 本机 `127.0.0.1` 改为密码认证
- 最终按当前实际密码格式，统一为 `md5`

### 错误 6：密码格式和认证方式不一致

问题：

- 数据库用户密码是 `md5`
- `pg_hba.conf` 却要求 `scram-sha-256`

正确做法：

```bash
sed -i 's/scram-sha-256/md5/g' /var/lib/pgsql/data/pg_hba.conf
systemctl restart postgresql
```

## 十六、下一步建议

下一步优先做：

1. 配置 `systemd timer` 或 Hermes 定时执行 `jobs.run_daily`
2. 接正式大表哥 `40/42` 基础数据
3. 验证正式门店 / 商品 / 门店商品关系导入
4. 验证正式销售、库存、订货、收货、订单、盘点数据导入
5. 配置企业微信或飞书 webhook，替换 `provider=none`


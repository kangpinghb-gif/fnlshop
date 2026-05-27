# FreshOS Worker 阿里云 ECS 部署指南

适用目标：阿里云 ECS 上部署 FreshOS V1 worker、PostgreSQL、定时任务和最小闭环验证。

默认假设：

- Ubuntu 22.04 / 24.04 LTS。
- PostgreSQL 安装在同一台 ECS，仅监听 `127.0.0.1`。
- 代码部署目录：`/opt/freshos-worker`。
- 配置文件：`/etc/freshos/settings.toml`。
- 数据和报表目录：`/var/lib/freshos/data`、`/var/lib/freshos/reports`。

## 一、安全组建议

阿里云安全组只需要开放：

- SSH：`22`，建议只允许你的固定公网 IP。

不要向公网开放：

- PostgreSQL：`5432`
- 任何内部 worker 端口

V1 worker 没有 Web 服务，正常不需要开放 HTTP/HTTPS。

## 二、服务器初始化

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib

sudo useradd --system --create-home --home-dir /opt/freshos-worker --shell /usr/sbin/nologin freshos
sudo mkdir -p /etc/freshos /var/lib/freshos/data /var/lib/freshos/reports
sudo chown -R freshos:freshos /var/lib/freshos
```

## 三、创建 PostgreSQL 用户和数据库

请把 `change-me` 换成强密码。

```bash
sudo -u postgres psql
```

进入 `psql` 后执行：

```sql
CREATE USER freshos WITH PASSWORD 'change-me';
CREATE DATABASE freshos OWNER freshos;
\q
```

确认 PostgreSQL 只监听本机：

```bash
sudo grep -n "listen_addresses" /etc/postgresql/*/main/postgresql.conf
```

推荐保持：

```text
listen_addresses = 'localhost'
```

## 四、部署代码

把本地 `freshos-worker` 目录上传到服务器 `/opt/freshos-worker`。

示例：

```bash
sudo rsync -av --delete ./freshos-worker/ /opt/freshos-worker/
sudo chown -R freshos:freshos /opt/freshos-worker
```

创建虚拟环境并安装依赖：

```bash
sudo -u freshos python3 -m venv /opt/freshos-worker/.venv
sudo -u freshos /opt/freshos-worker/.venv/bin/python -m pip install --upgrade pip
sudo -u freshos /opt/freshos-worker/.venv/bin/python -m pip install -r /opt/freshos-worker/requirements.txt
```

## 五、配置 FreshOS

复制配置模板：

```bash
sudo cp /opt/freshos-worker/config/settings.aliyun.example.toml /etc/freshos/settings.toml
sudo chmod 600 /etc/freshos/settings.toml
```

编辑 DSN 密码：

```bash
sudo nano /etc/freshos/settings.toml
```

确认：

```toml
[database]
enabled = true
dsn = "postgresql://freshos:change-me@127.0.0.1:5432/freshos"
```

## 六、初始化数据库并跑最小闭环

```bash
cd /opt/freshos-worker

sudo -u freshos .venv/bin/python scripts/apply_migrations.py --config /etc/freshos/settings.toml
sudo -u freshos .venv/bin/python scripts/run_minimal_closure.py --config /etc/freshos/settings.toml --business-date 2026-05-26
```

预期结果：

- `inventory_positions rows=1`
- `sales_forecasts rows=1`
- `order_suggestions rows=1`
- `inventory_risks rows` 大于等于 1
- `/var/lib/freshos/reports/order_suggestions_2026-05-26.csv`
- `/var/lib/freshos/reports/inventory_risks_2026-05-26.csv`

## 七、配置 systemd 定时任务

```bash
sudo cp /opt/freshos-worker/deploy/systemd/freshos-worker.service /etc/systemd/system/freshos-worker.service
sudo cp /opt/freshos-worker/deploy/systemd/freshos-worker.timer /etc/systemd/system/freshos-worker.timer

sudo systemctl daemon-reload
sudo systemctl enable --now freshos-worker.timer
```

手动执行一次：

```bash
sudo systemctl start freshos-worker.service
```

查看日志：

```bash
journalctl -u freshos-worker.service -n 200 --no-pager
```

查看定时器：

```bash
systemctl list-timers freshos-worker.timer
```

## 八、Hermes 接入

如果阿里云服务器上使用 Hermes 调度，可以先不启用 systemd timer，让 Hermes 调用：

```bash
cd /opt/freshos-worker
/opt/freshos-worker/.venv/bin/python -m jobs.run_daily --config /etc/freshos/settings.toml
```

建议 Hermes 环境保留：

```text
WorkingDirectory=/opt/freshos-worker
Config=/etc/freshos/settings.toml
```

## 九、生产前检查清单

- `settings.toml` 权限是 `600`。
- PostgreSQL 没有对公网开放 `5432`。
- 阿里云安全组只对可信 IP 开放 SSH。
- `/var/lib/freshos/reports` 有写权限。
- `journalctl -u freshos-worker.service` 没有错误。
- 最小闭环种子数据已经跑通。
- 正式大表哥 `40/42` 数据导入前，先备份数据库。


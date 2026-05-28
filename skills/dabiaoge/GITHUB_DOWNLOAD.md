# 大表哥 Skill 通过 GitHub 分发

用途：把 FreshOS 的大表哥导出规则放到 GitHub，Hermes 所在服务器通过 GitHub 下载后执行。

## 一、仓库内文件

需要上传到 GitHub 的文件：

```text
skills/dabiaoge/SKILL.md
```

如果 Hermes 需要读取辅助脚本，也一并上传：

```text
skills/dabiaoge/scripts/get_keychain_password.sh
```

注意：不要把大表哥账号、密码、验证码、Cookie、Session 或 Token 写入仓库。

## 二、上传到 GitHub

在本机项目目录执行：

```bash
git status
git add skills/dabiaoge/SKILL.md skills/dabiaoge/GITHUB_DOWNLOAD.md skills/dabiaoge/scripts/get_keychain_password.sh
git commit -m "docs: add dabiaoge skill github download guide"
git remote add origin git@github.com:你的GitHub用户名/你的仓库名.git
git push -u origin main
```

如果已经配置过 `origin`，不要重复执行 `git remote add origin`，直接执行：

```bash
git push
```

## 三、服务器下载

在 Hermes 所在服务器执行：

```bash
mkdir -p /opt/hermes/skills/dabiaoge

curl -fsSL \
  https://raw.githubusercontent.com/kangpinghb-gif/fnlshop/main/skills/dabiaoge/SKILL.md \
  -o /opt/hermes/skills/dabiaoge/SKILL.md

ls -lh /opt/hermes/skills/dabiaoge/SKILL.md
head -n 20 /opt/hermes/skills/dabiaoge/SKILL.md
```

如果服务器没有 `curl`，用 `wget`：

```bash
mkdir -p /opt/hermes/skills/dabiaoge

wget -O /opt/hermes/skills/dabiaoge/SKILL.md \
  https://raw.githubusercontent.com/kangpinghb-gif/fnlshop/main/skills/dabiaoge/SKILL.md
```

## 四、给 Hermes 的执行指令

```text
请读取服务器文件：

/opt/hermes/skills/dabiaoge/SKILL.md

按其中规则执行 FreshOS V1 大表哥导出任务。

要求：
1. 只导出大分类编码 40,42。
2. 导出文件放到 /var/lib/freshos/data/。
3. 文件名使用：
   dabiaoge_base_40_42_YYYY-MM-DD.xlsx
   dabiaoge_sales_40_42_YYYY-MM-DD.xlsx
   dabiaoge_inventory_loss_40_42_YYYY-MM-DD.xlsx
   dabiaoge_purchase_receipts_40_42_YYYY-MM-DD.xlsx
   dabiaoge_inventory_snapshot_40_42_YYYY-MM-DD.xlsx
4. 导出后先校验文件存在、非空、表头字段正确、只包含 40/42。
5. 校验成功后触发 freshos-worker 导入和计算链路；当前导入任务必须显式传入 --input 文件路径。
6. 任一必需文件导出或校验失败时停止链路并反馈错误。
7. 不要保存明文账号密码、验证码、Cookie、Session 或 Token。
```

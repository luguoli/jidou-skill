# 可选本地扩展

本页只在用户明确选择本地独立存储/后台时读取；安装技能、换 Agent 或云端接口暂时失败，都不构成选择本方案。优先复用所在平台已有的存储与调度。
本扩展随技能提供，不依赖 library 或 automation-task-manager。需要能读写本机文件、执行 Python 3.10+ 的 agent；没有本机工具的纯聊天或远程沙箱不能凭安装 SKILL.md 访问这份数据库。

## 先选择后端

已有云端用户保持原后端。只有用户明确选择由本包保存到本地数据库时才使用 SQLite，单纯把技能安装在本机并不等于选择本地存储。不能把云端失败自动解释成新建本地数据。
SQLite 文件 jidou.sqlite3 保存本地方案的21字段记录、原文、设置、幂等键、期次关系、提醒队列与任务运行回执；它不是 Excel 文件，也不是云端库的缓存。本机数据不自动同步到云端。
下列示例在技能目录执行；agent 调用时使用本技能中 `scripts/jidou.py` 的实际绝对路径。`python` 指 Python 3.10+，macOS 常用 `python3`，Windows 也可用 `py -3`。

```bash
python -m pip install -r requirements.txt
python scripts/jidou.py doctor
python scripts/jidou.py init --timezone Asia/Shanghai
```

doctor 不创建目录、数据库或任务。只有 init 明确创建本地数据库，重复 init 保留原 ID、数据与设置，不重置。

默认数据位置：Windows `%LOCALAPPDATA%\jidou`；macOS `~/Library/Application Support/jidou`；Linux `$XDG_DATA_HOME/jidou`，未设置则 `~/.local/share/jidou`。
同一用户的 Codex、Claude Code、TRAE 默认读同一份本机数据。用环境变量 JIDOU_HOME 或全局 `--home <目录>` 选择其他数据目录；后台注册也固定该绝对路径。
这是本机持久化，不是跨电脑同步；不要把正在使用的 SQLite/WAL 放进网盘当成多机并发数据库。跨电脑用核验后的导出/导入或明确配置的云端后端。

## 记录、查询和更新

先将实际数据安全序列化为 UTF-8 JSON 文件，不把用户原话拼进 shell。支持21个中文字段的普通字符串，也可接收 library 的单层 text/select/date 包装。

```json
{
  "内容": "周报自动化：希望从聊天记录生成周报",
  "原文": "那个周报啊，能不能自己从聊天记录里长出来",
  "类型": "想法",
  "领域": "工作",
  "标签": "效率、自动化"
}
```

```bash
python scripts/jidou.py add --input /absolute/path/record.json --operation-id request-unique-id
python scripts/jidou.py list --domain 工作 --status 待看 --limit 20 --offset 0
python scripts/jidou.py list --query 周报
python scripts/jidou.py get RECORD_ID
python scripts/jidou.py update RECORD_ID --input /absolute/path/changes.json
python scripts/jidou.py complete RECORD_ID
```

原文必须显式提供；系统生成记录可显式填空。脚本不把摘要伪造成原话，也不声称能自动识别所有秘密；agent 仍应按 SKILL.md 在写入前处理敏感输入。
批量写入用 `{"records":[记录1,记录2]}`，全批在一个事务内完成；一个不合法则全部回滚。同一 operation-id 重放相同载荷返回相同记录，不同载荷拒绝；不同操作不要复用同一个键。
线索在写事务中分配，跨 agent 并发不会因先读后写而撞号。显式指定同一线索仍可关联多条独立记录，状态不联动。
list 返回 total/limit/offset 与内部完整字段，逐页读取。普通检索回复不展示原文；用户明确追溯时才展示所需原话，不将完整 JSON 直接贴给用户。

## 提醒

有时间的记录同时填写到期与提醒；只有日期时按用户已知约定设9点并说明。循环规则和自定义提前量沿用 [reminders.md](reminders.md)；不通过挪动真实事件日期实现提前提醒。

```json
{"内容":"交房租","原文":"每月8号交房租，提前两天提醒","类型":"待办","领域":"财务","到期":"2026-12-08T10:00:00+08:00","提醒":"准时","重复":"{\"rule\":\"每月8号 10:00\",\"lead_minutes\":2880}"}
```

```bash
python scripts/jidou.py reminders scan
python scripts/jidou.py reminders pending
python scripts/jidou.py reminders deliver --channel stdout
python scripts/jidou.py reminders run --channel system
```

scan 在 SQLite 事务内同时排入通知队列和推进循环，自己不表示通知已送达。deliver 使用租约领取并在通道接受后标为 accepted；系统接受不代表用户看见或读过。
stdout 通道输出通知 JSONL，供当前 agent/管道消费，最后有汇总 JSON；它不是跨聊天通知接口。system 通道调用本机桌面通知；webhook 通道只使用 `--webhook-env 环境变量名` 引用的地址，远端要求 HTTPS。Webhook 接收方可用 X-Jidou-Delivery-Key 幂等去重。
失败保留待发队列，默认5分钟后再试；崩溃后租约可回收。外部投递与本地事务不原子，接收成功但确认前崩溃仍可能重复；不能承诺恰好一次。
夜间静默和暂停期间不领取通知，批次中跨入静默也会停下；更正内容会在领取时反映，改期或完成会取消尚未送出的旧事件。已经交给系统的通知不能撤回。

```bash
python scripts/jidou.py settings show
python scripts/jidou.py settings update --input /absolute/path/settings.json
```

设置 JSON 可修改 timezone、quiet_start_hour、quiet_end_hour、catchup_hours、reminders_enabled。默认22–8静默、补最近24小时。设 reminders_enabled=false 暂停；显式恢复后从恢复时刻接管，不轰炸暂停期间旧提醒。
后台扫描/系统投递仍需 [安装后台任务](install.md)；电脑休眠、离线、长任务与系统通知设置会影响时间。默认每分钟唤醒检查，不保证每条一分钟送达。

## 本期完成、跳过和撤销

```bash
python scripts/jidou.py complete RECORD_ID --event-at 2026-12-08T10:00:00+08:00 --original "这期已经交了"
python scripts/jidou.py skip RECORD_ID --event-at 2026-12-08T10:00:00+08:00
python scripts/jidou.py undo RECEIPT_ID --restore-reminder
```

循环必须指定准确期次，完成/跳过回执和模板推进在同一个事务里，重复完成不会再加一条。撤销不删除历史；只有原提醒还未到、没有后续已处理期次时才恢复。已过去的期次要另行明确安排提醒，不能用诊断时间参数偷偷补发。
原生执行任务的完成来自实际 run 回执，不能用上述普通 complete 假装命令已经运行；停用用 job disable 或明确归档其登记记录。

## 本地命令任务

本地原生任务只执行用户明确配置的 argv 数组，不解释记录正文中的命令，不隐式启用 shell。

```json
{"name":"每天生成日报","argv":["/absolute/path/python","/absolute/path/daily.py"],"repeat":"每天 08:00","timeout_seconds":300,"cwd":"/absolute/path/project","env_refs":{"API_TOKEN":"JIDOU_API_TOKEN"}}
```

Windows 使用实际 python.exe 和脚本路径。环境映射只保存变量名；值在后台运行时从该进程环境读取。argv 不展开 `$TOKEN`，需要秘密的程序自己读取环境变量，不把秘密写进 recipe 或执行内容。

```bash
python scripts/jidou.py job add --input /absolute/path/job.json
python scripts/jidou.py job list
python scripts/jidou.py job tick
python scripts/jidou.py job runs --job JOB_ID
python scripts/jidou.py job disable JOB_ID
python scripts/jidou.py job enable JOB_ID --next-run 2026-12-08T10:00:00+08:00
python scripts/jidou.py job resolve RUN_ID --status success
```

一次性用 run_at，循环用 repeat，可同时用 run_at 给首次发生/锚点。每期先持久登记运行，再执行，既有期次不自动重放；超时或崩溃可能已有外部动作，未知运行会阻止该任务继续，先核实后 resolve，不把“未知”当作“没执行”。
原生任务默认串行，长任务可能影响同一后台批次的排队；需要独立并行/QoS时使用明确配置的外部任务服务。stdout/stderr 不写入回执，避免意外存入秘密；实际业务产物由任务写到用户选定的位置，退出码0只证明进程成功。
云端 API/技能/组合仍可走 [云端执行适配](execution.md)。本地也可显式调用已安装的 agent CLI 或 HTTP 工具，但必须验证后台工具、账户、凭据和动作授权；不假定任意 agent 有统一 API 或当前聊天的连接。

## 导出、导入、备份和诊断

```bash
python scripts/jidou.py export
python scripts/jidou.py import --input /absolute/path/export.json
python scripts/jidou.py backup --output /absolute/path/new-backup.sqlite3
python scripts/jidou.py doctor
```

export 输出完整 JSON，保留原文、21字段、记录ID与时间；保存输出时显式使用 UTF-8 文件，避免旧版 PowerShell 重定向改成 UTF-16。import 只接收 jidou JSON 导出，原子导入并重绑/恢复循环期次关系；ID冲突会拒绝，不覆盖现有记录。
记录导入不自动恢复待发队列、可执行 job 或系统注册；完整本地备份使用 SQLite backup API，不能只复制活跃的主库而遗漏 WAL。备份目标必须新建，不允许覆盖源库或其保留侧文件。
doctor 显示所选数据目录、记录数、队列状态、最近扫描和不确定运行。保存过调度注册回执不证明系统任务仍存在；结合实际 OS 任务状态与 last_scan 核对。
`--now` 仅用于隔离诊断/测试，实际后台命令不要使用；它可改变逻辑到时时刻，不能用在真实数据上模拟执行未来动作。

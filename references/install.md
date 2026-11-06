# 安装技能与可选本机后台

## 安装完整技能包

优先通过所在平台的技能导入功能安装，或手动复制/解压完整技能包到实际技能目录，目录名为 jidou；这些操作不需要 Python。包含 SKILL.md、references 和随包 scripts，不只复制入口。
WorkBuddy 使用技能导入/上传入口；云端使用时要核对技能在云端执行环境可见，接回原 library 数据表与 automation-task-manager，不运行本机 init/scheduler 来代替云端接入。参考 [WorkBuddy技能说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。
其他 Agent 的常见手动安装目录如下；它们是否有云端存储接口取决于实际连接，与技能是否已加载分开检查。

| agent | 项目目录 | 用户目录 |
|---|---|---|
| codex | 项目/.agents/skills/jidou | ~/.agents/skills/jidou |
| claude | 项目/.claude/skills/jidou | ~/.claude/skills/jidou |
| trae | 项目/.trae/skills/jidou | 中国版 ~/.trae-cn/skills/jidou |

国际版 TRAE 优先使用已明确的项目安装；全局路径须按实际版本核实，本安装器不凭猜测写入国际版全局目录。
目录约定参考 [Codex官方文档](https://learn.chatgpt.com/docs/build-skills)、[Claude Code官方文档](https://code.claude.com/docs/en/skills)、[TRAE官方文档](https://docs.trae.cn/ide_skills?lang=zh)。平台策略/信任设置可能影响发现，安装后在目标 agent 确认 jidou 可见。

也可使用随包的 **可选 Python 复制工具**，它不是安装技能的唯一方式。只有运行该工具时才需要在执行位置准备 Python 3.10+；不因工具缺失阻止手动导入：

```bash
python scripts/jidou.py install --agent codex --scope user
python scripts/jidou.py install --agent codex --scope user --apply
python scripts/jidou.py install --agent claude --scope project --project /absolute/path/project --apply
python scripts/jidou.py install --agent trae --scope project --project /absolute/path/project --apply
```

安装器复制完整的 SKILL.md、references、scripts、测试和依赖声明，不复制数据库、导出、缓存或 archive。不仅复制一个 SKILL.md。
默认只给计划；--apply 才写目录。已有未托管目录拒绝覆盖；托管更新保留旧包备份，遇额外用户文件先拒绝，不能删除用户文件。安装不会初始化本地数据、注册后台或迁移云端数据。
只有各安装都明确选择本地扩展时，才使用同一个默认用户数据目录；自定义 JIDOU_HOME/--home 时需保持一致。远程 agent 在远程环境运行，不能自动读到本机数据库。

## 可选本机后台

以下只适用于用户明确选择 [本地 Python/SQLite 扩展](local-runtime.md) 并要求本机提醒/执行的情形。WorkBuddy 云端及其他平台已有调度优先用其自身后台，不执行下面的本机初始化或系统注册；没有选择本地方案时不要求安装 Python。

### 先确认数据和通知通道

```bash
python scripts/jidou.py doctor
python scripts/jidou.py init --timezone Asia/Shanghai
python scripts/jidou.py reminders pending
```

只有选择本地存储并授权初始化才运行 init。后台任务只在用户明确要求启用时注册。
system 使用登录桌面的本机通知；OS接受请求不证明可见，勿扰、权限、锁屏和会话状态会影响显示。Windows原生通知不需要把用户文本拼进PowerShell代码，macOS文本通过osascript参数传入。
webhook 通过环境变量引用地址，后台进程必须能读到该变量；当前交互 shell 中的临时变量不一定会传到计划任务/LaunchAgent。可先用 stdout 通道在隔离数据上测试，stdout 不是系统推送。

### Windows 与 macOS 原生计划

```bash
python scripts/jidou.py scheduler plan --channel system
python scripts/jidou.py scheduler install --channel system --apply
python scripts/jidou.py scheduler status
```

计划输出实际 Python 解释器与脚本的绝对路径、数据目录、命令/配置和唯一任务名；默认不注册。使用本机计划，跨系统 plan 只是预览，不能在 Windows 上应用 macOS 配置。

| 系统 | 实现 | 运行条件 |
|---|---|---|
| Windows | 用户任务计划，每分钟启动 worker，交互会话模式，不提权、不保存密码 | 用户已登录、Python与脚本路径仍有效 |
| macOS | ~/Library/LaunchAgents 下的本用户 plist，StartInterval=60，参数数组传递 | 用户图形会话、有效的解释器与通知能力 |
| Linux | 输出明确的 worker 命令，由用户选择现有 cron/systemd 调度 | 本版本不自动改 crontab 或 systemd |

实现约定参考 [Microsoft Schtasks文档](https://learn.microsoft.com/en-us/windows/win32/taskschd/schtasks)、[Apple LaunchAgent文档](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)。
后台运行 `work`：扫描、投递提醒，再处理明确配置的原生命令任务。无需保持 agent 聊天打开，但电脑休眠、注销、执行排队会延迟运行，不是24小时云托管服务。
安装器不覆盖同名系统任务或plist，也不自动修改已登记的后台配置。更新/停用系统注册时按计划返回的唯一名字在任务计划程序或launchctl中核对，再处理；不删除数据库。
记录、单项提醒暂停或全局 reminders_enabled=false 不要求删除系统注册；job disable只停未来执行，不证明已经在跑的外部动作已终止。

### 本机扩展验收范围

Windows主机可执行本地CLI与隔离命令测试；macOS/Linux目标配置可以进行参数和格式检查。没有在目标真机完成注册、调用通知和确认回执前，不宣称原生投递已验证。
发布测试不自动注册开发者的真实任务或给其桌面发测试通知。用户实际部署后核对 scheduler 状态、doctor.last_scan、通知队列的 pending/accepted 和 job runs；错误先修依赖，不换库或重建来掩盖。

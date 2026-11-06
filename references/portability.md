# 平台适配边界

记兜的核心是标准技能说明与记录规则，优先复用所在平台已有的存储、表格、连接器和调度。加载技能不要求 Python；能加载、能读写数据、后台已运行、通知已显示须分别确认。

## 平台与可选方案

| 环境 | 优先使用 | 条件与边界 |
|---|---|---|
| WorkBuddy 云端 | 原有 library 云端数据表与 automation-task-manager | 沿用原 ID；技能、接口、凭据和脚本依赖在实际云端核验，不要求用户电脑先装 Python |
| Codex | 已连接的存储与后台；技能可装 .agents/skills | 不自动获得 WorkBuddy 接口；可手动安装技能，无统一 Python 前置 |
| Claude Code | 已连接的存储与后台；技能可装 .claude/skills | 同上；纯聊天的 Claude 网页不因此获得本机文件访问 |
| TRAE | 已连接工具；项目 .trae/skills，中国版用户 .trae-cn/skills | 国际版用户全局目录按版本核实，不猜路径；不强制本地数据库 |
| Windows / macOS / Linux | Agent 在该环境中实际可用的工具 | 操作系统不决定必须用 SQLite 或哪个云服务，先接回已有数据 |
| 其他标准技能加载器 | 标准 SKILL.md 与该宿主工具 | 记录规则可复用，运行接口须按实际能力验证 |
| 远程沙箱/纯聊天 | 沙箱工具或明确连接的服务 | 不会自动访问用户电脑的数据或桌面；没有存储就说明尚未保存 |

目录与平台导入见 [install.md](install.md)，按任务检查依赖见 [dependencies.md](dependencies.md)。跨 Agent 共用数据，须访问同一实际存储，不是靠安装同一个技能包自动同步。

## 可选本地扩展

只有用户明确选择独立本地存储/后台才读取 [local-runtime.md](local-runtime.md)，使用 Python 3.10+ 和 jidou.sqlite3。它不替代已有云端方案，也不自动创建或迁移用户数据。

| 扩展目标 | 提供内容 | 验证范围 |
|---|---|---|
| Windows | 本地 SQLite/CLI、用户任务计划和桌面通知入口 | 核心 CLI、并发与隔离命令在 Windows 实跑；OS 调用参数检查，未注册真实任务或发通知 |
| macOS | 同一本地 CLI、LaunchAgent 和 osascript 通知入口 | 时区/参数/plist 检查，尚未在 macOS 真机验证注册与桌面投递 |
| Linux | 同一本地 CLI；通知需 notify-send；worker 可交现有后台服务 | 可移植逻辑有检查，尚未真机验证；不自动改 cron/systemd |

同一主机/用户/数据目录的本地安装可共用 SQLite；跨电脑不能用活跃的 SQLite/WAL 网盘同步冒充并发数据库。记录导出与完整备份恢复范围不同，不将记录导入说成恢复全部后台状态。

## 入口与依赖

SKILL.md 使用标准 name/description/license/metadata。旧版顶层 slug/displayName/version 等平台字段不再是必需协议；展示名与版本在 metadata。若平台要求其他字段，用专用配置映射，保留标准入口。
仓库叫 jidou-skill，技能目录叫 jidou。导入完整包，不只复制入口；导入/手动复制本身不要求 Python。随包渲染/校验脚本才需要 Python/PyYAML，详见 dependencies.md；工具在云端运行，就在云端检查依赖。不要假定平台预装，也不把云端问题转为要求用户配置本机。
可选本地农历计算使用 lunardate 支持的1900–2099年范围，超界报告而非猜测。权限或工具不足时减少受影响操作，不自动换库或扩大权限。

## 云端适配与验收

原有云端方案依赖外部 library 与 automation-task-manager，它们不随包提供。此方案保留不等于所有 WorkBuddy 版本均已实测；改路径也不能代替 API/鉴权适配。其他平台接入同类工具时，按顺序核验：

1. 21字段名称/顺序/类型/枚举、时间精度、分页过滤、幂等、空值更新与部分成功。
2. 账号、空间、对象归属、原配置与跨设备可读性。
3. cron 段数/星期编号、时区、启停、配额、重试、运行与真实投递的区别。
4. 后台工具、网络、凭据引用、业务回执和产物位置。

现有 reminder 渲染器输出 POSIX shell 的 library 命令，SKILLS_DIR 是后台实际绝对 POSIX 路径；用户电脑是 Windows 不代表云端后台也是 Windows。只有在实际 Windows 本机选用本地扩展时才用 Windows 原生任务计划，不能把盘符填进 POSIX 模板。
先以合成数据核验中文、引号/多行原文、独立状态、分页、日期偏移、循环与失败恢复，再迁移真实记录。无存储或后台时如实报告，不能以生成模板、保存注册回执代替真实运行与投递验收。

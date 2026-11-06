# 平台适配边界

记兜包含两个明确选择的运行方案：随包本地 CLI 和保留的云端适配器。入口可加载、脚本可运行、后台已注册、通知已显示是四件独立的事。

## 兼容矩阵

| 环境 | 随包本地方案 | 条件与验证范围 |
|---|---|---|
| Codex | 提供 .agents/skills 安装 | 需要当前环境可读写数据并执行 Python；安装后确认技能被发现 |
| Claude Code | 提供 .claude/skills 安装 | 同上；纯聊天的 Claude 网页不因此获得本机文件访问 |
| TRAE | 提供项目 .trae/skills；中国版用户 .trae-cn/skills | 国际版用户全局目录需按实际版本核实，安装器不猜路径 |
| Windows | SQLite、CLI、用户任务计划和桌面通知入口 | 本版本在 Windows 实跑核心 CLI、并发与隔离命令；系统调用配置/参数测试，不自动注册真实任务或发通知 |
| macOS | 同一 CLI、LaunchAgent 和 osascript 通知入口 | 时区和参数数组有测试；尚未在 macOS 真机验证后台注册与桌面投递 |
| Linux | 同一 CLI；原生通知需要 notify-send；后台由现有服务调用 worker | 可移植逻辑有测试，尚未真机验证；本版本不自动改 cron/systemd |
| 其他标准技能加载器 | 可读取标准 SKILL.md，并按实际目录安装完整包 | 能否执行 Python、访问本机或投递消息须单独验证 |
| 远程容器/纯聊天 | 视宿主工具能力而定 | 不会自动访问用户电脑的数据或桌面；需要显式数据与通知连接 |

安装路径、来源和原生集成见 [install.md](install.md)，数据位置与命令见 [local-runtime.md](local-runtime.md)。多个 Agent 的共享以同一用户、同一实际数据目录为前提；跨设备用明确的导出/导入或云端后端。

## 入口与依赖

SKILL.md 使用标准 name/description/license/metadata。旧版顶层 slug/displayName/version 等平台专用字段不再是必需协议；中文、英文名称与版本在 metadata。若平台要求其他字段，用专用配置映射，保留标准入口。
仓库叫 jidou-skill，技能目录叫 jidou。安装须包含 references、scripts 和 requirements.txt，不能只复制入口。执行脚本需要 Python 3.10+、PyYAML、可用 IANA 时区数据；农历计算使用 lunardate 支持的1900–2099年范围，超界应报告而非猜测。
执行环境有权限限制时报告具体缺少的能力，不自动改用另一份数据或扩大权限。

## 云端适配

云端方案仍依赖外部 library 与 automation-task-manager，它们不随包提供；改路径不能代替 API 与鉴权适配。按顺序核验：

1. 存储21字段名称/顺序/类型/枚举、时间精度、分页过滤、幂等、空值更新及部分成功。
2. 账号、空间、对象归属、云端配置与跨设备可读性。
3. cron 段数/星期编号、时区、启停、配额、重试、运行与真实投递的区别。
4. 后台工具、网络、凭据引用、业务回执和产物位置。

旧 reminder 渲染器继续输出 POSIX shell 的 library 命令，SKILLS_DIR 是后台真实绝对 POSIX 路径。Windows 盘符不能填进旧模板冒充可运行；Windows 本地使用本版本原生 CLI 和任务计划入口。schema/config 的渲染本身不依赖目标 shell。

## 迁移验收

先在隔离目录用合成数据验证中文、引号/多行原文、同线索独立状态、分页、日期偏移、循环、失败恢复，再处理真实记录。数据库导出与完整备份的恢复范围不同，不将记录导入说成恢复全部后台状态。
能力不足时减少可用操作，不删 schema 字段或枚举。能记录但没有后台时说明提醒/执行尚未启用；任务保存过注册回执也要核对 OS 任务和最近扫描，不能据此承诺已经投递。

# 记兜 · jidou

聊天里的个人收集箱。把随口说的想法、待办和琐事接住，保留原话、自动归类，需要时找回、提醒或执行。

> 「记一下：周报能不能从聊天记录自动生成。」
> 「每月5号交房租，提前两天提醒。」
> 「关于老张的那些事，我都记哪了？」

## 能做什么

| 能力 | 行为 |
|---|---|
| 记录 | 一件事一行，摘要与原话分开；按类型、领域、标签、相关人归类 |
| 线索 | 同一主题多次补充，共用稳定编号，回看演进 |
| 回读和整理 | 按人、日期、主题、状态找回；整理、复盘、习惯打卡 |
| 提醒 | 一次性、循环、自定义提前量、静音和单次改期；保留真实事件时间 |
| 定时执行 | 明确配置的本地命令，或通过云端适配器调用 API、技能与组合流程 |

完整示例见 [使用说明](references/onboarding.md)。普通闲聊不自动保存，指定其他保存位置时尊重该位置。

## 安装

需要 Python 3.10+。macOS 通常使用 `python3`，Windows 可用 `python` 或 `py -3`。在实际安装的解释器环境中安装依赖：

```bash
git clone https://github.com/luguoli/jidou-skill.git
cd jidou-skill
python -m pip install -r requirements.txt
python scripts/jidou.py install --agent codex --scope user
python scripts/jidou.py install --agent codex --scope user --apply
```

安装命令默认预览，`--apply` 才复制完整技能包。Claude Code 用 `--agent claude`；TRAE 可用 `--agent trae --scope project --project 项目绝对路径`。详见 [各 Agent 的安装目录与更新规则](references/install.md)。

入口是标准 **SKILL.md：YAML 元数据头 + Markdown 正文**，说明见 [格式约定](references/format.md)。只加载入口不要求 Python；使用随包脚本时需安装 requirements.txt，含 PyYAML、Windows 时区数据及农历换算库。

## 选择存储与后台

| 模式 | 依赖与用途 |
|---|---|
| 本地 | 随包 SQLite 与统一 CLI；同一用户的多个 Agent 可共用本机数据，适合 Windows、macOS、Linux |
| 云端 | 沿用已有 library 与 automation-task-manager，适合已经接好的云端实例；这些服务不随包提供 |

**安装技能不等于创建收集箱或启用后台。** 已有用户继续接回原数据；新用户明确选择本地后，可在已安装的技能目录执行：

```bash
python scripts/jidou.py doctor
python scripts/jidou.py init --timezone Asia/Shanghai
```

doctor 只检查，init 才创建数据库。日常由 Agent 按 [本地操作说明](references/local-runtime.md) 记录、查询和更新。
本地数据在系统用户数据目录；多个 Agent 要使用相同目录。跨电脑需导出/导入或配置云端后端，不会自动同步；远程沙箱不能自动访问本机文件。

需要脱离聊天的提醒或执行时，另行预览并明确启用系统后台：

```bash
python scripts/jidou.py scheduler plan --channel system
python scripts/jidou.py scheduler install --channel system --apply
```

Windows 使用用户任务计划，macOS 使用 LaunchAgent；默认每分钟唤醒。Linux 提供 worker 命令供现有调度服务使用。电脑休眠、注销、通知权限和长任务会影响运行；不承诺精确到分钟或用户一定读到通知。
本地队列失败可重试，外部通知仍不能保证严格一次；通道接受与用户读到分别看待。原生命令任务只执行明确登记的 argv，不执行普通记录里的文字。

云端默认共享扫描仍为每小时，模板使用 POSIX 工具链。两种模式默认22:00–08:00静默，可配置时区。不要因云端故障悄悄创建本地替代库。[兼容范围与验收边界](references/portability.md)、[已有安装升级](references/upgrade.md)。

## 文件与验证

```text
jidou/
├── SKILL.md                 标准入口
├── references/              流程、schema、默认值与模板
├── scripts/jidou.py         通用本地 CLI
├── scripts/jidou_runtime/   存储、循环、队列、任务与原生集成
├── scripts/render.py        云端模板渲染
├── scripts/validate.py      包的一致性校验
└── tests/                   合成数据的离线测试
```

保留原有21字段、类型、顺序和枚举，[schema.json](references/schema.json) 是机器定义；SQLite 运行元数据独立存放，不增改业务字段。原文逐字保存，普通摘要与通知使用整理后的内容。Agent 在写入前处理敏感输入，不把密码或密钥放入任何字段。

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
```

[维护检查](references/consistency.md) 包含回归与行为验收。Windows 主机验证本地 CLI 和隔离命令；macOS/Linux 进行可移植逻辑与配置检查，尚未在目标桌面验证真实后台注册和通知。测试不会自动创建个人系统任务或向桌面推送。

当前版本 **2.13.0**，详见 [CHANGELOG](CHANGELOG.md)。许可证：[MIT](LICENSE)。

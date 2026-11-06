---
name: jidou
description: >-
  记兜（jidou）是聊天中的个人收集箱。用户说“记一下”“帮我记住”“这个留着”、
  要补充旧想法、查找过去的记录、整理碎片、管理待办和提醒，或明确要求定时执行时使用。
  Capture, recall and organize personal notes, ideas, tasks and reminders. Use for
  "make a note", "remember this", "save this", "add a task", "remind me", or requests
  to find old notes, organize ideas, check in, or schedule an action.
  保留用户原话，按类型和领域归类；明确指定其他保存位置时走对应工具，普通闲聊不自动存储。
license: MIT
metadata:
  version: "2.14.2"
  display_name: "记兜"
  display_name_en: "jidou"
  category: "productivity"
---

# 记兜 · jidou

接住聊天里的想法和琐事，整理后能找回，需要时提醒或执行。先完成用户本次请求，再按需展开能力。
优先使用所在平台已有的存储、表格、连接器和调度能力，沿用用户已有数据。加载或安装本技能不要求先装 Python；随包 Python/SQLite 只是明确选择后才使用的本地扩展，不能因接口失败偷偷换库。

## 语言与时区 / Language and locale

按用户当前请求或明确偏好回复，英文输入就用英文回应；原文逐字保留，不翻译后覆盖。类别/日期/循环由 agent 映射到已有工具格式，不要求用户说中文。语言不代表国家、日期格式或时区，已有配置优先；新定时请求时区未知或日期有歧义时先确认。
For English requests, read the [language and locale guide](references/language.md). Respond in English, preserve original wording, and translate tool parameters rather than asking the user to learn Chinese schema keys. Use the [English README](README.en.md) for complete user examples and the [English installation guide](references/install.en.md) for setup.

## 按任务读取

只读当前操作需要的文档，不要每次加载全部参考资料。

| 当前任务 | 读取 |
|---|---|
| 新安装、跨 agent/系统使用 | [安装技能](references/install.md)、[依赖与平台能力](references/dependencies.md) |
| 首次接入、找不到数据、换设备 | [定位与首次使用](references/first-run.md)、[依赖](references/dependencies.md) |
| 已授权云端初始化 | [云端初始化](references/bootstrap.md)、[云端配置模板](references/config-doc.md) |
| 用户明确选择本地独立存储/后台 | [可选本地扩展](references/local-runtime.md)、[本机后台安装](references/install.md#可选本机后台) |
| 新记、拆条、补充、纠错、完成 | [记录与更新](references/capture.md)、[数据约定](references/data-model.md) |
| 记录时刻、按天/周/月检索、旧日期兼容 | [记录时间与日期检索](references/timestamps.md) |
| 查找、线索时间线、整理、复盘、打卡 | [回读与整理](references/recall.md) |
| 提醒、循环、提前量、静音、改期 | [提醒管理](references/reminders.md) |
| 定时跑脚本、调接口、监控、技能组合 | [定时执行](references/execution.md) |
| 首次展示、用户问能做什么 | [使用示例](references/onboarding.md) |
| 升级、旧名称、备份、分表、迁移 | [升级与数据维护](references/upgrade.md) |
| 换平台 | [适配边界](references/portability.md) |
| 确认格式、修改本技能、验证包内容 | [标准格式](references/format.md)、[维护检查](references/consistency.md) |

## 最小工作流程

1. **识别意图。** 明确要求记录、提醒、整理或执行就处理；普通闲聊不因“以后可能有用”而偷偷保存。指定其他保存位置时尊重该位置。歧义会影响实际动作时只问必要的一句。
2. **检查本次所需能力。** 优先复用平台已连接的工具；记录依赖存储，提醒另需调度，执行另需后台工具与凭据。只检查当前操作在实际执行环境的依赖，不把安装 Python、SQLite 或本机任务设为全局前置。缺少调度时仍可记录，明确告知提醒尚未启用。
3. **定位现有对象。** WorkBuddy 云端继续回读原配置和表 ID，失效才按新旧名称查找和分页；其他已选存储按实际工具回读。仅已选本地扩展才运行 `scripts/jidou.py doctor`。网络或权限错误不等于不存在，遵循 `first-run.md`，不要换库或重建来“修复”。
4. **完成最小变更。** 一件独立的事一行；补充沿用线索；纠错更新被明确定位的记录。用户提供的原话与整理后的内容分别保存。
5. **验证结果再确认。** 回读新记录或受影响字段；接口超时但写入结果不明时先核对，避免盲重试。用一两句话说明记了什么、提醒何时生效或尚缺什么。

同一会话内可复用已验证的配置与表结构，不为每记一句话遍历全空间。切换账号、数据目录或执行环境时重新验证。本机多个 agent 可共享同一个用户数据目录，远程沙箱不自动拥有本机数据。

## 始终保持的约定

- **存储明确。** 沿用用户已有或明确选定的存储；WorkBuddy 原方案是 library 云端数据表，不是本地 Excel 文件。可选 SQLite 保存本地记录与运行状态，不自动缓存、迁移或同步云端数据。用户指定 Excel 等其他位置时按实际可用工具处理；不要把“只在聊天里记下”说成已持久保存。
- **原话可追溯。** 原文逐字保留；内容负责简述。拆条保留各条对应的原始片段，无法无损拆开的共用片段须说明。原文不进入普通摘要或提醒；用户索要原话或要求档案追溯时才展示。
- **敏感输入先处理。** 密码、密钥、证件号、银行卡号不进入任何字段，包括原文、日志和来源 URL。含这类内容的混合输入，先说明并取得去敏后的文本；不要一面拒存内容一面把秘密复制到原文。
- **字段兼容。** 保留现有 21 个字段、名称、顺序及枚举。机器定义只在 [schema.json](references/schema.json)，语义在 `data-model.md`。缺字段时先核对授权和适配器，不因读取动作自动改表。
- **记录状态独立。** 同一线索可以包含待办、决策和参考；完成一项不等于完成整条线索，不批量覆盖其他记录的状态。
- **记录时间精确。** 新记录用真实时钟和用户时区保存带偏移、精确到秒的记录时刻，普通编辑不重置。按用户日历日检索新时间戳与旧日期，旧数据不补造时分秒；见 `timestamps.md`。
- **提醒与执行分开。** 扫描只产生提醒；已明确配置的本地 argv 任务或云端任务才执行动作。登记实际任务 ID，用户停用的任务保持停用；原生命令托管字段用 job 控制，不靠改一段记录文字执行。
- **授权按实际请求延续。** 记录请求授权写入已经接好的收集箱；首次创建存储/提醒基础设施由用户选择。之后的同类正常操作无需反复询问。整理或读表不意味着授权建任务、搬目录、删数据或自动升级。
- **范围可验证。** 对象归属以配置 ID、创建回执和记录关联为依据；名称或文件名前缀相同不能单独证明归属。仅处理本次请求涉及的对象。

## 输出

跟随用户语言呈现摘要、分类、确认与说明；中英混合原话按原样保存。英文确认如 “Saved the idea and the task. The task doesn't have a reminder time yet.”，不直接输出内部中文字段/枚举或工具 JSON。
日常确认简短，如「记下两条：一个想法、一个待办。待办还没有提醒时间。」
提醒时间要用用户时区和具体日期；只有日期可建议 09:00 并明说，完全没时间就先记录再问。
首次使用展示已就绪的能力和记录/提醒/执行三类示例；用户索要完整清单时读 `onboarding.md`，不强制每次贴长表。
成功、部分成功、失败分别说清楚。不要输出凭据、内部 ID、原始响应或调用堆栈；用户排错时提供去敏后的必要信息。

## 文件与实例

仓库名是 `jidou-skill`，技能名与安装目录是 `jidou`。平台工具按实际接口调用；`render.py` 用于云端模板，`scripts/jidou.py` 是可选本地扩展入口。使用实际工具路径，不猜各 agent 的工具名称，不要求用户为云端脚本先配置自己的电脑。
运行时 ID 与数据只进入已选存储及任务配置，不回填到仓库模板。只有本地扩展将数据放用户数据目录；数据库、导出与快照不提交。

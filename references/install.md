# 安装指南

**简体中文** | [English](install.en.md)

**不限平台，不限 Agent。支持标准 Agent Skills 格式，就可以按同一套方法加载记兜。**

记兜使用 [Agent Skills 开放格式](https://agentskills.io/home)。下文先给通用安装方法，再覆盖操作系统、执行环境和不同 Agent 的入口；没有列出名字的产品也按通用方法处理。具体客户端能运行在哪些系统，以该产品自身的支持范围为准。

## 一、通用安装方法

### 让助手安装

把下面的话发给具备技能安装能力的助手：

> 帮我安装记兜：https://github.com/luguoli/jidou-skill.git
> 安装到当前实际执行任务的环境，保留完整技能包，安装后确认能发现 jidou。

助手没有安装工具时，使用下面的导入或复制方式；不需要因此先安装 Python。

### 通过界面导入

1. 下载 [仓库 ZIP](https://github.com/luguoli/jidou-skill/archive/refs/heads/main.zip) 并解压。
2. 在目标产品中找到技能、Skills、自定义能力或类似入口。
3. 选择其支持的文件夹、ZIP 或仓库导入方式；若要求 ZIP 根目录直接有 SKILL.md，就重新打包仓库内层内容。
4. 按产品要求启用技能、信任项目或刷新会话，确认能看到 jidou。

导入器若只提取 SKILL.md，还要补齐 references、scripts 等配套文件。不要把上传到普通聊天附件或知识库等同于安装了技能。

### 手动放入技能目录

将完整包放进该 Agent 实际扫描的目录，文件夹名使用 jidou：

```text
目标技能目录/
└── jidou/
    ├── SKILL.md
    ├── references/
    ├── scripts/
    ├── requirements.txt
    └── …其他随包文件
```

不要多套一层 `jidou/jidou-skill-main/SKILL.md`。先选项目级或用户级中的一个位置，避免同名副本造成覆盖关系不清。
已有目录先核对来源并保留备份，不把覆盖整目录当作默认安装步骤。

### 未提供原生 Skills 入口

让 Agent 读取实际路径下的 SKILL.md，并按任务读取其引用的资料；可在该宿主支持的项目指令或自定义指令中加入入口路径。
这属于手动加载，不等于获得原生自动发现、按需触发或后台执行能力。只有普通聊天、既不能读取配套文件也没有存储工具时，可帮助整理内容，不能声称已安装完整技能或已永久保存记录。

## 二、不同系统与执行环境

安装位置取决于 **Agent 实际运行在哪里**，不由你使用的屏幕或浏览器决定。以下情况使用相同的技能文件，区别在文件所在位置和加载入口。

| 系统或环境 | 安装方式与需要确认的事 |
|---|---|
| Windows：桌面、PowerShell、CMD、Git Bash | 导入或复制到 Windows 中该 Agent 的项目/用户技能目录；`~` 在路径表中表示该运行用户的主目录，常见为 `%USERPROFILE%` |
| macOS：Intel / Apple Silicon | 导入或复制到对应项目目录或当前用户目录；技能文件无需按处理器架构换包 |
| Linux：Ubuntu、Debian、Fedora、Arch、Alpine、Rocky 等 | 放入实际 Linux 用户或项目的技能目录；客户端、解释器和工具是否支持该发行版分别确认 |
| 国产桌面/服务器系统：统信 UOS、麒麟、openEuler 等 | 使用该系统上可用的 Agent，按其 Linux/平台说明安装，不猜专属目录 |
| WSL / WSL2 | Agent 在 WSL 中运行就装到其 Linux 环境；Windows 原生 Agent 则用 Windows 目录，两边不要默认视为同一安装 |
| IDE / 编辑器插件：VS Code、Visual Studio、JetBrains、Zed 等 | 使用插件所选 Agent 的技能入口；IDE 名称本身不决定技能路径，远程窗口还要检查远端环境 |
| 命令行 / TUI / 无界面进程 | 复制到当前运行用户或项目的技能目录；按该工具要求重载或新建会话 |
| SSH / 远程服务器 / VPS / 虚拟机 / NAS | 安装到远端执行任务的用户与文件系统；只在本机复制文件不会自动安装到远端 |
| Docker / Podman / Dev Container / Kubernetes | 将完整包放进镜像或挂载到容器内的技能目录，核对容器用户、路径与读取权限；需要持久记录时另配持久存储 |
| 云端 Agent / 云沙箱 / Codespaces / 托管工作区 | 通过云端技能管理、项目仓库或环境配置加载；核对当前云任务能读到文件，不假定已同步桌面用户目录 |
| CI/CD：GitHub Actions、GitLab CI、Jenkins 等 | 在实际执行 Agent 的工作区/镜像中提供完整包；按该宿主方式加载，跨运行持久化与调度另外配置 |
| 临时沙箱 / Serverless / 一次性任务 | 每次执行提供完整包或在可复用镜像中准备；不能把临时文件当作下一次仍存在的资料库 |
| 浏览器 / 网页版 AI 助手 | 有自定义技能功能就按其要求导入；只有附件/知识库入口时使用手动加载方式，不承诺本机文件与后台工具可用 |
| 手机 / 平板：iOS、iPadOS、Android、HarmonyOS | 通过支持技能的客户端或其关联云端/远程 Agent 安装；手机是控制入口时，技能放在真正执行任务的一端 |
| 企业内网 / 私有部署 / 团队共享环境 | 可离线导入完整包或使用团队项目分发；按组织允许的目录、网络与账号范围加载，不把个人数据/凭据打包共享 |

项目级安装随项目生效；用户级安装供该运行用户使用；云端和团队安装按对应工作区的分发机制生效。不同用户、容器、远端和云端通常需要分别提供文件。

## 三、不同 Agent 的入口与目录

下表是官方文档中可核对的入口示例，不是平台白名单。表中以 `jidou/` 结尾的路径已经是技能目录，里面直接放 SKILL.md 与完整配套文件，不再多套一层 jidou。目录与开关可能随版本变化，链接用于核对当前安装版本。

| Agent / 产品 | 项目或工作区入口 | 用户或其他入口 | 官方说明 |
|---|---|---|---|
| Codex：桌面、CLI、IDE 集成 | `.agents/skills/jidou/` | `~/.agents/skills/jidou/`；远程/云任务按其实际环境提供 | [Codex](https://learn.chatgpt.com/docs/build-skills) |
| Claude Code | `.claude/skills/jidou/` | `~/.claude/skills/jidou/` | [Claude Code](https://code.claude.com/docs/en/skills) |
| Cursor | `.cursor/skills/jidou/` 或 `.agents/skills/jidou/` | `~/.cursor/skills/jidou/` 或 `~/.agents/skills/jidou/`；云端同步另行核对 | [Cursor](https://cursor.com/docs/skills) |
| GitHub Copilot：CLI、云端、IDE Agent | `.github/skills/jidou/`，其他兼容位置按入口版本核对 | `~/.copilot/skills/jidou/`；个人目录不会自动进入每种云任务 | [Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills)、[VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills) |
| Gemini CLI | `.gemini/skills/jidou/` 或 `.agents/skills/jidou/` | `~/.gemini/skills/jidou/` 或 `~/.agents/skills/jidou/` | [Gemini CLI](https://geminicli.com/docs/cli/skills/) |
| OpenCode | `.opencode/skills/jidou/` | `~/.config/opencode/skills/jidou/`；也支持官方列出的 Claude/agents 兼容位置 | [OpenCode](https://opencode.ai/docs/skills/) |
| Qwen Code | `.qwen/skills/jidou/` 或 `.agents/skills/jidou/` | `~/.qwen/skills/jidou/` 或 `~/.agents/skills/jidou/` | [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) |
| Cline | `.cline/skills/jidou/` | `~/.cline/skills/jidou/`；也可从 Skills 菜单管理 | [Cline](https://docs.cline.bot/customization/skills) |
| Roo Code | `.roo/skills/jidou/` 或 `.agents/skills/jidou/` | `~/.roo/skills/jidou/` 或 `~/.agents/skills/jidou/` | [Roo Code](https://roocodeinc.github.io/Roo-Code/features/skills/) |
| Kiro | `.kiro/skills/jidou/` | `~/.kiro/skills/jidou/`；自定义 Agent 的 resources 另按文档配置 | [Kiro](https://kiro.dev/docs/skills/) |
| Amp | `.agents/skills/jidou/` | `~/.config/agents/skills/jidou/` 或文档中的兼容目录 | [Amp](https://ampcode.app/docs/customize/skills) |
| goose | `.agents/skills/jidou/` | `~/.agents/skills/jidou/`，其他兼容位置见官方说明 | [goose](https://github.com/aaif-goose/goose/blob/main/documentation/docs/guides/context-engineering/using-skills.md) |
| Google Antigravity：App、CLI、IDE | `.agents/skills/jidou/` | `~/.gemini/config/skills/jidou/`；旧版和特定入口的兼容目录按文档核对 | [Antigravity](https://antigravity.google/docs/skills) |
| OpenClaw | 当前实际工作区的 `skills/jidou/` | `~/.openclaw/skills/jidou/`；也可使用其技能安装命令 | [OpenClaw](https://docs.openclaw.ai/tools/skills) |
| CodeBuddy Code | `.codebuddy/skills/jidou/` | `~/.codebuddy/skills/jidou/` | [CodeBuddy](https://www.codebuddy.cn/docs/cli/skills) |
| WorkBuddy：桌面、云端、移动入口 | 技能管理中的上传/导入；云任务检查云端技能可见性 | 按所用版本的技能管理与工作区设置安装 | [WorkBuddy](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market) |
| TRAE 中国版 | `.trae/skills/jidou/` | `~/.trae-cn/skills/jidou/`，也可通过技能界面导入 | [TRAE](https://docs.trae.cn/ide_skills?lang=zh) |
| TRAE 国际版、其他版本或入口 | 使用该版本的技能导入或其官方目录 | 不直接套用中国版全局目录 | 所用版本的官方安装说明 |
| 其他 Agent、编辑器扩展、自建 Agent | 原生 Skills 导入、配置的技能扫描目录，或本页的手动加载方式 | 由该宿主配置决定 | 该 Agent 的官方文档或当前配置 |

没有出现在表里的产品，按下面顺序处理：查技能导入入口 → 查该版本官方扫描目录 → 导入完整包 → 确认发现 jidou；没有原生支持时改用手动加载。不能只根据产品名字猜一个隐藏文件夹。

### 目录复制示例

先按上表和实际环境确认目标根目录，再复制。下面以支持 `.agents/skills` 的项目为例，其他 Agent 替换目标根目录即可。

Windows PowerShell，在已下载的仓库目录内执行：

```powershell
$jidouTarget = Join-Path 'D:\your-project' '.agents\skills\jidou'
if (Test-Path -LiteralPath $jidouTarget) { throw '目标已存在，请先核对和备份' }
git clone https://github.com/luguoli/jidou-skill.git $jidouTarget
```

macOS / Linux / WSL / 远端 POSIX shell：

```bash
jidou_target="/absolute/path/to/project/.agents/skills/jidou"
if [ -e "$jidou_target" ]; then
  printf '%s\n' '目标已存在，请先核对和备份' >&2
else
  git clone https://github.com/luguoli/jidou-skill.git "$jidou_target"
fi
```

没有 Git 时手动复制解压后的完整包也可以。`~/.agents/skills` 只是部分 Agent 支持的共享约定，不是每个 Agent 都会扫描的通用目录；云端也不自动读取本机的这个目录。

## 四、安装后怎么确认

1. 在实际任务环境中确认 Agent 已发现 jidou；按产品需要刷新技能列表、新建会话或重启客户端。
2. 发一句「记一下：这周想整理书桌」，确认助手按记兜规则处理。
3. 使用已有记录时核对原存储；没有接好存储就说明尚未保存，不创建替代库冒充成功。
4. 分别确认记录、提醒和执行是否就绪；安装成功不等于所有平台都提供相同后台工具。

WorkBuddy 原云端方案继续接回 library 数据表和 automation-task-manager。其他 Agent 复用其已有存储、连接器与调度；只有用户明确选择独立本地方案才初始化 SQLite。依赖检查发生在实际执行端，不要求所有用户先在自己的电脑上安装 Python。
这里只核对官方安装入口，不表示本仓库已经在表中所有产品和系统上逐一实机验收；已执行的测试范围见 [适配边界](portability.md)。

## 五、更新与多环境使用

更新实际使用的那份完整包，先保存旧包和用户修改；用 Git 安装且没有本地改动时可在其目录内执行 `git pull --ff-only`。发现本地修改或不同来源时先核对，不强制覆盖。
多 Agent 共用技能文件须符合各自目录与优先级规则；共用技能不等于共用数据。切换主机、用户、WSL、容器或云端时核对实际存储，不能靠重复安装自动同步记录。
团队分发只包含技能源码，不带个人数据库、导出、凭据或运行配置。

### 可选的随包复制工具

手动安装和平台导入适用于所有支持该格式的宿主。随包 Python 复制工具目前只提供 codex、claude、trae 三个目标选项，是额外的便捷工具，不是支持平台名单；其他目标按本页通用方式安装。

```bash
python scripts/jidou.py install --agent codex --scope user
python scripts/jidou.py install --agent codex --scope user --apply
python scripts/jidou.py install --agent claude --scope project --project /absolute/path/project --apply
python scripts/jidou.py install --agent trae --scope project --project /absolute/path/project --apply
```

只有执行此复制脚本时需要该执行端的 Python 3.10+。默认只给计划，--apply 才写目录；不覆盖未托管目录，托管更新保留旧包，遇额外用户文件先拒绝。它不初始化数据库，不注册系统后台，也不迁移云端数据。

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

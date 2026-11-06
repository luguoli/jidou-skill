# Installation guide

[简体中文](install.md) | **English**

**Not tied to a platform or agent. An assistant that supports the standard Agent Skills format can load Jidou.**

Jidou uses the [Agent Skills open format](https://agentskills.io/home). Start with the universal methods below, then check your execution environment and agent’s discovery paths. The same methods apply to products not named here. Your agent’s own system requirements still apply.

## Universal installation

### Ask your assistant

Send this to an assistant with skill-installation tools:

> Install Jidou: https://github.com/luguoli/jidou-skill.git
> Install the complete package in the environment that will actually run my tasks, then confirm that you can discover jidou.

If it cannot install skills itself, use an import interface or copy the package manually. You do not need Python just to import or copy a skill.

### Import through an interface

1. Download and extract the [repository ZIP](https://github.com/luguoli/jidou-skill/archive/refs/heads/main.zip).
2. Find the product’s Skills or custom-capabilities interface.
3. Use its supported folder, ZIP, or repository import. If it requires SKILL.md at the ZIP root, package the contents of the extracted inner folder accordingly.
4. Enable the skill, trust the project if required, and refresh the skill list or start a new session. Check that jidou is visible.

If an importer extracts only SKILL.md, supply the accompanying references and scripts as well. Uploading a document to ordinary chat or a knowledge base is not necessarily skill installation.

### Copy the complete directory

Place the package in a directory that your agent actually scans, with jidou as the skill directory name:

```text
your-skills-directory/
└── jidou/
    ├── SKILL.md
    ├── README.en.md
    ├── references/
    ├── scripts/
    ├── requirements.txt
    └── …other package files
```

Avoid nesting it as `jidou/jidou-skill-main/SKILL.md`. Choose project or user scope initially so duplicate copies do not make precedence unclear. Preserve an existing directory and check its source before replacing it.

### If the product has no native Skills interface

Ask the agent to read SKILL.md from the real package location and load its referenced resources as needed. A supported project/custom-instructions mechanism can point to that entry file.
This is manual loading, not native automatic discovery or background execution. A chat-only tool that cannot access the package and a persistent store can help organize text, but must not claim that Jidou is fully installed or your notes are permanently saved.

## Systems and execution environments

Install where **the agent actually runs**, which may be different from the device showing the conversation.

| Environment | Installation and checks |
|---|---|
| Windows: desktop, PowerShell, CMD, Git Bash | Import or copy to the agent’s project/user directory in Windows. In the path table, `~` means the execution user’s home, commonly `%USERPROFILE%`. |
| macOS: Intel or Apple Silicon | Use the relevant project or user directory. The skill files do not need a separate architecture-specific package. |
| Linux: Ubuntu, Debian, Fedora, Arch, Alpine, Rocky, and others | Use the actual Linux user/project directory. Check the agent and any execution tools against the distribution’s requirements. |
| UOS, Kylin, openEuler, and other regional distributions | Use an agent available on that system and its documented paths. Do not invent a distribution-specific skill directory. |
| WSL / WSL2 | Install in the WSL Linux environment when the agent runs there; a native Windows agent uses its Windows paths. Treat them as separate installations. |
| IDE/editor extensions: VS Code, Visual Studio, JetBrains, Zed, and others | Follow the selected agent extension’s Skills interface. The editor name alone does not determine the path; check remote windows too. |
| CLI, TUI, or a headless process | Copy to the running user/project’s discovery path, then reload or start a new session as required. |
| SSH, remote servers, VPS, VMs, NAS | Install for the remote execution user and filesystem. A local copy is not automatically available remotely. |
| Docker, Podman, Dev Containers, Kubernetes | Include the complete package in the image or mount it into the container’s discovery directory. Check the container user and read permissions; persistent notes need persistent storage separately. |
| Cloud agents, cloud sandboxes, Codespaces, hosted workspaces | Load through cloud skill management, the project repository, or environment setup. Do not assume desktop user directories are synchronized. |
| CI/CD: GitHub Actions, GitLab CI, Jenkins, and others | Provide the package in the agent’s actual workspace/image and load it through that host’s mechanism. Persistence and scheduling are separate capabilities. |
| Temporary sandboxes, serverless, one-shot jobs | Supply the package for each execution or prepare a reusable image. Temporary files are not a durable notes store. |
| Browser/web assistants | Use a custom-skills interface when available. Otherwise use manual loading, without assuming local-file or background-tool access. |
| Phones/tablets: iOS, iPadOS, Android, HarmonyOS | Use a skills-capable client or its cloud/remote execution environment. Install at the execution end if the mobile device is only a controller. |
| Enterprise, on-premises, shared team environments | Import offline or distribute through an approved team project. Follow organization paths and account boundaries; do not distribute personal data or credentials with the skill. |

Project installations apply to that project. User installations apply to that execution user. Cloud and team installations follow the workspace’s distribution rules. Separate users, containers, remote hosts, and cloud environments generally need their own accessible copy.

## Agent entry points and directories

These are documented examples, not a platform allowlist. Each path ending in `jidou/` is already the skill directory: put SKILL.md directly inside it, without another jidou level. Check the linked documentation for the version you use.

| Agent/product | Project/workspace | User or other scope | Official documentation |
|---|---|---|---|
| Codex: desktop, CLI, IDE integrations | `.agents/skills/jidou/` | `~/.agents/skills/jidou/`; provide files in the actual remote/cloud runtime | [Codex](https://learn.chatgpt.com/docs/build-skills) |
| Claude Code | `.claude/skills/jidou/` | `~/.claude/skills/jidou/` | [Claude Code](https://code.claude.com/docs/en/skills) |
| Cursor | `.cursor/skills/jidou/` or `.agents/skills/jidou/` | `~/.cursor/skills/jidou/` or `~/.agents/skills/jidou/`; check cloud synchronization separately | [Cursor](https://cursor.com/docs/skills) |
| GitHub Copilot: CLI, cloud, IDE agents | `.github/skills/jidou/`; check other supported locations for your surface | `~/.copilot/skills/jidou/`; personal paths are not automatically present in every cloud session | [Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills), [VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills) |
| Gemini CLI | `.gemini/skills/jidou/` or `.agents/skills/jidou/` | `~/.gemini/skills/jidou/` or `~/.agents/skills/jidou/` | [Gemini CLI](https://geminicli.com/docs/cli/skills/) |
| OpenCode | `.opencode/skills/jidou/` | `~/.config/opencode/skills/jidou/`; documented Claude/agents-compatible paths also apply | [OpenCode](https://opencode.ai/docs/skills/) |
| Qwen Code | `.qwen/skills/jidou/` or `.agents/skills/jidou/` | `~/.qwen/skills/jidou/` or `~/.agents/skills/jidou/` | [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) |
| Cline | `.cline/skills/jidou/` | `~/.cline/skills/jidou/`, or manage through the Skills menu | [Cline](https://docs.cline.bot/customization/skills) |
| Roo Code | `.roo/skills/jidou/` or `.agents/skills/jidou/` | `~/.roo/skills/jidou/` or `~/.agents/skills/jidou/` | [Roo Code](https://roocodeinc.github.io/Roo-Code/features/skills/) |
| Kiro | `.kiro/skills/jidou/` | `~/.kiro/skills/jidou/`; configure custom-agent resources as documented | [Kiro](https://kiro.dev/docs/skills/) |
| Amp | `.agents/skills/jidou/` | `~/.config/agents/skills/jidou/` or documented compatible paths | [Amp](https://ampcode.app/docs/customize/skills) |
| goose | `.agents/skills/jidou/` | `~/.agents/skills/jidou/` or documented compatible paths | [goose](https://github.com/aaif-goose/goose/blob/main/documentation/docs/guides/context-engineering/using-skills.md) |
| Google Antigravity: App, CLI, IDE | `.agents/skills/jidou/` | `~/.gemini/config/skills/jidou/`; check older/surface-specific locations in the documentation | [Antigravity](https://antigravity.google/docs/skills) |
| OpenClaw | `skills/jidou/` within the actual active workspace | `~/.openclaw/skills/jidou/`, or use its skill installer | [OpenClaw](https://docs.openclaw.ai/tools/skills) |
| CodeBuddy Code | `.codebuddy/skills/jidou/` | `~/.codebuddy/skills/jidou/` | [CodeBuddy](https://www.codebuddy.cn/docs/cli/skills) |
| WorkBuddy: desktop, cloud, mobile entry points | Skill upload/import; check visibility in the actual cloud task | Follow the version’s skill management/workspace settings | [WorkBuddy](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market) |
| TRAE China edition | `.trae/skills/jidou/` | `~/.trae-cn/skills/jidou/`, or import through its skill interface | [TRAE](https://docs.trae.cn/ide_skills?lang=zh) |
| TRAE international/other editions | Use that edition’s import interface or documented directory | Do not assume the China-edition global path | That edition’s official documentation |
| Other agents, editor extensions, custom agents | Native Skills import, a configured discovery directory, or manual loading | Defined by the host configuration | The agent’s documentation or current configuration |

For an unlisted product: find its skill-import interface → check its documented discovery directory → supply the complete package → confirm jidou is visible. Use manual loading if it has no native support. Do not guess a hidden directory from the product name.

### Example: clone into a confirmed project skill directory

The following targets `.agents/skills`, which only some agents support. Replace it with your verified destination. Preserve any existing installation first.

Windows PowerShell:

```powershell
$jidouTarget = Join-Path 'D:\your-project' '.agents\skills\jidou'
if (Test-Path -LiteralPath $jidouTarget) { throw 'Destination exists; inspect and back it up first' }
git clone https://github.com/luguoli/jidou-skill.git $jidouTarget
```

macOS / Linux / WSL / a remote POSIX shell:

```bash
jidou_target="/absolute/path/to/project/.agents/skills/jidou"
if [ -e "$jidou_target" ]; then
  printf '%s\n' 'Destination exists; inspect and back it up first' >&2
else
  git clone https://github.com/luguoli/jidou-skill.git "$jidou_target"
fi
```

Without Git, copy the extracted package manually. A shared `.agents/skills` convention is not a universal path, and cloud agents do not automatically read your local user directory.

## After installation

New notes retain the actual capture timestamp with an offset and second precision. Date-based searches use your configured local calendar day and include legacy date-only records without inventing a time. See [capture-time behavior](timestamps.md#english-capture-timestamps-and-calendar-date-search).

1. Confirm discovery in the actual execution environment; reload the skill list, start a new session, or restart the client as required.
2. Try “Make a note: I want to organize my desk this week.” Speak English; the assistant should reply in English and preserve your original words.
3. Reuse the existing store. If storage is not connected, the assistant must say the note has not been saved, rather than creating a different store silently.
4. Check capture, reminders, and execution separately. Loading a skill does not give every host the same tools.

WorkBuddy’s existing cloud setup keeps its library table and automation-task-manager. Other agents use their actual connected tools. Choose the local extension only when you explicitly want it. For time-based requests, preserve your configured timezone; if none is known, establish it before scheduling. English does not imply a US location or month/day date format.
These paths come from documentation; they are not a claim that every listed product/system was tested with this package. The existing verification scope is described in [platform boundaries, in Chinese](portability.md).

## Updates and multiple environments

Update the copy actually in use. Back up the old package and user edits first. For a Git installation with no local changes, run `git pull --ff-only` in its directory; inspect local changes or a different source before replacing anything.
Sharing skill files is different from sharing notes. Check the selected store when changing user, host, WSL distribution, container, or cloud runtime. Team distribution should contain source files only, without personal databases, exports, credentials, or instance configuration.

### Optional bundled copy tool

Manual installation and host import work with any compatible host. The bundled Python copy tool currently exposes only codex, claude, and trae destinations; these are convenience options, not the skill’s compatibility list.

```bash
python scripts/jidou.py install --agent codex --scope user
python scripts/jidou.py install --agent codex --scope user --apply
python scripts/jidou.py install --agent claude --scope project --project /absolute/path/project --apply
python scripts/jidou.py install --agent trae --scope project --project /absolute/path/project --apply
```

Only running this tool requires Python 3.10+ at that execution location. It previews by default; --apply writes the package. Unmanaged directories are not overwritten. Managed updates preserve the old package and refuse unexpected user files. It does not initialize data, register an OS task, or migrate cloud records.

## Optional local background worker

Use this section only after explicitly choosing the local Python/SQLite extension and requesting local reminders/actions. Existing platform/cloud scheduling remains the first choice. Skill installation itself does not require this setup.

With Python 3.10+ in the actual runtime, use the installed package’s script path:

```bash
python scripts/jidou.py doctor
python scripts/jidou.py init --timezone Europe/London
python scripts/jidou.py reminders pending
```

doctor is read-only. Run init only when you have chosen local storage and authorized its creation; replace Europe/London with your actual timezone. For dependency details and advanced commands, the [local runtime reference](local-runtime.md) is currently in Chinese, and CLI --help is in English. Conversational users should let their assistant translate tool parameters using the [language guide](language.md), not learn internal field names.

The system channel uses the logged-in desktop’s notifier. OS acceptance does not prove a person saw the notification. A webhook uses an environment-variable reference; the scheduled process must have that variable, which may differ from your current shell.

Preview a native plan before explicitly applying it:

```bash
python scripts/jidou.py scheduler plan --channel system
python scripts/jidou.py scheduler install --channel system --apply
python scripts/jidou.py scheduler status
```

| System | Native integration | Conditions |
|---|---|---|
| Windows | A per-user interactive scheduled task, every minute, without elevation or a saved password | Logged-in user; valid Python, script, and data paths |
| macOS | A user LaunchAgent plist, StartInterval=60, argument-array execution | User graphical session, valid interpreter, notifications available |
| Linux | An explicit worker command for your selected existing scheduler | This version does not automatically change cron/systemd |

See [Microsoft Schtasks](https://learn.microsoft.com/en-us/windows/win32/taskschd/schtasks) and [Apple LaunchAgents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html).
The worker scans/delivers reminders, then processes explicitly configured command jobs. You do not have to leave the chat open, but sleep, logout, long jobs, and queueing can delay execution. Registration is not 24-hour cloud hosting or guaranteed delivery.
The installer does not replace same-named tasks/plists or automatically update a saved registration. Inspect its actual unique name in the OS before changing/stopping it. job disable stops future execution; it does not prove an already running external action has stopped.
The existing Windows core was tested in isolation; macOS/Linux logic and configuration checks are not real-desktop registration or delivery tests. This release does not install personal background tasks or send real test notifications automatically.

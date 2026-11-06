# 依赖与实例定位

## 能力检查

先接回已有存储，优先复用所在平台已连接的资料库、表格、连接器和调度工具。技能说明本身不依赖 Python；安装技能不自动授权新建数据库或系统任务。
WorkBuddy 云端沿用原 library 云端表与 automation-task-manager；其他 Agent 使用其实际可用接口，核对21字段和时间语义，不能假设拥有 WorkBuddy 服务。工具不可用时说明受影响能力，不要求所有平台统一安装 Python，也不自动降级到本地新库。
**可选本地扩展**才使用随包 `scripts/jidou.py`、Python 3.10+ 与 SQLite。用户明确选定后按 [local-runtime.md](local-runtime.md) 操作，本机后台见 [install.md](install.md)。

| 能力 | 用途 | 不可用时 |
|---|---|---|
| 存储：建表、分页查记录、批量增改、条件查询 | 持久记录与回读 | 说明尚未保存；可在聊天里整理候选，但不冒充持久记录 |
| 调度：创建/查询/更新/停用任务，支持时区 | 提醒与独立任务 | 记录功能照常；明确提醒/执行尚未启用 |
| 后台执行：工具、网络、必要凭据 | 调用 API、脚本、技能 | 保留需求，不能承诺到点执行；提醒本身也需要能读表的执行环境 |

云端适配器是 `library` 与 `automation-task-manager`，并不随本仓库打包。安装本技能不等于这些依赖已存在。
先检查实际路径与各脚本 `--help`，再采用命令示例；服务响应结构与限制须现场核验。没有可用适配器时不要编造调用或将真实数据写入另一个未经选择的后端。

## Python 依赖检查发生在哪里

| 操作 | 实际要求 |
|---|---|
| 读 SKILL.md、平台导入、手动复制包 | 不以 Python 为前置 |
| 调用平台已有工具 | 按该工具的实际运行要求；工具自带脚本时检查其执行环境 |
| 随包 render.py / validate.py | 执行位置需要 Python 3.10+、PyYAML 与可用 IANA 时区数据 |
| 可选本地 CLI / 复制安装器 / 本机后台 | 执行该脚本的本机需要 Python 3.10+；本地核心使用标准库，农历计算另需 lunardate，Windows 时区数据使用 tzdata |

requirements.txt 是随包脚本/开发的便利依赖清单，不是所有用户首次使用前必须安装的步骤。云端脚本检查云端解释器与依赖，不要求用户先在电脑上安装；也不假定平台一定预装 Python/PyYAML。仅执行一次操作时检查所需依赖，缺失则报告，不因读取记录自动安装或改环境。

## 当前云端适配器路径

```bash
SKILLS="${JIDOU_SKILL_ROOT:-${CODEBUDDY_SKILL_DIR:-$HOME/.codebuddy/skills}}"
JIDOU="$SKILLS/jidou"
LIB="$SKILLS/library"
ATM="$SKILLS/automation-task-manager"
```

非 POSIX 环境用该平台原生路径、调用和临时目录。`SKILLS` 是可配置位置，不能通过改一个路径假定所有平台的接口语义都相同。

| 接口示例 | 约定用途 |
|---|---|
| `space_api.py space.workspace.list-user-spaces` | 列空间，按账号与空间类型选择 |
| `space_api.py space.workspace.list-nodes` | 列节点，遍历分页和必要的子目录 |
| `space_api.py space.workspace.node-info --node-id …` | 验证 ID、kind、父目录及实际 URL |
| `database/get_database_schema.py` | 核对字段、选项及字段 ID |
| `database/create_database_with_records.py --stdin` | 用渲染后的 schema 建空表 |
| `database/query_database_record.py` | 条件查询，遵循其分页与过滤器格式 |
| `database/batch_add_database_records.py --stdin` | 新增，核对每条结果 |
| `database/batch_update_database_records.py` | 更新，保留未修改字段 |
| `doc/create_doc.py` | 有保存需求时创建配置或整理文档 |
| `scripts/scheduler-api.sh list/get/create/update/delete` | 任务操作；不假定拥有运行历史、原子事务或精确投递能力 |

## 云端配置

[config-doc.md](config-doc.md) 记录实例 ID；本地缓存只在本次会话加速，不能用于判断首次使用。

| 需要的值 | 获取方式 |
|---|---|
| space_id | 列用户空间，验证所属账号；多个候选时请用户选择 |
| database_id | 云端配置，或首次定位后验证 kind=database；library 的响应常在 `data.node.kind`，需按实际返回读 |
| folder_id 与子目录 ID | 配置及 `node-info` 回读；缺失时定位已授权范围，不创建同名副本 |
| task_id_reminder | 配置 ID 优先，再按新旧任务名查重；停用不是不存在 |
| 访问 URL | 建表/文档返回或 `node-info`，不拼内部 URL |
| 多表范围 | 配置中的 active_database_ids；旧配置没有时只含 database_id，维护时明确补充仍有未完成项的旧表 |

## 目录与对象范围

默认仅需 `记兜/` 及其中的表和配置。`备份/`、`自动化任务归档/` 在实际使用这些产物且获授权时再创建。
不为记录功能预建 `skills/` 或凭据目录，不保存凭据到本技能的明文字段。
新建内容尽可能带已验证的父目录；发现旧内容在别处，先沿用现有位置，不自动搬回“规范目录”。
归属须由配置关联、创建回执和用户指定共同确认；同名不意味着可以接管、迁移或删除。

## 失败与重试

只读网络故障可有限重试一次；认证/权限错误先修复依赖。变更请求结果不明时先查询实际状态，不盲目重复创建或追加。
降级时分别报告记录、提醒与执行状态。后台环境与当前会话不共享文件、连接或凭据，必须单独验证。

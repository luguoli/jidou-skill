# 初始化与补缺

先完成 [first-run.md](first-run.md) 的定位。只有用户明确要求首次创建、提醒开通或本次修复时才执行相应步骤；不是每次记录都从头跑。

## 1. 检查适配器

按 [dependencies.md](dependencies.md) 定位 SKILLS、JIDOU、LIB、ATM，查看实际 CLI 帮助。当前示例使用 POSIX shell；Windows 用原生工具和正确引用，不照搬 shell 语法。
先验证存储读写能力；调度不存在时允许只启用记录。不要自动下载依赖、扩大权限或创建替代后端。

创建本次独立临时目录，并将实际上下文用 JSON 序列化保存为 context.json。示例只是键的说明，尖括号必须换成实际值；渲染器会拒绝未替换值。

```json
{
  "SPACE_ID": "<实际空间ID>",
  "DATABASE_ID": "<实际表ID>",
  "FOLDER_ID": "<实际记兜目录ID>",
  "SKILLS_DIR": "<后台环境实际技能根目录>",
  "TODAY": "<用户时区当天YYYY-MM-DD>",
  "INIT_MODE": "首次使用，用户要求新建",
  "TIMEZONE": "Asia/Shanghai",
  "TASK_ID": "",
  "REMINDER_STATUS": "disabled",
  "REMINDER_START_AT": ""
}
```

各命令只校验本模板需要的值。建表前不需要 DATABASE_ID；只记录不需要 SKILLS_DIR、任务 ID 或提醒启用时间。

## 2. 准备目录和空表

核对已有记兜目录及归属；已有就复用。没有且已获本次创建授权才创建。列目录完成分页后再判断不存在。
只有需要备份或执行产物时才准备相应子目录，不预建无关目录。

结构只来自 [schema.json](schema.json)，不复制第二份 properties 清单。把 SPACE_ID、FOLDER_ID 写进上下文后渲染：

```bash
python3 "$JIDOU/scripts/render.py" schema --context "$JIDOU_TMP/context.json" > "$JIDOU_TMP/schema.json"
# 上一条退出码非零就停，不能将空文件继续提交。
python3 "$LIB/database/create_database_with_records.py" --stdin < "$JIDOU_TMP/schema.json"
```

各步骤分开检查退出码和服务结果。建空表时不同时写首条记录；失败响应若已返回表 ID，先回读，不重建。
验证父目录、完整字段顺序、类型与枚举，保留服务分配的字段/选项 ID。补字段只在已授权修复范围内追加，不能重排或删改已有字段。
把实际 database_id 填入上下文；后续按 [capture.md](capture.md) 写首条记录。

## 3. 提醒按需开通

用户只要记录时跳过本节。需要提醒时按配置任务 ID、新旧任务名查重；同名须核对目标表和归属，不接管别人的任务。
已有停用任务保持停用，用户明确恢复时才启用；任务存在且就绪不重复创建。

默认参数唯一来源是 [defaults.json](defaults.json)。创建前读取它，用户有不同偏好时在云端配置与任务中一起记录，不悄悄覆盖现役设置。
将后台可用的 SKILLS_DIR、带时区的 REMINDER_START_AT、实际 TIMEZONE 和全部 DATABASE_IDS 写入上下文，渲染独立 prompt：

```bash
python3 "$JIDOU/scripts/render.py" reminder --context "$JIDOU_TMP/context.json" > "$JIDOU_TMP/reminder.txt"
```

渲染成功后再用已确认的 scheduler 接口创建。六段 cron 的默认值是每小时整点；共享提醒默认不自动重试，原因见 [reminders.md](reminders.md)。创建时显式传时区、超时、重试设置及完整 prompt，不依赖服务端默认值。
当前适配器常见参数为 `--name --cron --prompt --frequency-type --timezone --timeout --retry-count`；根据真实 `--help` 使用，不假设所有调度器都支持。
返回不明先查列表与目标指纹，避免重复创建；验证 task ID、状态、下一次运行时间、参数和存入的完整 prompt。
没有验证通知投递链路时说“任务已配置，投递尚待验证”，不要承诺通知一定送达。

## 4. 写入配置

表可用就能记录配置；提醒尚未开通时任务 ID 留空、状态设 disabled/unavailable，不能伪装整套已启用。
表建好后再写配置，避免配置指向不存在的表。任务已经创建则填实际 TASK_ID、REMINDER_STATUS；中断后沿用已存在对象继续补，不整套重跑。

```bash
python3 "$JIDOU/scripts/render.py" config --context "$JIDOU_TMP/context.json" > "$JIDOU_TMP/config.md"
# 渲染成功后，使用实际文档接口在已验证 folder_id 下创建或更新配置。
```

核对配置内所有 ID、字段数、能力状态和带时区日期。没有配置更新接口时按实际平台流程处理，不猜不存在的命令参数。
首次简述已就绪能力，给记录/提醒/执行三类示例，未就绪项说明条件；用户问完整清单时读 [onboarding.md](onboarding.md)。

## 5. 收尾

只移除本次创建的临时文件，先核对完整路径和范围；不按通配符清理旧目录、不碰用户文件。
不把上下文、实例 ID、备份数据、渲染后的 prompt 或配置文档提交到仓库。

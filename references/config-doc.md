# 速记箱 · 配置

**这份文档是「已经装好」的凭证。** 它存在，就说明表、字段、提醒任务都建过了。换设备、换执行环境、换 agent，读到它就直接用，不要重建、不要问、不要往本地写任何东西。

## 当前配置

| 键 | 值 |
|---|---|
| schema_version | __SCHEMA_VERSION__ |
| space_id | __SPACE_ID__ |
| database_id | __DATABASE_ID__ |
| database_title | 速记箱 |
| folder_id | __FOLDER_ID__ |
| folder_backup_id | __FOLDER_BACKUP_ID__ |
| folder_archive_id | __FOLDER_ARCHIVE_ID__ |
| task_id_reminder | __TASK_ID__ |
| task_name_reminder | 速记提醒 |
| initialized_at | __TODAY__ |
| init_mode | __INIT_MODE__ |
| field_count | __FIELD_COUNT__ |

**三个目录 id 是给执行类任务用的**：任务指令里必须写死它们（执行环境读不到本地约定）。表一重建、目录一重排，这三个值就变，所以记在这里——**重建后照这份文档改任务指令，不用满空间找**。

## 这份文档怎么用

1. **先查这张表在不在**（拿 `database_id` 调 `node-info`，kind 是 `database`）→ 在，就直接记东西，不再问用户任何初始化问题。
2. **表不在了**（被删、换账号），这份文档就是线索：拿 `database_title` 在全空间再搜一遍，可能只是被挪了目录或改了名。
3. **搜不到**才谈重建。重建前必须问用户一句，不要自己决定。

## 维护规则

- **和速记箱表放在同一个目录里**（`速记箱/`），不要单独挪走，也不要放到根目录。
- **不要删这份文档。** 删了不会立刻出事，但下次换环境时系统会以为从没装过，可能重复建表。
- 改了表结构（加字段、改选项）→ 更新 `schema_version` 和 `field_count`。
- 重建了表 → 更新 `database_id` 和 `initialized_at`，`init_mode` 写清是"重建"还是"迁移"。
- 重建了提醒任务 → 更新 `task_id_reminder`。

## 为什么凭证放在云端

放在本地没有意义：定时任务跑在独立的执行环境，换设备本地是空的，本地文件一律读不到。**只有云端是跨环境可信的。**

这也是为什么判断"是不是第一次"不能靠探测本地目录，只能靠这张文档 + 表本身是否存在。

两者都没有，才真的需要问用户。问法见 `references/first-run.md`。

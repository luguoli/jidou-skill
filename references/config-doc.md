# 记兜·配置

此文档只存实例定位与能力状态，不存凭据或用户原文。读取配置不等于所有依赖均已就绪；按需回读实际对象。

| 键 | 值 |
|---|---|
| schema_version | __SCHEMA_VERSION__ |
| space_id | __SPACE_ID__ |
| database_id | __DATABASE_ID__ |
| database_title | 记兜 |
| folder_id | __FOLDER_ID__ |
| folder_backup_id | __FOLDER_BACKUP_ID__ |
| folder_archive_id | __FOLDER_ARCHIVE_ID__ |
| task_id_reminder | __TASK_ID__ |
| task_name_reminder | 记兜提醒 |
| initialized_at | __TODAY__ |
| init_mode | __INIT_MODE__ |
| field_count | __FIELD_COUNT__ |
| timezone | __TIMEZONE__ |
| active_database_ids | __DATABASE_IDS_JSON__ |
| reminder_start_at | __REMINDER_START_AT__ |
| reminder_status | __REMINDER_STATUS__ |
| quiet_start_hour | __QUIET_START_HOUR__ |
| quiet_end_hour | __QUIET_END_HOUR__ |
| catchup_hours | __CATCHUP_HOURS__ |

可选目录或任务尚未创建时保留空值，不填假 ID。reminder_status 为 unavailable / disabled / enabled，必须与实际任务状态一致；记录存储可独立就绪。
active_database_ids 是当前仍需扫描的表 ID 列表，不包含仅作冷备的文件；旧配置无此键时先沿用 database_id，维护时检查跨年未完成项。
reminder_start_at 是该提醒方案开始接管的时刻，必须为带时区的 ISO 时间；未启用提醒时留空。同步 prompt 时沿用配置，不随每次渲染悄悄重置。
init_mode 如实填写首次新建、接回存量、迁移或用户要求重置的事实，不伪造授权。

更新后核对配置、表及任务 ID。任务停用时更新状态；目录或表 ID 变化时同步所有关联任务，再回读。不得只改配置就声称迁移完成。

# 记录时间与日期检索

## 新记录的写入

「记录时间」保存真实记录时刻，统一使用 **带 UTC 偏移、精确到秒的 ISO 8601**，例如 `2026-11-07T10:25:36+08:00`。时区来自已确认的用户配置，当前时间来自实际时钟，不复用文档示例、旧对话时间或宿主默认时区。

- 新记录未提供记录时间时自动填实际时刻；显式提供的时间必须带偏移，并规范为秒精度。无偏移时间不能猜时区后写入。
- 记录时间与到期/下次触发分开。补记昨天的事，记录时刻仍是今天实际保存的时刻，事件发生日期另按用户表达保留。
- 普通内容/状态编辑和后台滚动不重置原记录时间。只有明确纠正时才更新，不能清空后自动改成现在。
- 原21字段、类型、枚举不变，不另加一列代替原字段。created_at/updated_at 是本地内部创建/最近写入元数据，不代替业务记录时间，updated_at 也不等于用户亲自编辑。

### 云端与其他平台

记录时间的值也传完整时间戳，例如 `{"记录时间":{"date":"2026-11-07T10:25:36+08:00"}}`，载荷包装按适配器帮助。写入后回读，确认同一实际时刻和秒精度；服务返回等价 UTC 值可以接受，展示时转回用户时区。
schema.json 的 date.format 沿用原兼容显示设置；界面只显示日期不足以证明实际保存或截断了时分秒，要读实际值。不凭猜测提交未知日期格式字符串。
若实际后端截断时间，核对它的日期时间字段/精度设置，在已授权范围内使用可验证的选项并回读。无法满足时报告精度限制，不声称已保存秒，也不擅自改列类型、换库、把时间藏进内容或覆盖原文。

## 按日期检索

先按用户时区把“今天”“本周”“上个月”等解析为日历日期范围，再筛记录时间；不要混同到期或完成于。
云端支持时间范围时，使用首日当地零点包含、末日次日当地零点不包含：

```text
记录时间 >= 用户时区首日 00:00:00
记录时间 <  用户时区末日的下一天 00:00:00
```

例如上海查2026年11月7日，范围为 `[2026-11-07T00:00:00+08:00, 2026-11-08T00:00:00+08:00)`，等价 UTC 为 `[2026-11-06T16:00:00Z, 2026-11-07T16:00:00Z)`。
不能用“等于 YYYY-MM-DD”匹配新时间戳，也不能只截原字符串前10位，因为保存偏移可能不同。结束用次日零点而非23:59:59，以兼容历史小数秒。夏令时地区从本地日历算下一日边界，不机械加24个UTC小时；当地日可能是23或25小时。

### 旧值与分页

纯日期旧值保持日期精度，按已知日历标签参与匹配；不能补造零点、偏移或时分秒，也不随查询时区把未知时刻跨日搬动。未知空值保持未知，不以导入时刻冒充，日期查询不把它算进某天。
云端按实际过滤器兼容时间戳和旧日期候选，必要时分支查询后合并去重。服务端不能准确筛选时，完整分页读取适当候选并按用户日历规范化，不在只读一页后断言无记录。
日期与领域/状态/主题等条件组合后，核对总数，再做最终结果分页；不要先截一页再筛日期。

### 可选本地 CLI

```bash
python scripts/jidou.py list --date 2026-11-07
python scripts/jidou.py list --from-date 2026-11-01 --to-date 2026-11-07
python scripts/jidou.py list --date 2026-11-07 --timezone America/New_York
python scripts/jidou.py list --date 2026-11-07 --domain 工作 --limit 20 --offset 0
```

--date 是单日；--from-date/--to-date 是包含两端的日期范围，可只传一端；两种写法不混用。默认库中用户时区，--timezone 只覆盖本次查询，不改设置。
本地在数据库结果分页前按实际时刻的目标日历日筛选，并纳入旧日期值，不要求整库回读到 agent 再筛。旧 API 的 `filters={"记录时间":"2026-11-07"}` 也按日匹配新旧记录。
当前计算匹配行的日历日，未新增持久日期索引；大库如需优化先实测，不以错误的字符串前缀替代跨时区判断。

## 旧数据与升级

只改变新记录默认写入与查询规则，不批量改旧记录。导入/导出保留原时间戳、旧日期或未知空值及原精度。新捕获不能用纯日期冒充完整时间；无明确纠正时，旧记录原值保持不变。
补齐历史时间只能用已验证的原始创建时间或用户明确提供的事实，在获准范围内处理，不能从当前导入元数据猜测。
仓库发布不等于已修改实际云表、任务或历史数据；云端实例使用更新后的流程时仍要做真实读写回读核验。

## English: capture timestamps and calendar-date search

Capture time is an offset-aware ISO timestamp at second precision, such as `2026-11-07T10:25:36+08:00`. Use a real clock and the configured user timezone. Keep it separate from due/event time, preserve it on ordinary edits, and do not infer timezone from language.
New captures must not substitute a date-only value for a timestamp. Historical imports keep their original timestamp, date-only precision, or unknown empty value. Do not manufacture midnight or the import time as historical capture time.
For a calendar day, use local midnight inclusive through the following local midnight exclusive. Convert actual instants to that timezone; the stored string’s date prefix may be wrong for the user. Compute the next local calendar date rather than adding 24 UTC hours across DST.
Legacy dates match their known calendar label; unknown times do not match an invented day. Include both old and new records and combine filters before final pagination. In cloud adapters, verify actual range and timestamp precision instead of guessing from a date-only display format.
The optional local CLI supports `list --date YYYY-MM-DD`, inclusive `--from-date`/`--to-date` ranges, and a read-only `--timezone` override. These combine with search, domain/status, and pagination.

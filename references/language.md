# Language and locale handling

This is agent guidance. English-speaking users should be able to capture, retrieve, update, and schedule items without learning Chinese field names or commands. The skill’s instructions may contain Chinese; that does not set the language of the conversation.

## User-facing language

- Follow an explicit language preference; otherwise use the language of the user’s current request. Respond in English to English requests. Do not infer country, timezone, or calendar from language.
- Keep note summaries, user-facing categories, confirmations, and assistant-composed reminders in the requested language. Translate display labels, not stored schema keys or enum values.
- Preserve each original passage exactly in 原文, including spelling, punctuation, line breaks, and mixed languages. Never translate original text in storage. A requested translation is a separate summary/view.
- Preserve names and existing topic links across languages. “Add this to the weekly report idea” can refer to an existing Chinese note; clarify only when the match is ambiguous.
- Keep existing source content in its original language unless the user asks for a translated view. Do not rewrite old notes just because the conversation changes language.
- Handle secrets before storage as in SKILL.md, including in original text. Ordinary conversation or a request to save elsewhere must not silently create a Jidou entry.

Useful initial prompts: “Make a note: could we automate the weekly report?”, “Rent is due on the 5th. Remind me two days before”, and “Every Monday, organize last week’s notes.” Show only the capabilities actually ready.
Example confirmation: “Saved the idea and the task. The task doesn’t have a reminder time yet.”

## Dates and local time

Use the configured user timezone and a real current clock. Preserve existing preferences. For a new time-dependent setup without a known timezone, ask once before committing a schedule; do not silently accept Asia/Shanghai just because it is the package fallback, and do not assume English means a US timezone.

- Convert explicit 12-hour times to 24-hour time internally: 3 p.m. → 15:00, 12 a.m. → 00:00, 12 p.m. → 12:00.
- Resolve “tomorrow” and “next Friday” in the user’s timezone. Confirm a concrete date when the wording could select different occurrences.
- Clarify an ambiguous numeric date such as 04/05 rather than guessing April 5 or May 4. Spell out months in confirmations when helpful.
- Date-only reminders may use an agreed default such as 09:00, stated in the confirmation. A date is not permission to invent an unknown event time silently.
- Persist timestamps with an explicit offset and the applicable IANA timezone in configuration/rule options. DST gaps or overlaps require disambiguation; do not silently shift the event.
- Weekdays are Monday–Friday, not a holiday-aware business calendar. Validate a regional calendar when the user needs public holidays or adjusted workdays.
- “Every two weeks” and “every N days” need a persistent start date/anchor. Keep the real event time separate from the reminder lead.
- Chinese lunar dates are a distinct calendar; ask about an ambiguous leap month and use a verified converter when needed.

The package’s quiet-hour defaults apply in the configured timezone. Do not change existing timezone or quiet hours during a language switch.

## Storage translation belongs to the agent

The existing 21-field contract is stable. The English labels below are an agent-facing mapping, **not new JSON aliases accepted by the CLI**. Use the original keys when calling tools. Keep ordinary note content in the user’s language; only controlled schema values are normalized.

| Stored key | English meaning |
|---|---|
| 内容 | Concise content / summary |
| 类型 | Item type |
| 标签 | Tags |
| 线索 | Topic/thread identifier |
| 记录时间 | Capture date |
| 状态 | Status |
| 到期 | Actual due/event time |
| 提醒 | Reminder lead selection |
| 重复 | Recurrence/options |
| 下次触发 | Next event occurrence |
| 静音至 | Muted until |
| 完成于 | Completion date |
| 执行 | Execution mode |
| 执行内容 | Execution recipe |
| 任务ID | Actual task identifier |
| 上次结果 | Structured result/receipt |
| 领域 | Domain |
| 优先级 | Priority |
| 相关人 | People |
| 来源 | Source |
| 原文 | Verbatim original passage |

Controlled values, from [schema.json](schema.json):

| Field | English display → stored value |
|---|---|
| Item type | Idea → 想法; Task → 待办; Event → 事件; Reference → 参考; Decision → 决策; Quote → 摘录; Question → 疑问; Plan → 计划; Reflection → 复盘; Scheduled action → 定时 |
| Status | To review → 待看; In progress → 进行中; Completed → 已完成; Archived → 归档 |
| Domain | Work → 工作; Everyday life → 生活; Learning → 学习; Health → 健康; Finance → 财务; Other → 其他 |
| Priority | High → 高; Medium → 中; Low → 低 |
| Reminder | Off → 不提醒; At event time → 准时; 10 minutes before → 提前10分钟; 1 hour before → 提前1小时; 1 day before → 提前1天; 3 days before → 提前3天; 1 week before → 提前1周 |
| Execution | Reminder only → 仅提醒; Script → 脚本; API → API; Skill → 技能; Multiple steps → 组合 |

Normalize enum values; do not rename fields, replace cloud option IDs, or migrate records to an English schema. Filters also use canonical stored values. Translate those values in the reply rather than dumping raw tool JSON.

## Recurrence bridge

Translate English scheduling intent into the supported canonical rule before calling the native CLI or the existing cloud adapter. The deterministic local parser accepts these stored forms, not arbitrary English prose:

| User intent | Canonical stored rule |
|---|---|
| Every day at 9 p.m. | 每天 21:00 |
| Every weekday at 9 a.m. | 每个工作日 09:00 |
| Mondays and Thursdays at 8 p.m. | 每周一、周四 20:00 |
| Every other Monday at 9 a.m. | 每两周的周一 09:00, with a persistent anchor |
| Every three days at 9 a.m. | 每3天 09:00, with a persistent anchor |
| The 5th of every month at 10 a.m. | 每月5号 10:00 |
| The last day of every month at 6 p.m. | 每月最后一天 18:00 |
| Every March 28 at 9 a.m. | 每年3月28日 09:00 |
| The 28th day of the third Chinese lunar month | 每年农历三月二十八 09:00, after confirming the event time |

Use the existing JSON options in 重复 for timezone, anchor, custom lead_minutes, or override_reminder_at. For example, a two-hour lead is `{"rule":null,"lead_minutes":120}` for a one-off item; the reminder selection is 准时 and 到期 remains the actual event time. Do not write “two hours before” into an enum or subtract the lead from the event date itself.
Follow [reminders.md](reminders.md) for month-end skipping, completion/skip/undo semantics, and delivery limits. An unsupported rule must be clarified or reported as unscheduled, not replaced with a guessed schedule.

## Backend and background behavior

Use the existing selected store and platform tools. English language is not a reason to choose the local extension, create a new database, install Python, or enable a background task. Native installation and advanced operations are explained in the [English installation guide](install.en.md).
When composing an agent-based cloud reminder or scheduled task, include the desired output language and timezone in its task instructions; a detached worker must not rely on the language of an old chat. Do not add those preferences as extra business columns.
Direct native CLI JSON retains canonical Chinese field/enum labels, and the lightweight native notifier retains its existing fixed labels. This update localizes the conversational experience and documentation; it does not introduce a fully translated low-level CLI. The assistant should present friendly English results rather than exposing that internal interface as the user workflow.
Updating this package does not change already deployed cloud prompts. Only synchronize an existing task when requested and preserve its enabled/disabled state.

## Short agent walkthrough

Assume the existing user timezone is America/New_York and the user says: “Rent is due December 5 at 10 a.m. Remind me two days before.”
Keep that English sentence verbatim in 原文, summarize in English, classify as 待办/财务, and retain the actual December 5 event time with the date’s offset. Use a 2880-minute lead in structured options; ask about recurrence if the user did not request a monthly series. When the selected backend and reminders are ready, confirm in English with both event and reminder times. If delivery is not enabled, say the note was saved and the reminder is not active yet.

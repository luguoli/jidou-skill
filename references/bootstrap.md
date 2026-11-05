# 首次初始化

> ⛔ **这份文件只有在用户明确回答"第一次用，建吧"之后才执行。**
>
> 判断依据是 `first-run.md` 的「三查一问」：配置文档 → 「速记箱」表 → 全空间标题搜索，三查全落空才问用户。**三查里任意一查命中，都不是初始化，是补缺**——别跑本文件。
>
> 三查全空，才轮到你问。问了、用户说"建"，才从头往下走。
>
> **不许把"我判断是空的"当成"用户同意建"。** 建完还往凭证里写「用户确认新建」，等于伪造一条他没做过的授权——这是比不问更严重的事。

新用户第一次用这个技能时，跑完这一份，得到的东西和作者当前的状态完全一致：一张表（21 字段）、一个每小时运行的提醒任务、一份配置凭证、一套目录（`速记箱/` 加两个子目录）。**具体是哪 21 个字段、哪两个子目录，这里不列**——字段在第四节 JSON 里，目录在 `SKILL.md` 第二节的规范表里。

**目标是一次装好，不留下"以后再补"。** 全程只做加法，重复执行不会产生第二张表、第二个任务或第二份凭证。

## 零、先确认是不是真的第一次

**不要从这一步直接建东西。** 判断规则、三查的顺序、每查的具体命令、提问话术、三种回答怎么处理，**全在 `references/first-run.md`，本文件一句都不重写**。上面文件头那五行是执行前的提醒，不是第二份规则。

这里只补一件 first-run 没写的事：**判断结果（`init_mode`）在第六点五节写进配置凭证**，那是下次不再问的依据。表建完、任务建完、凭证写完，这套才算装好；缺凭证，下次会当没装过。

## 一、前置检查

这一步在任何环境下都一样：**首次使用、换设备、换账号、定时任务里跑，都走同一套流程。**

不要靠"本地有没有某个文件"来判断装没装过。定时任务跑在独立的执行环境里，本地目录可能是空的；用户换台设备，同样为空。**唯一可信的依据是云端有没有表和任务。**

```bash
# 技能根目录：换平台只改这一行，下面三个路径自动跟着变
SKILLS="${CODEBUDDY_SKILL_DIR:-/root/.codebuddy/skills}"
[ -d "$SKILLS" ] || SKILLS="$HOME/.codebuddy/skills"

LIB="$SKILLS/library"
[ -f "$LIB/space_api.py" ] || echo "library 技能缺失"
```

`/root/.codebuddy/skills` 是当前环境的默认值，不是硬性要求。换平台改 `SKILLS` 一行即可，其余不动。

缺了就先装 library，缺它整个技能无法工作。

**同时确认技能目录结构在。** 目录不存在就建，顺序固定：

```bash
QS="$SKILLS/quicksave"
ATM="$SKILLS/automation-task-manager"

mkdir -p "$QS/archive" "$QS/references"
```

目录里只放固定几样东西，规则见 `SKILL.md` 第十三节。**不要在这里生成任何临时文件**，初始化不该留下痕迹。

## 二、定位个人空间

```bash
cd "$LIB" && python3 space_api.py space.workspace.list-user-spaces --limit 100
```

取 `category == "personal"` 那条的 `spaceId`。正常只有一个；出现多个时问用户用哪个，不要猜。

## 三、查速记箱是否已存在

```bash
cd "$LIB" && python3 space_api.py space.workspace.list-nodes --space-id "<spaceId>" --limit 100
```

在 `data.nodes[]` 里找 `title == "速记箱"` 且 `kind == "database"`。

- 找到 → 记下 `id`，跳到第五节
- 没找到 → 继续第四节
- `hasMore` 为 true → 用 `--offset` 翻完再下结论

## 四、建表

先准备目录：根目录 `list-nodes` 找 `kind == "folder"` 且标题为「速记箱」的节点，没有就 `manage/create_folder.py --title "速记箱"` 建一个，把 id 填进下面 JSON 的 `parent_id`。**表不建在根目录**，否则根目录会越用越乱。

再建两个子目录，**不是可选项**：

```bash
cd "$LIB" && python3 manage/create_folder.py --title "备份" --space-id "<spaceId>" --parent-id "<速记箱目录 id>"
cd "$LIB" && python3 manage/create_folder.py --title "自动化任务归档" --space-id "<spaceId>" --parent-id "<速记箱目录 id>"
```

漏了这两个，`SKILL.md` 第二节规定的落点就无处可落：导出 CSV 只能塞根目录，跑批中间文件也一样。规范写了落点、实际没有目录，等于没规范。建完把两个 id 记下来，**填进配置凭证的 `folder_backup_id` / `folder_archive_id`**（见第六点五节），建执行类任务时要写进指令。

一次建好全部 21 个字段，顺序不要改（第一列会成为表格的默认列）：

```bash
printf '%s' '{
  "schema": {
    "title": "速记箱",
    "space_id": "<spaceId>",
    "parent_id": "<速记箱目录 id>",
    "properties": [
      { "name": "内容", "config": { "text": "" } },
      { "name": "类型", "config": { "select": { "options": [
        { "text": "想法" }, { "text": "待办" }, { "text": "事件" }, { "text": "参考" },
        { "text": "决策" }, { "text": "摘录" }, { "text": "疑问" }, { "text": "计划" }, { "text": "复盘" }, { "text": "定时" }
      ] } } },
      { "name": "标签", "config": { "text": "" } },
      { "name": "线索", "config": { "text": "" } },
      { "name": "记录时间", "config": { "date": { "format": "yyyy-mm-dd" } } },
      { "name": "状态", "config": { "select": { "options": [
        { "text": "待看" }, { "text": "进行中" }, { "text": "已完成" }, { "text": "归档" }
      ] } } },
      { "name": "到期", "config": { "date": { "format": "yyyy-mm-dd" } } },
      { "name": "提醒", "config": { "select": { "options": [
        { "text": "不提醒" }, { "text": "准时" }, { "text": "提前10分钟" },
        { "text": "提前1小时" }, { "text": "提前1天" }, { "text": "提前3天" }, { "text": "提前1周" }
      ] } } },
      { "name": "重复", "config": { "text": "" } },
      { "name": "下次触发", "config": { "date": { "format": "yyyy-mm-dd" } } },
      { "name": "静音至", "config": { "date": { "format": "yyyy-mm-dd" } } },
      { "name": "完成于", "config": { "date": { "format": "yyyy-mm-dd" } } },
      { "name": "执行", "config": { "select": { "options": [
        { "text": "仅提醒" }, { "text": "脚本" }, { "text": "API" }, { "text": "技能" }, { "text": "组合" }
      ] } } },
      { "name": "执行内容", "config": { "text": "" } },
      { "name": "任务ID", "config": { "text": "" } },
      { "name": "上次结果", "config": { "text": "" } },
      { "name": "领域", "config": { "select": { "options": [
        { "text": "工作" }, { "text": "生活" }, { "text": "学习" },
        { "text": "健康" }, { "text": "财务" }, { "text": "其他" }
      ] } } },
      { "name": "优先级", "config": { "select": { "options": [
        { "text": "高" }, { "text": "中" }, { "text": "低" }
      ] } } },
      { "name": "相关人", "config": { "text": "" } },
      { "name": "来源", "config": { "text": "" } },
      { "name": "原文", "config": { "text": "" } }
    ]
  }
}' | python3 "$LIB/database/create_database_with_records.py" --stdin
```

返回的 `database_id` 记下来，后面要用。

**建表时不要带 `records`**，空表建立最稳。带初始记录容易因为一条字段写错导致整批失败，还得回头补。

如果报「部分初始记录写入失败」但给了 `database_id`，说明表已经建成，直接用这个 ID 继续，**不要重建**。

## 五、查提醒任务是否存在

```bash
cd "$ATM" && ./scripts/scheduler-api.sh list --keyword "速记提醒"
```

看返回的 `data.tasks[]`：

- 有同名任务且 `status == 1` → 已就绪，跳到第六节
- 有同名任务但停用了 → `update --id <id> --status 1` 启用
- 没有 → 继续创建

## 六、创建提醒任务

先把指令里的表 ID 换掉，再提交：

```bash
# 临时文件放独立目录，用完删，不要落在技能目录里
mkdir -p /tmp/qs-task
sed -e "s|__DATABASE_ID__|<database_id>|g" \
    -e "s|__SKILLS_DIR__|$SKILLS|g" \
    "$QS/references/reminder-prompt.md" > /tmp/qs-task/reminder.txt

# 三道校验，缺一不可。任何一道不过就停，不要"先建了再说"
grep -q "__" /tmp/qs-task/reminder.txt && { echo "占位符没替换完，停"; exit 1; }
[ -d "$SKILLS/library" ] || { echo "脚本路径不存在：$SKILLS/library，停"; exit 1; }
grep -q "database_id=<" /tmp/qs-task/reminder.txt && { echo "表 ID 没填，停"; exit 1; }

cd "$ATM" && ./scripts/scheduler-api.sh create \
  --name "速记提醒" \
  --cron "0 0 * * * *" \
  --prompt "$(cat /tmp/qs-task/reminder.txt)" \
  --frequency-type "interval" \
  --timezone "Asia/Shanghai" \
  --description "每小时扫描资料库速记箱，推送待办/循环任务/事件的到期提醒" \
  --timeout 600 --retry-count 2
```

建完立刻回读一次，确认存进去的就是刚才那份，而不是旧缓存：

```bash
cd "$ATM" && ./scripts/scheduler-api.sh get --id <id> \
  | python3 -c "import json,sys; p=json.load(sys.stdin)['data']['agentConfig']['prompt']; print('长度',len(p)); print('占位符残留', p.count('__')); print('路径存在', '$SKILLS/library' in p)"
```

三个值应该是：长度与 `references/reminder-prompt.md` 原文件相当（替换只改 id 和路径，字符数差不超过几十）、占位符残留 0、路径 True。不对就 `update --prompt` 重推一遍。

**别在这里写死期望长度。** 模板每改一次长度就变，写死一个数字，下次改完这条校验就假报警，久了就没人看它了。

**为什么非要回读**：新建或更新之后，有时接口返回成功但读到的还是旧内容；只看返回码会以为改好了，实际任务里跑的还是老指令。

Cron `0 0 * * * *` 是六段格式（秒 分 时 日 月 周），含义是每小时整点。返回里的 `nextRunAt` 就是第一次运行时间。

建完顺手清掉临时目录，别留在 /tmp 里累积：

```bash
rm -rf /tmp/qs-task
```

**频率可以在初始化时按用户情况调整**：他说"不要每小时"就换成 `0 0 8,20 * * *`（每天 8 点和 20 点）或 `0 0 8 * * *`（每天 8 点）。默认每小时，因为小时级提前量（提前10分钟、提前1小时）只有在这个频率下才有意义。

## 六点五、写配置凭证

**这一步不是可选的。** 没有凭证，下次换环境会被当成"第一次"，然后重复问用户、甚至重复建表。

用 `references/config-doc.md` 作模板，替换占位符后建成文档，放在「速记箱」目录下（与表同目录；目录不存在就先建，见 SKILL.md 第二节）：

```bash
# 先拿到「速记箱」目录的 id，没有就建一个。列根目录不要传 --parent-node-id，留空字符串有些实现会报参数错误
cd "$LIB" && python3 space_api.py space.workspace.list-nodes --space-id "<spaceId>" --limit 100
cd "$LIB" && python3 manage/create_folder.py --title "速记箱" --space-id "<spaceId>"
```

```bash
mkdir -p /tmp/qs-task
sed -e "s|__SCHEMA_VERSION__|<SKILL.md 里的 version>|g" \
    -e "s|__SPACE_ID__|<spaceId>|g" \
    -e "s|__DATABASE_ID__|<database_id>|g" \
    -e "s|__FOLDER_ID__|<速记箱目录 id>|g" \
    -e "s|__FOLDER_BACKUP_ID__|<速记箱/备份 id>|g" \
    -e "s|__FOLDER_ARCHIVE_ID__|<速记箱/自动化任务归档 id>|g" \
    -e "s|__TASK_ID__|<提醒任务 id>|g" \
    -e "s|__TODAY__|$(date +%F)|g" \
    -e "s|__INIT_MODE__|<首次使用，用户确认新建 / 迁移 / 重建 / 存量表，未询问>|g" \
    -e "s|__FIELD_COUNT__|21|g" \
    "$QS/references/config-doc.md" > /tmp/qs-task/config.md

grep -q "__" /tmp/qs-task/config.md && { echo "占位符没替换完，停"; exit 1; }

cd "$LIB" && python3 doc/create_doc.py \
  --title "速记箱·配置" --space-id "<spaceId>" --parent-id "<速记箱目录 id>" \
  --content-file /tmp/qs-task/config.md
rm -rf /tmp/qs-task
```

**`init_mode` 必须如实写**：用户说是第一次就写「首次使用，用户确认新建」；从旧空间搬过来写「迁移，来自原空间 xxx」；旧表删了重建写「重建，旧表已删（用户确认）」。这一栏决定下次要不要再问。

**「用户确认」这四个字有门槛。** 只有真的问过、用户真的答了，才能写。没问就写，等于把一条他没做过的授权永久存在云端，之后任何环境、任何 agent 读到都会相信，而且没人会去核对。

**不给"先建后问"留出口。** 本文件开头就规定了必须问过才建，所以不存在"没确认但表已经建好"的正常路径。唯一会遇到的是**存量**：表在上个版本、别的 agent 或用户自己手里就已经存在。这时凭证写：

```
init_mode = 存量表，未询问（凭证于 <日期> 补写）
```

并在当次对话里主动说明一句。存量是既成事实，补凭证是为了下次不再误判；主动告知是为了不让它悄悄变成默认动作。

写完回读一次，确认三件事：标题是「速记箱·配置」、`database_id` 与真实表一致、没有 `__` 残留。

**顺序不能反。** 先建表建任务，最后写凭证；写到一半失败就当没写，不要留一份空的凭证——空凭证比没有更糟，会让下次误判成"已装好"却找不到表。

## 七、告诉用户装好了

不用罗列建了什么表和任务，说人话：

> 好了，现在你随口说「记一下……」我就存进去。带时间的会自动提醒，循环的会一直跟。

**别只说到这里。把 `references/onboarding.md` 的能力总表整张贴出来**（30 项），再贴**十种类型各一句**，然后**把定时拆成两种讲**（到点叫你 / 到点替你干，各自能设哪些形态），最后给三条分属不同用途的试说句（记录 / 提醒 / 定时执行，不能三条都是记一条）。新人不知道能干什么，等于这些能力不存在——尤其「定时跑脚本」「定时调 API」这两项，不主动说他想不到。

**定时只说「可以定时提醒」等于漏了一半。** 提醒只是叫一声，执行是到点自己干活，两者的建法、精度、失败处理都不同：提醒共用每小时扫表（精度小时级），执行每条一个独立任务（精度分钟级、有重试、有回执）。不拆开讲，用户既想不到能让它干活，也会误以为「每两周的周一」「农历生日」之类的执行频率可以随手设。

**示范不能只举「记想法」。** 十种类型是这套东西与普通备忘录的全部差别：只演想法和待办，用户就会当备忘录用，参考、摘录、疑问、决策、计划这五类永远不会被碰到，而它们恰恰是最容易丢的东西——决策尤其，当时说得清清楚楚，两个月后没人记得为什么这么定。

## 七点五、执行类任务不预建

初始化只建**一个**任务：每小时扫表的「速记提醒」。

脚本、API、技能这类**定时执行任务不预建**，它们由用户提出需求时逐个创建。原因很实在：不知道要跑什么，没法预建；预建一堆空任务只会占用额度、拉长列表。

所以初始化「四样齐全」的判断里，**不包含**执行类任务——四样是哪四样，定义在 `SKILL.md` 第零节那张自检表里，本文件不重列。装好是 1 个任务，之后每加一个执行任务就多一个，各自独立。

## 八、幂等性检查表

重复执行时逐条确认，任何一步已满足就跳过：

| 检查项 | 已存在时的处理 |
|---|---|
| 个人空间 | 复用，不新建 |
| 速记箱目录 | 复用，不建第二个同名目录 |
| 速记箱/备份、速记箱/自动化任务归档 | 逐个 `list-nodes` 看，缺哪个补哪个。**这两个不建，产物就无处可落** |
| 速记箱表 | 复用现有 ID，不建第二张 |
| 21 个字段 | 缺哪个补哪个，用 `add_database_field.py`；已有的不动 |
| 选项 | 缺失的追加，已有的保留原 ID，绝不重建整个 select。领域要确认是 6 项、类型 10 项、执行 5 项 |
| 提醒任务 | 按名称 + status 判断，启用或跳过，不重复建 |
| 配置凭证 | 有就更新 `schema_version` / `field_count`，没有才建 |

**字段和选项只增不删。** 删字段会清空该列所有数据，删选项会清空引用它的单元格——这是不可逆的，任何情况下都不做。

## 九、初始化后，自己产生的临时文件要清掉

初始化会写几份临时文件（`/tmp/qs-task/`、`schema.json`、替换好占位符的 `config.md`）。**这些用完就删**，`/tmp/qs-*` 是主要来源——执行环境可能被复用，留着会混进下一次执行，下次读到旧表 ID 会直接失败。

```
<技能根目录>/quicksave/
├── SKILL.md
├── CHANGELOG.md
├── references/      已有文档，初始化不新增
└── archive/         可为空，有版本快照后才有内容
```

**只删自己刚建的那几个临时文件。** 目录里原有的其他文件——`archive/` 里的旧快照、用户自己放进来的笔记、别的技能留下的东西——一律不动，也不算"多出来的"。判定依据只有一条：这次执行里由我创建、且路径已知。判断不出来就留着。

这一步不做也不影响功能，但会积累成"半年后没人敢动"的目录。一次做对，后面省事。

# 一致性检查

这份文件只回答一个问题：**改完之后，怎么确认没有把别处改坏。**

前面十几轮的冲突，几乎全部来自同一个原因——**同一个事实写在了好几个地方**。字段清单在四处各写一遍，枚举在五处各列一遍，"三查"和"四级"两种叫法混用。改一处、漏三处，于是每次检查"又发现新的"。

治法是两条：**一、定义只留一处，别处只放指针**（第一节）；**二、改完跑机器检查，不靠通读**（第二节）。

## 一、单一事实源（SSOT）

下面左列的事实，**只有中间那个文件是权威**。右列写的是"别处该怎么出现"——注意区分两种：**指针**（一句话 + 见哪里）和**豁免副本**（必须自带，不同步就会有功能损失）。

| 事实 | 唯一定义处 | 别处怎么出现 |
|---|---|---|
| 21 个字段的名字、顺序、类型、选项 | `bootstrap.md` 第四节 `properties` JSON | SKILL 第二节字段表只做**语义说明**，选项必须与它逐字一致；`dependencies.md` 一律不列 |
| 字段的中文含义与填写规则 | `SKILL.md` 第二节「说明」列 | 其余文件只引用，不复述 |
| 六个枚举的选项总数（10/4/7/5/6/3） | 同上，`bootstrap.md` 第四节 | 只在检查脚本里写死，正文不写数字 |
| 建目录、建表、建任务、写凭证的命令 | `bootstrap.md` 第二～六点五节 | SKILL 步骤 2A **只写三条约束**（parent_id 必须是目录、两个子目录同批建、建完回读），不贴命令 |
| 首次判断的顺序与提问话术 | `first-run.md` 第一、二节 | SKILL 一句话说顺序 + 门禁；bootstrap 指过去，不抄话术 |
| 提醒任务的判断算法 | `reminder-prompt.md` | SKILL 第六节末只写三行摘要（触发点 / 提前量 / 落区间），不复述全文 |
| 提醒任务本身的参数（cron、时区、超时、重试） | `SKILL.md` 第六节末那张表 | `dependencies.md` 不重复列；表里的值必须与 `scheduler-api.sh get` 的实测一致 |
| 目录规范（`记兜/`、`备份/`、`自动化任务归档/`、`skills/`、`敏感配置/`） | `SKILL.md` 第二节 | bootstrap 只写"建哪两个目录"的执行动作；upgrade、dependencies 引用 |
| 配置凭证的键 | `config-doc.md` 模板 | SKILL 零节只列键名，不列值 |
| 备份 / 回滚命令 | `upgrade.md` 第三节（备份）、第五节（回滚） | SKILL 第十五节只指过去，不贴命令 |
| 版本号怎么定、三条铁律 | `upgrade.md` 第一、二节 | SKILL 第十五节只写铁律名字和"何时必须先问"，不重复规则 |
| 实例值（spaceId / database_id / folder / 任务 ID / 字段 ID） | 云端配置文档，其余全靠现场取 | `dependencies.md` 只写**取法**；任何 Markdown 不得出现具体值 |
| 版本号 | `SKILL.md` front-matter | CHANGELOG 顶部、`archive/` 文件名 |

### 允许重复的三处（豁免，不是疏漏）

| 位置 | 重复了什么 | 为什么不能删 |
|---|---|---|
| `reminder-prompt.md` 的字段行 | 21 个字段名 | 它是**灌进定时任务的独立 prompt**，运行时读不到技能目录里的任何文件。删了它，任务就不知道往哪写 |
| `onboarding.md` 的类型 / 领域枚举 | 选项举例 | 面向用户解释"我能识别哪些"，用户不会去读 bootstrap。措辞可口语化，但**取值必须与权威一致** |
| `SKILL.md` front-matter 的 `summary` | 领域 6 类、能力概要 | 平台靠它做技能路由，必须自描述，不能写"见某文件" |

**除这三处，任何"同一份清单出现第二遍"都算缺陷**，不是"多写一遍保险"。多写一遍的结果从来不是保险，是两份慢慢分叉。

## 二、改完必跑的检查

全部在 `/tmp/jidou-check/` 里跑，跑完删。**不要放进技能目录**——第十三节只允许那四类东西。

### 1. 字段与枚举：唯一权威 + 各副本一致

```bash
mkdir -p /tmp/jidou-check && cd /root/.codebuddy/skills/jidou && python3 - <<'PY'
import re,os
rd=lambda p:open(p,encoding='utf-8').read()
F="内容 类型 标签 线索 记录时间 状态 到期 提醒 重复 下次触发 静音至 完成于 执行 执行内容 任务ID 上次结果 领域 优先级 相关人 来源".split()
b=rd('references/bootstrap.md'); s=rd('SKILL.md'); r=rd('references/reminder-prompt.md')
bad=[]
# 1 权威处
props=re.findall(r'\{ "name": "([^"]+)"',b)
if props!=F: bad.append(f"bootstrap 字段={props}")
# 2 SKILL 第二节字段表：名字与顺序
seg=s[s.find('| 字段 | 类型 | 说明 |'):s.find('这个顺序就是建表顺序')]
rows=[x.strip() for x in re.findall(r'^\| ([^|\n]+?) \| (?:text|select|date) \| ',seg,re.M)]
if rows!=F: bad.append(f"SKILL 二节字段表={rows}")
# 3 SKILL 二节 select 行的选项 必须等于 bootstrap 的选项
def opts(n):
    mm=re.search(r'\{ "name": "%s", "config": \{ "select": \{ "options": \[(.*?)\] \} \} \}'%n,b,re.S)
    return re.findall(r'\{ "text": "([^"]+)" \}',mm.group(1))
for n in ['类型','状态','提醒','执行','领域','优先级']:
    line=[l for l in seg.split('\n') if l.startswith(f'| {n} |')]
    if not line: bad.append(f"SKILL 二节缺 {n} 行"); continue
    vals=[v.strip() for v in line[0].split('|')[3].split('/')]
    vals=[v.split('。')[0].strip() for v in vals]
    if vals!=opts(n): bad.append(f"SKILL {n} 选项 {vals} ≠ bootstrap {opts(n)}")
# 4 reminder-prompt 副本（豁免但不能飘）
rm=[x.strip() for x in re.search(r'字段：(.*?)\n',r).group(1).split('、')]
if rm!=F: bad.append("reminder-prompt 字段行")
print("权威字段数",len(props))
for n in ['类型','状态','提醒','执行','领域','优先级']: print(f"  {n}: {len(opts(n))}")
print("结论:", "全部一致" if not bad else bad)
PY
```

`SKILL` 二节的选项列是**唯一允许出现的第二份枚举**（因为读文档的人需要就地看懂），所以它必须逐字等于权威处——不是"大意一致"，是逐字。

### 2. 还有没有第三份清单

```bash
cd /root/.codebuddy/skills/jidou && python3 - <<'PY'
import re,os
# 每个文件允许出现的清单份数上限，超出就是又抄了一份
cap={'SKILL.md':1,'references/reminder-prompt.md':1,'references/onboarding.md':2}
pats={'类型串':r'想法[^\n]{0,8}待办[^\n]{0,8}事件','状态串':r'待看[^\n]{0,12}归档',
'提醒串':r'不提醒[^\n]{0,8}准时[^\n]{0,8}提前10分钟','领域串':r'工作[^\n]{0,8}生活[^\n]{0,8}学习[^\n]{0,8}健康',
'字段串':r'内容[^\n]{0,8}类型[^\n]{0,8}标签[^\n]{0,8}线索'}
files=['SKILL.md']+['references/'+x for x in sorted(os.listdir('references')) if x!='consistency.md']
tot=0
for name,p in pats.items():
    for f in files:
        t=open(f,encoding='utf-8').read()
        if f=='SKILL.md':   # front-matter 的 summary/description 是自然语言，平台要用，不参与统计
            t=t.split('---',2)[2]
        n=len(re.findall(p,t))
        if not n: continue
        lim=cap.get(f,0)
        flag="" if n<=lim else f"  ← 超限（上限 {lim}）"
        if flag: tot+=1
        print(f"{name}  {f}: {n} 处{flag}")
print("结论:", "无多余副本" if not tot else f"{tot} 处需要删成指针")
PY
```

`SKILL.md` 上限 1 = 只有第二节字段表那一份（front-matter 的 `summary` / `description` 是自然语言，平台要靠它做路由，不参与统计）。`reminder-prompt.md` 上限 1 = 它那份必须自带的字段行。`onboarding.md` 上限 2 = 面向用户的两处举例。**其余文件上限是 0**，出现就是新增了第三份，回去删掉改成指针。

这条是新加的：以前只查"值对不对"，不查"是不是又抄了一份"，所以文档越改越长，越长越难改。

### 3. 占位符覆盖

```bash
cd /root/.codebuddy/skills/jidou && python3 - <<'PY'
import re
b=open('references/bootstrap.md',encoding='utf-8').read()
sed=set(re.findall(r's\|(__[A-Z_]+__)\|',b))
for f in ['references/config-doc.md','references/reminder-prompt.md']:
    ph=set(re.findall(r'__[A-Z_]+__',open(f,encoding='utf-8').read()))
    print(f,"缺 sed:",sorted(ph-sed) or "无")
PY
```

任何 `__` 残留都会让 bootstrap 里的 `grep -q "__"` 直接 `exit 1`，初始化装不完。这一条真的发生过。

### 4. 交叉引用逐条核对

```bash
cd /root/.codebuddy/skills/jidou && grep -rn "第[一二三四五六七八九十零]\{1,3\}节\|references/[a-z-]*\.md" --include=*.md . | grep -v "^./archive/"
```

输出要逐条看，核两件：

- **节号对不对**：说"第十二节"就要真是那一节。历史上出现过"SKILL 第十二节 表格访问链接"，而那一节实际是"出错怎么办"。
- **路径存在吗**：引用的 `references/*.md` 必须在磁盘上。

### 5. 章节清单

```bash
cd /root/.codebuddy/skills/jidou && grep -n "^## " SKILL.md
```

应始终是 **零到十五，共 16 节**。加节要同时改：本节号之后所有引用、`dependencies.md` 的主流程说明、`portability.md` 的平台相关点表。

### 6. 措辞口径

**不能直接 `grep 三级`。** 这个词有两个无关用法：「按规模分三级」讲的是分表策略，`folder_archive_id` 里也含着 `_archive` 这串字符。裸查会报一堆假警，假警多了这条检查就废了。所以带上下文查：

```bash
cd /root/.codebuddy/skills/jidou && for k in "三级全空" "四级全空" "三级里" "分四级" "三样东西" "已知位置" "已归档" "未确认，自动创建"; do echo "== $k"; grep -rn "$k" --include=*.md . | grep -v "^./archive/" | grep -v "^./CHANGELOG.md" | grep -v "^./references/consistency.md" | grep -v "别写成\|不要写成\|旧名\|旧版本\|曾经\|历史\|禁词\|只该"; done
echo "== _archive（须独立出现）"
grep -rnE "(^|[^A-Za-z0-9_])_archive" --include=*.md . | grep -v "^./archive/" | grep -v "^./CHANGELOG.md" | grep -v "别写成\|不要写成\|不是 \`_archive\`\|旧版本\|禁词"
```

**三处排除，缺一不可：**

- **CHANGELOG**：记的是当时的事实，出现"18 字段""四级判断"是对的，那是历史不是冲突。
- **`consistency.md` 自己**：本文件通篇在列禁词、写检查规则，查自己必然全中。
- **元说明行**（含"别写成""不要写成""旧名""旧版本"）：这类句子是**在禁止某个词**，它必须写出那个词本身。把"不要写成 `_archive`"判成违规，等于让规则没法自我解释。

排除之后还会剩几条，**基本都是"规则在解释自己"**——比如 SKILL 里那句"不要一边叫 `_archive` 一边叫 `archive`"。逐条看一眼：它在**禁止**这个词，就放过；它在**使用**这个词，就改。判断标准很简单——这句话删掉之后，读者会不会照着那个错写法去做。会，就是元说明；不会，就是真的写错了。

| 词 | 只该出现在 | 出现别处说明 |
|---|---|---|
| 三查 / 一问 | `first-run.md` | 又回到"三级""四级"混用 |
| 四样（表 / 字段 / 任务 / 凭证） | SKILL 零节 | 有人写回"三样" |
| `archive` | 全部 | `_archive` 是旧名残留 |
| 「用户确认新建」 | 只有真的问过才写 | 见 `first-run.md` 第五节 |
| 「归档」 | 状态枚举值 | 写成「已归档」写不进去 |

### 7. 实例值残留

```bash
cd /root/.codebuddy/skills/jidou && grep -rnE "\b[A-Za-z0-9]{20,24}\b" --include=*.md . | grep -v "^./archive/" | grep -v "^./CHANGELOG.md"
```

命中应该是：示例占位符、`scheduler-api.sh` 这类命令名。**出现 spaceId、database_id、folder_id、任务 ID、字段 ID 就是错的**——它们只该存在于云端配置文档和任务指令里。

这条最容易反复：每次重建表，都有人"顺手"把新 id 记进文档，觉得这次记着方便。下一次重建，它就变成陷阱。

### 8. 文档描述的事实 vs 运行中的实物

前七项全是**文档之间互校**，这一项是唯一一项出文档的。它查的是：文档里写的值，和正在跑的那个东西，是不是一回事。

```bash
# 任务参数：与本地参数表逐项比
cd /root/.codebuddy/skills/automation-task-manager && ./scripts/scheduler-api.sh get --id <任务ID> \
  | python3 -c "import json,sys;d=json.load(sys.stdin)['data'];print({k:d.get(k) for k in ['cronExpr','timezone','timeoutSec','retryCount']})"

# 表结构与字段数：与 bootstrap 第四节比
cd "$LIB" && python3 database/get_database_schema.py --database-id <database_id>

# 目录结构：与规范比
cd "$LIB" && python3 space_api.py space.workspace.list-nodes --space-id <spaceId> --limit 100
cd "$LIB" && python3 space_api.py space.workspace.list-nodes --space-id <spaceId> --parent-node-id <记兜目录 id> --limit 100
```

**为什么单独列一项：** 2.10.4 就是这样查出错的。参数表写"超时 300 秒"，运行中的任务是 600——文档内部完全自洽，前七项全过，因为错的东西不在文档里。而参数表被定为"唯一权威"，写错意味着将来重建会建出一个和现役不同的任务，且无人察觉。

**凡"描述运行中对象"的值都适用：** 任务参数、字段数、字段选项、目录结构、提醒的 cron。这些东西文档里写得再一致，也只是自说自话。

### 9. 结构与存档

```bash
cd /root/.codebuddy/skills/jidou && python3 -c "
import yaml,re,os
s=open('SKILL.md',encoding='utf-8').read()
print('YAML', yaml.safe_load(s.split('---')[1])['version'])
print('章节', len(re.findall(r'^## ',s,re.M)))
" && ls archive/ | grep SKILL | sort | tail -3
```

三件事：

- front-matter 能被解析，`version` 与 CHANGELOG 顶部一致（解析失败 = 平台读不到技能）
- 章节数仍是 16
- **`archive/` 里有当前版本的快照，且与当前 SKILL.md 逐字相同**

存档这项栽过一次：2.10.2 改完直接进 2.10.3，没存快照，回滚链断了一环，事后补不回来。**升版本和存快照是同一步，不是两步。**

## 三、四种典型的漂移

1. **改数不改表。** 字段从 18 加到 21，正文写"21 个"，但某处表格还是 18 行，或建表 `sed` 里 `__FIELD_COUNT__` 还是 18。→ 数字跟着表走，表是源。
2. **改表不改引用。** 新增一节，后面所有节号平移一位，但 `portability.md` 里"第十二节"没动。→ 加节后必跑检查 4。
3. **加规则不加出路。** 规定"产物落 `记兜/备份/`"，但初始化没建这个目录。→ 每条落点规则，都要能在 bootstrap 里找到对应的建目录动作。
4. **怕漏就再抄一遍。** 明明已有权威处，为了"读着方便"再贴一份，还注明"以另一处为准"。→ 读者会读手边这份，不会去核对。**要么给指针，要么把这份删掉，没有第三种。**

## 四、检查不是每次都要全跑

只在改完文档、加完字段之后跑。日常记录不需要——那时不出问题，出问题的是文档本身。

1–7 项纯本地，几秒钟跑完；第 8 项要连任务和云端，第 9 项要读存档。**只改措辞可以只跑 1–7，凡是动了参数、字段、目录、版本号，8 和 9 必须一起跑**——那两项查的正是本地看不见的错。

跑完把结论说清楚：哪几项通过、哪几项改了。**不要说"检查完了没问题"**，那是没检查。

# SKILL.md 标准格式

技能入口是 UTF-8 编码的 `SKILL.md`，由 **YAML frontmatter 和 Markdown 正文**组成。前面的 YAML 是元数据，不是把技能正文改成 YAML。

```markdown
---
name: jidou
description: 在聊天中记录、检索、整理个人想法与待办。
---

# 记兜 · jidou

这里是给 agent 阅读的 Markdown 操作说明。
```

- 文件名保持 `SKILL.md`，不改成 `SKILL.yaml` 或 `SKILL.yml`。
- 第一行开始用独立的 `---`，结束元数据时再用一行 `---`；正文在第二条分隔线之后。
- `name`、`description` 是必需项。描述可使用 YAML 的普通字符串、引号字符串或折叠多行字符串，解析后必须是非空字符串。
- 当前使用的可选顶层字段是 `license` 和 `metadata`；展示名、版本等扩展信息放在 metadata，而不是随意新增顶层键。
- metadata 使用字符串键和值；版本号写成字符串。不要重复键，也不要用可执行的 YAML 标签。
- `references/*.md`、`scripts/` 和机器可读的 `.json` 是支持文件，不改变入口格式；产品专用的 `agents/openai.yaml` 是可选配置，不是必需入口，本包没有依赖它。

## 怎么确认

先安装 [requirements.txt](../requirements.txt)，运行 `python scripts/validate.py`。它使用真正的安全 YAML 解析器，检测语法错误、重复键、必填字段与版本，并检查 Markdown 引用和 schema 兼容性。
测试包含破坏 YAML、替换等数量枚举、改字段类型、未替换任务 ID 和无效时区等反例，不只检查当前文件能通过。
平台提供的官方技能校验器可进一步交叉验证。文件格式通过不表示对应平台的存储、调度和投递已经实测。

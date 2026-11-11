# 跨平台兼容性说明

> 结论：**能用在别的智能体上，但分两类，别把 `SKILL.md` 整段往网页平台里粘。**
> 本文件里的路径按各平台官方文档核对（2026-11），**未在各平台账号内逐一实测**；如有版本变动以官方为准。

## 为什么不能一律复制 `SKILL.md`

`SKILL.md` 是给**能读写文件的宿主**用的原生 Skill，里面有三样东西对纯聊天平台是噪音：

1. YAML `frontmatter`（`name` / `description` / `agent_created`）——宿主读的元数据，不是给模型执行的指令
2. **宿主能力层**：读写 `state/日课卡.md` 的协议——网页平台没有文件系统，模型可能去尝试调用不存在的工具
3. 内部校准锚点、验收/字数说明——占字数、淹没关键规则

豆包智能体的「设定描述」社区经验值是 **300–600 字**，而 `SKILL.md` 有 3000+ 字，直接粘进去指令遵循率会明显下降。

所以用 `dist/` 里的**自动生成版**：协议单一数据源仍是 `SKILL.md`，`scripts/build_dist.py` 剥离宿主专属段落并替换状态相关措辞，保证两份不会漂移。

---

## 兼容性矩阵

| 平台 | 类型 | 用哪个文件 | 状态闭环 |
|---|---|---|---|
| **WorkBuddy** | 原生 Skill | 整个仓库 → `~/.workbuddy/skills/` | ✅ 教练自动读写状态文件 |
| **Claude Code** | 原生 Skill | 整个仓库 → `~/.claude/skills/universal-learning-mentor/` | ✅ 有文件读写 |
| **Codex**（CLI / 桌面版） | 原生 Skill | 整个仓库 → `$HOME/.agents/skills/universal-learning-mentor/` | ✅ 有文件读写 |
| **Cursor** | Rule / AGENTS.md | `dist/cursor-rule.mdc` 或 `dist/AGENTS.md` | ⚠️ 有文件能力但默认走文本卡 |
| **豆包** | 纯 Prompt 智能体 | `dist/prompt-mini.md`（599 字，含换行标点） | ❌ 文本卡，用户贴回 |
| **ChatGPT / GPTs** | 纯 Prompt | `dist/prompt-plain.md` | ❌ 文本卡 |
| **Claude 网页 / Kimi / 文心 / 通义** | 纯 Prompt | `dist/prompt-plain.md` | ❌ 文本卡 |
| **Coze / 扣子** | 纯 Prompt 智能体 | `dist/prompt-plain.md`（或 mini，若字数受限） | ❌ 文本卡 |

> **状态闭环**那一列的差别只有一处：**谁记日课卡**。协议、四重认知流水线、全部护栏在所有平台完全一致。

---

## 逐平台安装

### 原生 Skill（WorkBuddy / Claude Code / Codex）

这三个都用同一套 `SKILL.md` + `name`/`description` frontmatter，直接复制整个目录：

```bash
# WorkBuddy
git clone https://github.com/guomu520/universal-learning-mentor.git \
  ~/.workbuddy/skills/universal-learning-mentor

# Claude Code
git clone https://github.com/guomu520/universal-learning-mentor.git \
  ~/.claude/skills/universal-learning-mentor

# Codex（注意：不是 ~/.codex/skills/）
git clone https://github.com/guomu520/universal-learning-mentor.git \
  ~/.agents/skills/universal-learning-mentor
```

三个平台都建议补上初始状态文件，让第零步有东西可读：

```bash
cp <技能目录>/state/日课卡.example.md <技能目录>/state/日课卡.md
```

Codex 也支持仓库级 `.agents/skills/`，以及在 `~/.codex/config.toml` 里用 `[[skills.config]]` 控制启用；Claude Code 可用 `/universal-learning-mentor` 显式召唤，也能靠 `description` 自动命中。

### Cursor

```bash
mkdir -p .cursor/rules
cp dist/cursor-rule.mdc .cursor/rules/universal-learning-mentor.mdc
```

`.mdc` 的 frontmatter 是 `description` + `alwaysApply: false`，即 **Apply Intelligently**：Cursor 只在判断相关时才加载，不会每次对话都占上下文。也可以把 `dist/AGENTS.md` 放到项目根目录，让 20+ 种工具共用。

### 豆包（重点：两个设置别漏）

1. 豆包 App / 网页 → 左侧「更多」→「智能体」→「+ 创建 AI 智能体」
2. 名称随便填；「**设定描述**」栏整段粘贴 `dist/prompt-mini.md`（**文件里没有标题和说明，整段就是协议正文**，599 字（按落盘真实字符数，含换行标点），符合 300–600 字建议区间）
3. 「开场白」栏填：`你好，我是你的学习教练。不买课、不囤资料，一次只做一件事。你每天重复做、最烦的那件事是什么？`
4. ⚠️ **把「最大输出字数」从默认 500 调到 1000 以上**——处方 + 启动模板 + 日课卡合计会超过 500 字，不调会被截断，减法声明和日课卡会丢
5. 联网搜索可关掉：这个教练不需要检索，联网反而容易引回一堆教程链接

### ChatGPT / Claude 网页 / Kimi / 文心 / Coze

把 `dist/prompt-plain.md` 整段粘到对应位置：

- ChatGPT：GPTs → Instructions，或「设置 → 个性化 → 自定义指令」
- Claude：Project → Custom instructions
- Kimi / 文心 / 通义：自定义人设 / 智能体设定
- Coze：智能体 →「人设与回复逻辑」

开场白发一句「我想学 AI，但不知道从哪开始」即可。

---

## 粘完怎么确认生效

发这一句，看首轮回复：

> 我想学 AI，但不知道从哪开始，能不能推荐点课程？

**合格**：一句短共情 + **只有一个问题**（问的是"你每天最烦的一件事"）+ 末尾「信息 n/3」+ **没有任何工具/课程/链接**。

**不合格**：直接甩课程清单、列 3 个工具、解释大模型原理、一次问两个问题 —— 说明提示词没被完整加载，或平台把它压缩了。此时换 `prompt-mini.md` 再试。

复盘时把教练给的日课卡**原样贴回来**即可，这是纯 Prompt 平台唯一需要用户手动做的一件事。

---

## 重新生成

改动 `SKILL.md` 后不要手改 `dist/`，跑：

```bash
python3 scripts/build_dist.py   # 重新生成 4 个适配文件，精简版超 600 字会直接报错
python3 scripts/check_skill.py  # 验收协议与 dist 一致性
```

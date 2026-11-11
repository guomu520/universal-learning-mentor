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
| **豆包** | 纯 Prompt 智能体 | **首选 `dist/prompt-plain.md`**；确有短字数限制才用 `dist/prompt-mini.md`（1165 字） | ⚠️ 文本回钩，带回归信号才复盘 |
| **ChatGPT / GPTs** | 纯 Prompt | `dist/prompt-plain.md` | ⚠️ 文本回钩，带回归信号才复盘 |
| **Claude 网页 / Kimi / 文心 / 通义** | 纯 Prompt | `dist/prompt-plain.md` | ⚠️ 文本回钩，带回归信号才复盘 |
| **Coze / 扣子** | 纯 Prompt 智能体 | `dist/prompt-plain.md`（或 mini，若字数受限） | ⚠️ 文本回钩，带回归信号才复盘 |

> **状态闭环**那一列的差别只有一处：**谁记日课卡**。协议、四重认知流水线、全部护栏在所有平台完全一致。
> v4.1 起纯 Prompt 平台**不再要求用户保存或贴回日课卡**：回钩自带任务上下文；**只有首句带回归信号（做了 / 没做 / 我断了 / 上次那个）才进复盘，新用户第一句话一律走开场白**。代价是断更日期只能靠用户自述，宿主版仍以日期为准。

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
2. 名称随便填；「**设定描述**」栏整段粘贴 **`dist/prompt-plain.md`**（完整版，约 3200 字）。
   - 查证结论：豆包官方只限制名称 12 字、「最大输出字数」默认 500 可调 2000；网传「设定描述 300–600 字」是社区**建议**不是硬上限。
   - 独立双盲评测证明 600 字精简版会丢掉规则优先级仲裁、焦虑/跑题分支区分、介质兜底、结业重启暗号，行为会变形。**v4.x 把精简版扩到 1165 字**，但只在你的账号确实放不下完整版时才用 `dist/prompt-mini.md`（文件里没有标题和说明，整段就是协议正文）。
3. 「开场白」栏填：`我是学习教练。不囤资料，一次只做一件事。先不用想清楚——你每天重复做、最烦的那件事是什么？`
4. ⚠️ **把「最大输出字数」从默认 500 调到 1000 以上**——处方 + 贴给 App 的话 + 照着点 + 日课卡合计会超过 500 字，不调会被截断，减法声明和日课卡会丢
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

**合格**：一句短共情（≤12 字）+ **只有一个问题**（问的是"你每天最烦的一件事"）+ **不出现任何进度步数** + **没有任何工具/课程/链接**。

**不合格**：直接甩课程清单、列 3 个工具、解释大模型原理、一次问两个问题、或冒出「信息 0/3」—— 说明提示词没被完整加载，或平台加载的是旧版。此时重新粘贴 `prompt-plain.md` 并确认保存生效。

**复盘不需要贴卡**：隔天发一句带回归信号的话（「周报助理，做了」「我断了」），教练会先用那几个字复述上次动作再判断；**首次对话仍走开场白**，不会被误判成回来交作业。v4.1 起不要求用户保存或贴回整张卡。

处方里还应出现两块可复制内容：贴给 App 的话（示例填好、无占位符）和「照着点」操作步；日课卡第三行是「明天这个点：发『周报助理，做了』或『我断了』」。缺任一块说明提示词被压缩了。

---

## 重新生成

改动 `SKILL.md` 后不要手改 `dist/`，跑：

```bash
python3 scripts/build_dist.py   # 重新生成 4 个适配文件，精简版超 1300 字会直接报错
python3 scripts/check_skill.py  # 验收协议与 dist 一致性
```

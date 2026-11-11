#!/usr/bin/env python3
"""
从 SKILL.md（单一数据源）生成各平台的适配文件。

为什么需要它：SKILL.md 是给"能读写文件的宿主"用的，含 YAML frontmatter、
文件读写指令、内部校准锚点。整段粘到豆包/ChatGPT 的自定义指令里会是噪音，
而独立手写一份又会和主协议逐渐漂移。这里做可重复、可校验的自动生成。

    python3 scripts/build_dist.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, 'SKILL.md')
DIST = os.path.join(ROOT, 'dist')

# ---- 宿主专属段落剥离后需要替换的文案（纯提示词平台版本）----
REPLACEMENTS = [
    (
        '【第零步 · 每次对话必做】先按「宿主能力层」判断能否读写状态文件。能，则**先读 `state/日课卡.md`**：有未结业的卡就直接进入阶段四复盘，跳过开场白。不读状态就开口，等于没在监督。\n'
        '【流水线】读状态 → 摸底 → 处方（诊断+规划，一次给完）→ 日课卡 → 复盘循环 → 结业',
        '【第零步 · 每次对话必做】若用户贴回了日课卡，直接进阶段四复盘，跳过开场白；否则走开场白。\n'
        '【流水线】看有无日课卡 → 摸底 → 处方（诊断+规划，一次给完）→ 日课卡 → 复盘循环 → 结业',
    ),
    ('## 日课卡 + 宿主能力层（让复盘真的发生）',
     '## 日课卡（处方末尾必须附上）'),
    ('**输出给用户的 3 行卡**（两种模式都要给）：',
     '处方末尾附上这张 3 行卡：'),
    ('**为什么必须有**：对话会换设备、清上下文、隔很久才回来。没有状态，复盘就无从盘起——这才是「计划总是半途而废」的真正断点，不是意志力问题。',
     '**为什么必须有**：对话会换设备、清上下文、隔很久才回来。没有这张卡，复盘就无从盘起——这才是「计划总是半途而废」的真正断点，不是意志力问题。请让用户把这张卡复制保存，下次直接贴回来续上。'),
    ('1. 每次对话第一句先盘：「做了没？把结果贴给我。」**状态文件里有卡就以其为准，没有才等用户贴卡**。不看情绪，只看交付物。',
     '1. 每次对话第一句先盘：「做了没？把结果贴给我。」**以用户贴回的日课卡为准**。不看情绪，只看交付物。'),
    ('（用户开场若已点名某项技能，直接从这句问起，不要再问「你想学什么」；若状态文件里已有未结业的卡，不要输出开场白，直接复盘。）',
     '（用户开场若已点名某项技能，直接从这句问起，不要再问「你想学什么」；若用户贴回了日课卡，不要输出开场白，直接复盘。）'),
]

PLAIN_HEADER = '''# 通用反焦虑学习教练 · 纯提示词版

> 把下面**全部内容**复制到目标平台的「系统提示词 / 自定义指令 / 人设与回复逻辑」。
> 本文件由 `scripts/build_dist.py` 从 `SKILL.md` 自动生成，**请勿手改**。
> 纯网页平台无法读写文件，复盘靠用户把日课卡贴回来续上；协议与护栏和原生版完全一致。
> 能读写文件的宿主请直接安装 `SKILL.md`，闭环更完整。

---

'''

CURSOR_FRONTMATTER = '''---
description: "反焦虑学习教练。当用户说'想学 XX 不知道从哪开始'、'怕不学 AI 被淘汰'、'买了课一直没看'、'学习计划半途而废'，或回来做日课复盘时使用。不用于代码任务。"
alwaysApply: false
---

'''

# 豆包智能体「设定描述」建议 300-600 字，这是压缩到该量级的等价版本。
MINI = '''你是「通用学习教练」，服务零基础小白。

【最高优先级】不给路线图、书单、课表；不解释原理和黑话；全篇只提 1 个工具，且必须是用户已装好、免费中文、零下载零注册；不说「坚持」「打基础」；不夸奖；一次只安排一个动作。
【字数】摸底≤80字，处方≤260字，复盘≤120字；模板与日课卡不计入。开头可一句短共情。

【摸底】每次只问一个问题，末尾标「信息 n/3」；收齐目标场景、基础、每日时间。把「我想学 XX」翻译成「你每天重复做、最烦的那件事」。用户说「怕被淘汰」或跑题，别追问，只回：「我们一次只解决一件事。你每天重复做、最烦的那件事是什么？」齐了立刻给处方。

【处方】一次给完，必含：①一句话画像；②≥2 个「绝对不要碰」的陷阱及死因；③只留 1 个学习介质；④减法声明；⑤15 分钟能产出成品的微动作 + 可整段复制的启动模板。禁「第一步第二步」「先准备好再开始」及第二个动作。

【日课卡】必附，请用户保存、下次贴回：
日课卡
- 今天只做：…
- 交付物：…
- 下次回来：把结果原样贴给我

【复盘】第一句只问「做了没？把结果贴给我」。没做/断更：不追问、不提「坚持」，砍到 3 分钟重来，当作第一天。效果差：只改模板一句话。做好了：升到 20 分钟、给新卡。满 3 次结业：「你已经会自己拆动作了，不用再来找我。」

【开场白】「你好，我是你的学习教练。不买课、不囤资料，一次只做一件事。先不用想清楚——你每天重复做、最烦的那件事是什么？」信息 0/3
'''


def cjk_len(s):
    return len(re.sub(r'\s', '', s))


def build_plain(src):
    body = re.sub(r'^---\n.*?\n---\n', '', src, count=1, flags=re.S)
    body, n = re.subn(r'\n?<!-- HOST_ONLY -->.*?<!-- /HOST_ONLY -->\n?', '\n', body, flags=re.S)
    assert n == 1, 'HOST_ONLY 标记未找到或不唯一，SKILL.md 结构可能已变'
    for old, new in REPLACEMENTS:
        assert old in body, '替换目标未命中（协议已改动，请同步更新 build_dist.py）：' + old[:40]
        body = body.replace(old, new)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    body = body.replace('\n## 阶段四：复盘', '\n---\n\n## 阶段四：复盘')
    forbidden = ['HOST_ONLY', 'state/日课卡.md', '宿主能力层', 'agent_created', 'frontmatter']
    for bad in forbidden:
        assert bad not in body, '纯提示词版仍残留宿主专属内容：' + bad
    return body


def main():
    os.makedirs(DIST, exist_ok=True)
    src = open(SKILL, encoding='utf-8').read()
    plain = build_plain(src)

    files = {
        'prompt-plain.md': PLAIN_HEADER + plain,
        # 精简版不放任何文件头：用户整段粘进豆包时，每个字都要花在协议上
        'prompt-mini.md': MINI,
        'cursor-rule.mdc': CURSOR_FRONTMATTER + plain,
        'AGENTS.md': ('# 通用反焦虑学习教练\n\n'
                      '> 由 `scripts/build_dist.py` 生成，请勿手改。放到项目根目录即可被 '
                      'Codex / Cursor / Copilot 等读取。\n\n' + plain),
    }
    for name, content in files.items():
        with open(os.path.join(DIST, name), 'w', encoding='utf-8') as f:
            f.write(content.rstrip() + '\n')
        print('%-22s %5d 字' % (name, cjk_len(content)))

    mini_len = cjk_len(MINI)
    if mini_len > 600:
        print('\n[FAIL] 精简版 %d 字，超过豆包建议的 600 字上限' % mini_len)
        sys.exit(1)
    print('\n构建完成，精简版 %d 字 ≤ 600。' % mini_len)


if __name__ == '__main__':
    main()

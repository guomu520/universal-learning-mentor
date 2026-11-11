#!/usr/bin/env python3
"""
universal-learning-mentor 验收器。

把"规则写得对不对"和"输出合不合规"变成可复现的检查，而不是靠人读文档判断。

用法:
    python3 scripts/check_skill.py                 # 全部检查
    python3 scripts/check_skill.py --prompt-only  # 只查 SKILL.md 结构
    python3 scripts/check_skill.py --transcript-only
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, 'SKILL.md')
TRANSCRIPT = os.path.join(ROOT, 'tests', 'sample-transcript.md')

results = []


def check(label, ok, detail=''):
    results.append((label, bool(ok), detail))


def visible_len(s):
    return len(re.sub(r'\s', '', s))


# ---------- 1. SKILL.md 结构检查 ----------
def check_prompt():
    text = open(SKILL, encoding='utf-8').read()
    fm = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    check('frontmatter 存在', bool(fm))
    if fm:
        head = fm.group(1)
        check('name 字段', re.search(r'^name:\s*\S+', head, re.M))
        check('description 字段', re.search(r'^description:', head, re.M))
        check('agent_created: true（宿主可管理）', 'agent_created: true' in head)
        check('version 字段', re.search(r'^version:\s*\d', head, re.M))
        check('description 含触发式措辞', 'This skill should be used when' in head)
        check('description 含中文触发例句', '想学' in head and '半途而废' in head)

    sections = ['系统总则', '全局禁止清单', '阶段一：摸底', '阶段二+三：处方',
                '日课卡', '宿主能力层', '阶段四：复盘', '处方锚点', '初始化']
    for s in sections:
        check('章节存在 · ' + s, s in text)

    rules = {
        '规则优先级': '规则优先级',
        '字数预算': '字数预算',
        '第零步读状态': '第零步',
        '快速通道': '快速通道',
        '焦虑分支': '焦虑分支',
        '兜底机制': '【兜底】',
        '零安装硬约束': '零注册零下载',
        '减法声明': '减法声明',
        '启动模板': '启动模板',
        '可见成品': '看得见的成品',
        '日课卡自动写入': '不要求用户保存任何东西',
        '断更按日期': '断更靠日期判断',
        '结业机制': '结业',
        '隐私约定': '不写姓名',
        '纯网页降级': '完全跳过本节',
        '状态字段模板': '日课卡.example.md',
    }
    for label, needle in rules.items():
        check('硬规则 · ' + label, needle in text)

    # 规则冲突回归：这些是历史版本里出现过的自相矛盾，必须不再出现
    conflicts = {
        '不再有 150 字总限制': '总字数不超过 150 字',
        '问号规则已加边界': '你的回复必须以问号结尾',
        '不让用户自己保存卡': '让用户复制保存',
        '开场白不再一次两问': '你最近最想学的一项技能是什么？它主要是',
        '不再依赖用户主动想起': '不依赖小白主动想起你',
    }
    for label, bad in conflicts.items():
        check('无冲突回归 · ' + label, bad not in text)


# ---------- 2. 真实输出验收 ----------
def parse_transcript():
    if not os.path.exists(TRANSCRIPT):
        return []
    raw = open(TRANSCRIPT, encoding='utf-8').read()
    pattern = r'###\s*T(\d+)\s*\|\s*stage=(\S+)[^\n]*\n+```text\n(.*?)\n```'
    return [(m.group(1), m.group(2), m.group(3)) for m in
            re.finditer(pattern, raw, re.S)]


BANNED = ['第一步', '第二步', '先准备好', '学习路线图', '每天坚持', '养成习惯',
          '打好基础', '为什么没坚持', 'CO-STAR']


def strip_blocks(s):
    """去掉启动模板与日课卡（不计入字数预算）。"""
    s = re.sub(r'```.*?```', '', s, flags=re.S)
    s = re.sub(r'>.*?(?=\n\n|\Z)', '', s, flags=re.S)
    s = re.sub(r'^- (今天只做|交付物|下次回来)：.*$', '', s, flags=re.M)
    return s


def check_transcript():
    turns = parse_transcript()
    check('transcript 可解析且覆盖 3 个阶段', len(turns) >= 4,
          '解析到 %d 段' % len(turns))
    for tid, stage, out in turns:
        body = strip_blocks(out)
        n = visible_len(body)
        for bad in BANNED:
            check('T%s 无禁用表达 · %s' % (tid, bad), bad not in out)

        if stage == '摸底':
            check('T%s 只问一个问题' % tid, out.count('？') == 1,
                  '问号数=%d' % out.count('？'))
            check('T%s 有进度标记' % tid, bool(re.search(r'信息 \d/3', out)))
            check('T%s 字数 ≤80' % tid, n <= 80, '实际 %d 字' % n)
            check('T%s 不推荐工具' % tid,
                  not re.search(r'豆包|Kimi|ChatGPT|Python|课程', out))
        elif stage == '处方':
            check('T%s 有画像' % tid, '观察' in out or '属于' in out)
            check('T%s 至少 2 个陷阱' % tid,
                  len(re.findall(r'[①②]|不要碰', out)) >= 2)
            check('T%s 有减法声明' % tid, '不用准备' in out or '为什么' in out)
            check('T%s 有可复制启动模板' % tid, '```' in out or '>' in out)
            check('T%s 有日课卡' % tid, '日课卡' in out)
            check('T%s 只提 1 个工具' % tid,
                  len(set(re.findall(r'豆包|Kimi|ChatGPT|讯飞|微信', out))) <= 1)
            check('T%s 叙述字数 ≤260' % tid, n <= 260, '实际 %d 字' % n)
        elif stage == '复盘':
            check('T%s 字数 ≤120' % tid, n <= 120, '实际 %d 字' % n)
            check('T%s 不追问原因' % tid, '为什么' not in out)
            check('T%s 给的是动作' % tid, len(out.strip()) > 5)


def main():
    args = sys.argv[1:]
    if '--transcript-only' not in args:
        check_prompt()
    if '--prompt-only' not in args:
        check_transcript()

    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(l, d) for l, ok, d in results if not ok]
    for label, ok, detail in results:
        flag = 'PASS' if ok else 'FAIL'
        suffix = ('  (%s)' % detail) if detail else ''
        print('[%s] %s%s' % (flag, label, suffix))
    print('\n%d/%d 通过' % (passed, len(results)))
    if failed:
        print('失败项：')
        for l, d in failed:
            print('  - %s %s' % (l, d))
        sys.exit(1)
    print('验收通过。')


if __name__ == '__main__':
    main()

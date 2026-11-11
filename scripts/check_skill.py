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
        '不显示步数': '不显示任何进度数字或步数标记',
        '照着点操作步': '照着点',
        '围栏才不计字数': '只有用 `>` 引用块',
        '闭环锚到任意一句话': '回钩锚在',
        '结业判据改为自主重开': '断更后自己回来',
        '不预判用户失败': '不预判用户会失败',
        '禁占位符': '不出现任何占位符',
        '首次回归区分': '只有首句带回归信号',
        '介质死锁兜底': '若那个 App 里没有能对话的 AI 入口',
        '纯网页不判结业': '纯网页版不判结业',
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
        '不再要求用户保存贴回': '请让用户把这张卡复制保存',
        '不再强制显示进度标记': '每轮末尾标「信息 n/3」',
        '结业不再关门': '不用再来找我',
        '不再预判用户放弃': '下载注册超过 2 分钟你就会放弃',
        '不再把首次对话当回归': '用户发来的任何内容都视为回来复盘',
        '不再要求贴回结果': '把结果贴给我',
    }
    for label, bad in conflicts.items():
        check('无冲突回归 · ' + label, bad not in text)


# ---------- 2. 真实输出验收 ----------
def parse_transcript(path=None):
    p = path or TRANSCRIPT
    if not os.path.exists(p):
        return []
    raw = open(p, encoding='utf-8').read()
    pattern = r'###\s*T(\d+)\s*\|\s*stage=(\S+)[^\n]*\n+```text\n(.*?)\n```'
    return [(m.group(1), m.group(2), m.group(3)) for m in
            re.finditer(pattern, raw, re.S)]


BANNED = ['第一步', '第二步', '先准备好', '学习路线图', '每天坚持', '养成习惯',
          '打好基础', '为什么没坚持', 'CO-STAR']


def strip_blocks(s):
    """去掉启动模板与日课卡（不计入字数预算）。"""
    s = re.sub(r'```.*?```', '', s, flags=re.S)
    s = re.sub(r'>.*?(?=\n\n|\Z)', '', s, flags=re.S)
    s = re.sub(r'^- (今天只做|做出来的是|明天这个点|下次回来|交付物)：.*$', '', s, flags=re.M)
    return s


def check_transcript(path=None):
    turns = parse_transcript(path)
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
            check('T%s 不显示步数标记' % tid, not re.search(r'信息 \d/3', out))
            check('T%s 字数 ≤80' % tid, n <= 80, '实际 %d 字' % n)
            check('T%s 不推荐工具' % tid,
                  not re.search(r'豆包|Kimi|ChatGPT|Python|课程', out))
        elif stage == '处方':
            check('T%s 有画像' % tid,
                  any(k in out for k in ['观察', '属于', '画像', '每天只有', '只想少烦']))
            check('T%s 至少 2 个陷阱' % tid,
                  len(re.findall(r'[①②]|不要碰|^\s*-\s', out, re.M)) >= 2)
            check('T%s 有减法声明' % tid,
                  any(k in out for k in ['不用准备', '为什么', '减法声明', '今天不装', '现在用的就够']))
            check('T%s 有可复制启动模板' % tid,
                  any(k in out for k in ['```', '>', '贴给', '照着点']))
            check('T%s 有日课卡' % tid, '日课卡' in out)
            check('T%s 只提 1 个工具' % tid,
                  len(set(re.findall(r'豆包|Kimi|ChatGPT|讯飞|微信', out))) <= 1)
            check('T%s 叙述字数 ≤260' % tid, n <= 260, '实际 %d 字' % n)
            check('T%s 无占位符泄漏' % tid,
                  not re.search(r'<[^>]{1,20}>|\[[^\]]{1,20}\]|…', out))
            check('T%s 有照着点操作步' % tid, '照着点' in out)
            check('T%s 日课卡有回钩' % tid, '明天这个点' in out)
        elif stage == '复盘':
            if '你已经会自己' in out:
                check('T%s 结业不关门（给重启暗号）' % tid, '我断了' in out)
            check('T%s 字数 ≤120' % tid, n <= 120, '实际 %d 字' % n)
            check('T%s 不追问原因' % tid, '为什么' not in out)
            check('T%s 给的是动作' % tid, len(out.strip()) > 5)


# ---------- 3. 跨平台 dist 一致性 ----------
DIST = os.path.join(ROOT, 'dist')

CORE_RULES = ['全局禁止清单', '阶段一：摸底', '阶段二+三：处方',
              '日课卡', '阶段四：复盘', '初始化',
              '快速通道', '焦虑分支', '减法声明', '启动模板', '结业']

HOST_ONLY_WORDS = ['agent_created', 'state/日课卡.md', '宿主能力层',
                   'HOST_ONLY', '第零步 · 每次对话必做】先按']


def check_dist():
    expected = ['prompt-plain.md', 'prompt-mini.md', 'cursor-rule.mdc',
                'AGENTS.md', 'PLATFORMS.md']
    for name in expected:
        path = os.path.join(DIST, name)
        check('dist 文件存在 · ' + name, os.path.exists(path))
        if not os.path.exists(path):
            return
    plain = open(os.path.join(DIST, 'prompt-plain.md'), encoding='utf-8').read()
    mini = open(os.path.join(DIST, 'prompt-mini.md'), encoding='utf-8').read()
    cursor = open(os.path.join(DIST, 'cursor-rule.mdc'), encoding='utf-8').read()
    platforms = open(os.path.join(DIST, 'PLATFORMS.md'), encoding='utf-8').read()

    for label, text in [('prompt-plain', plain), ('cursor-rule', cursor),
                        ('AGENTS', open(os.path.join(DIST, 'AGENTS.md'), encoding='utf-8').read())]:
        for bad in HOST_ONLY_WORDS:
            check('%s 无宿主残留 · %s' % (label, bad), bad not in text)
    for rule in CORE_RULES:
        check('prompt-plain 保留核心规则 · ' + rule, rule in plain)

    check('cursor-rule 有 frontmatter', cursor.startswith('---\n'))
    check('cursor-rule 为 Apply Intelligently', 'alwaysApply: false' in cursor and 'description:' in cursor)
    # 口径必须是「用户整段粘进去的真实字符数」：豆包按框内字符计数，
    # 换行、空格、标点都算。用去空白的 visible_len 会虚低约 37 字，导致实测超限却判通过。
    actual_len = len(mini.strip())
    check('prompt-mini 真实粘贴长度 ≤1300 字', actual_len <= 1300,
          '实际 %d 字（含换行/空格/标点）' % actual_len)
    check('prompt-mini 无文件头（整段即协议）',
          mini.lstrip().startswith('你是「学习教练」'))
    # v3.1 的 600 字版丢掉这些仲裁后行为变形（独立评审 3/10），v4.0 起必须常驻
    for label, needle in {
        '首次回归区分': '回归信号',
        '规则优先级仲裁': '仲裁',
        '焦虑与跑题区分': '不可混用',
        '介质死锁兜底': '当前这个对话',
        '照着点操作步': '照着点',
        '占位符禁令': '禁占位符',
        '回钩自带上下文': '不用保存整张卡',
        '结业重启暗号': '我断了',
        '纯网页不判结业': '纯网页版不判结业',
    }.items():
        check('prompt-mini 补回关键规则 · ' + label, needle in mini)
    check('prompt-mini 日课卡无省略号占位符', '- 今天只做：…' not in mini)
    for rule in ['最高优先级', '摸底', '处方', '日课卡', '复盘', '开场白', '结业']:
        check('prompt-mini 保留硬规则 · ' + rule, rule in mini)
    for path in ['~/.agents/skills/', '~/.claude/skills/', '.cursor/rules', '最大输出字数']:
        check('PLATFORMS 含关键指引 · ' + path, path in platforms)
    check('build_dist.py 存在',
          os.path.exists(os.path.join(ROOT, 'scripts', 'build_dist.py')))


# ---------- 4. 演示文档与协议一致性（防止协议升级后 demo 停在旧版） ----------
def check_examples():
    ex_dir = os.path.join(ROOT, 'examples')
    for name in ['demo-ai-learning.md', 'demo-anxiety.md']:
        path = os.path.join(ex_dir, name)
        check('演示存在 · ' + name, os.path.exists(path))
        if not os.path.exists(path):
            continue
        text = open(path, encoding='utf-8').read()
        check(name + ' 不显示步数标记', not re.search(r'信息 \d/3', text))
        check(name + ' 处方附日课卡', '日课卡' in text)
        check(name + ' 有可复制启动模板', '内容如下' in text or '发给' in text)
        check(name + ' 有结业', '结业' in text or '你已经会自己' in text)
        check(name + ' 日课卡有回钩', '明天这个点' in text)
        check(name + ' 有照着点操作步', '照着点' in text)
        check(name + ' 无黑话「交付物」', '交付物' not in text)
        check(name + ' 结业不关门', '不用再来找我' not in text)
        for bad in ['遇到卡壳是好事', '或「Kimi」', '第一步、第二步',
                    '日课卡照旧', '日课卡不变', '信息 0/3', '发我一个字']:
            check(name + ' 无旧协议残留 · ' + bad, bad not in text)

        # 一次一问：每段教练发言问号 ≤1（排除引用块、代码块、注释）
        turns = re.findall(r'\*\*AI 教练\*\*(.*?)(?=\n\*\*|\n---|\Z)', text, re.S)
        check(name + ' 可解析出教练发言', len(turns) >= 4, '实际 %d 段' % len(turns))
        for i, seg in enumerate(turns, 1):
            body, in_code = [], False
            for line in seg.splitlines():
                if line.strip().startswith('```'):
                    in_code = not in_code
                    continue
                if in_code or line.lstrip().startswith(('>', '注：')):
                    continue
                body.append(line)
            n = '\n'.join(body).count('？')
            check('%s 教练第%d轮 ≤1 个问号' % (name, i), n <= 1, '实际 %d 个' % n)


def main():
    args = sys.argv[1:]
    tpath = next((a.split('=', 1)[1] for a in args
                  if a.startswith('--transcript=')), None)
    if '--transcript-only' not in args:
        check_prompt()
        check_dist()
        check_examples()
    if '--prompt-only' not in args:
        check_transcript(tpath)

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

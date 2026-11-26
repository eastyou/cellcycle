"""练习纸与图解页的题目生成与 HTML 渲染（字符串拼接 + html.escape）。"""

import html
import math
import random
from typing import Dict, List, NamedTuple, Sequence

from .core import (
    STAGE_NAMES,
    cell_count,
    check_question_count,
    check_seed,
    mitosis_table,
    stage_durations,
    stage_percentages,
    total_time,
)

QUESTION_KINDS = ("细胞数", "周期时间", "各期计算", "染色体数")

STAGE_COLORS = {
    "G1": "#2563eb",
    "S": "#0ea5e9",
    "G2": "#16a34a",
    "M": "#ea580c",
}

STAGE_LABELS = {
    "G1": "G1 期（DNA 复制前准备）",
    "S": "S 期（DNA 复制）",
    "G2": "G2 期（复制后准备）",
    "M": "M 期（分裂期）",
}


class Question(NamedTuple):
    """一道练习题。"""

    kind: str
    prompt: str
    answer: str
    steps: str


def _fmt1(value: float) -> str:
    return "%.1f" % value


def _make_cell_question(rng: random.Random) -> Question:
    start = rng.randint(1, 100)
    divisions = rng.randint(1, 10)
    total = cell_count(start, divisions)
    prompt = "%d 个细胞经过 %d 次有丝分裂后，细胞总数是多少个？" % (start, divisions)
    answer = "%d 个" % total
    steps = "每个细胞每分裂一次变成 2 个，总数 = %d × 2^%d = %d 个。" % (
        start,
        divisions,
        total,
    )
    return Question("细胞数", prompt, answer, steps)


def _make_time_question(rng: random.Random) -> Question:
    cycle = rng.choice([8, 10, 12, 15, 16, 18, 20, 24])
    divisions = rng.randint(1, 12)
    hours = total_time(float(cycle), divisions)
    prompt = "某细胞的一个细胞周期约为 %d 小时，完成 %d 次分裂需要多少小时？" % (
        cycle,
        divisions,
    )
    answer = "%s 小时" % _fmt1(hours)
    steps = "所需时间 = 细胞周期 × 分裂次数 = %d 小时 × %d = %s 小时。" % (
        cycle,
        divisions,
        _fmt1(hours),
    )
    return Question("周期时间", prompt, answer, steps)


def _make_stage_question(rng: random.Random) -> Question:
    cycle = rng.choice([600, 720, 900, 1200, 1440])
    g1 = rng.randint(int(cycle * 0.30), int(cycle * 0.50))
    s_value = rng.randint(int(cycle * 0.10), int(cycle * 0.20))
    g2 = rng.randint(int(cycle * 0.10), int(cycle * 0.20))
    durations = stage_durations(float(cycle), float(g1), float(s_value), float(g2))
    prompt = (
        "某细胞周期总时长为 %d 分钟，其中 G1 期 %d 分钟、S 期 %d 分钟、"
        "G2 期 %d 分钟，则 M 期持续多少分钟？" % (cycle, g1, s_value, g2)
    )
    answer = "%s 分钟" % _fmt1(durations["M"])
    steps = "M 期 = %d - %d - %d - %d = %s 分钟。" % (
        cycle,
        g1,
        s_value,
        g2,
        _fmt1(durations["M"]),
    )
    return Question("各期计算", prompt, answer, steps)


def _make_chromosome_question(rng: random.Random) -> Question:
    diploid = rng.choice([2, 4, 6, 8, 10, 12, 16, 20, 24, 32, 36, 40, 46, 48, 50])
    if rng.randint(0, 1) == 0:
        doubled = diploid * 2
        prompt = (
            "某动物体细胞染色体数为 %d 条，有丝分裂后期每个细胞中有多少条染色体？"
            % diploid
        )
        answer = "%d 条" % doubled
        steps = "后期着丝点分裂，染色体数目暂时加倍：%d × 2 = %d 条。" % (
            diploid,
            doubled,
        )
        return Question("染色体数", prompt, answer, steps)
    doubled = diploid * 2
    prompt = (
        "某动物体细胞染色体数为 %d 条，有丝分裂前期每个细胞中有多少条染色单体？"
        % diploid
    )
    answer = "%d 条" % doubled
    steps = "前期每条染色体含 2 条染色单体：%d × 2 = %d 条。" % (diploid, doubled)
    return Question("染色体数", prompt, answer, steps)


def make_questions(count: int, seed: int) -> List[Question]:
    """按数量与随机种子生成练习题，同一种子结果可复现。"""
    total = check_question_count(count)
    seed_value = check_seed(seed)
    rng = random.Random(seed_value)
    makers = (
        _make_cell_question,
        _make_time_question,
        _make_stage_question,
        _make_chromosome_question,
    )
    questions: List[Question] = []
    for index in range(total):
        maker = makers[index % len(makers)]
        questions.append(maker(rng))
    return questions


def _base_style() -> str:
    return (
        "* { box-sizing: border-box; }\n"
        "body { margin: 0; padding: 24px; background: #eef2f6; color: #1f2937; "
        'font-family: "Songti SC", "SimSun", "Noto Serif CJK SC", serif; '
        "line-height: 1.9; }\n"
        ".page { max-width: 820px; margin: 0 auto; background: #ffffff; "
        "padding: 40px 46px 56px; box-shadow: 0 2px 14px rgba(15, 23, 42, 0.10); }\n"
        "h1 { font-size: 26px; margin: 0 0 6px; letter-spacing: 2px; }\n"
        "h2 { font-size: 20px; margin: 28px 0 12px; "
        "border-left: 4px solid #2563eb; padding-left: 10px; }\n"
        ".meta { margin: 0 0 4px; color: #4b5563; font-size: 14px; }\n"
        ".hint { color: #6b7280; font-size: 13px; margin: 2px 0 6px; }\n"
        "ol.questions { padding-left: 22px; }\n"
        "ol.questions > li { margin-bottom: 18px; page-break-inside: avoid; }\n"
        "p.prompt { margin: 0 0 6px; }\n"
        ".blank { height: 54px; border-bottom: 1px dashed #cbd5e1; }\n"
        ".answer-page { page-break-before: always; }\n"
        ".answer { color: #15803d; font-weight: 700; margin: 0 0 2px; }\n"
        ".steps { color: #4b5563; font-size: 14px; margin: 0 0 14px; }\n"
        "table { width: 100%; border-collapse: collapse; margin: 10px 0 18px; "
        "font-size: 15px; }\n"
        "th, td { border: 1px solid #cbd5e1; padding: 6px 10px; text-align: center; }\n"
        "th { background: #eff6ff; }\n"
        ".cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); "
        "gap: 14px; }\n"
        ".card { border: 1px solid #dbe3ec; border-radius: 10px; padding: 14px 16px; "
        "background: #fbfdff; }\n"
        ".card h3 { margin: 0 0 6px; font-size: 16px; color: #1d4ed8; }\n"
        ".card p { margin: 0; font-size: 14px; color: #374151; }\n"
        ".legend { list-style: none; padding: 0; margin: 12px 0 0; display: flex; "
        "flex-wrap: wrap; gap: 10px 18px; font-size: 14px; }\n"
        ".legend li { display: flex; align-items: center; gap: 6px; }\n"
        ".swatch { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }\n"
        ".figure { display: flex; justify-content: center; margin: 8px 0 4px; }\n"
        "@page { size: A4; margin: 16mm; }\n"
        "@media print {\n"
        "  body { background: #ffffff; padding: 0; }\n"
        "  .page { box-shadow: none; max-width: none; padding: 0; }\n"
        "}\n"
    )


def _page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        "<style>\n%s</style>\n"
        "</head>\n"
        "<body>\n"
        '<main class="page">\n%s</main>\n'
        "</body>\n"
        "</html>\n"
    ) % (html.escape(title), _base_style(), body)


def render_sheet(questions: Sequence[Question], answers: bool = False) -> str:
    """渲染 A4 练习纸 HTML，answers 为真时附加答案页。"""
    if not isinstance(answers, bool):
        raise ValueError("是否附答案必须是布尔值")
    if not isinstance(questions, (list, tuple)):
        raise ValueError("题目列表必须是列表或元组")
    if len(questions) == 0:
        raise ValueError("题目列表不能为空")
    for index, question in enumerate(questions):
        if not isinstance(question, Question):
            raise ValueError("第 %d 道题不是合法的题目对象" % (index + 1))

    items: List[str] = []
    for question in questions:
        items.append(
            '<li><p class="prompt">%s</p>'
            '<p class="hint">提示：写出计算过程（%s）</p>'
            '<div class="blank"></div></li>'
            % (html.escape(question.prompt), html.escape(question.kind))
        )
    body = (
        "<header>\n"
        "<h1>细胞分裂练习纸</h1>\n"
        '<p class="meta">共 %d 题 · 姓名：__________ 班级：__________</p>\n'
        '<p class="meta">要求：写出必要的计算过程，结果保留一位小数。</p>\n'
        "</header>\n"
        '<h2>练习题</h2>\n'
        '<ol class="questions">\n%s\n</ol>\n'
    ) % (len(questions), "\n".join(items))

    if answers:
        answer_items: List[str] = []
        for question in questions:
            answer_items.append(
                "<li><p class=\"answer\">%s</p><p class=\"steps\">%s</p></li>"
                % (html.escape(question.answer), html.escape(question.steps))
            )
        body += (
            '<section class="answer-page">\n'
            "<h2>参考答案</h2>\n"
            '<ol class="questions">\n%s\n</ol>\n'
            "</section>\n"
        ) % "\n".join(answer_items)

    return _page("细胞分裂练习纸", body)


def _cycle_svg(durations: Dict[str, float]) -> str:
    total = 0.0
    for label in STAGE_NAMES:
        total += durations[label]
    radius = 80.0
    circumference = 2.0 * math.pi * radius
    parts: List[str] = [
        '<svg viewBox="0 0 220 220" width="240" height="240" role="img" '
        'aria-label="细胞周期各时期占比示意">',
        '<circle cx="110" cy="110" r="80" fill="none" stroke="#e2e8f0" stroke-width="24"/>',
    ]
    offset = 0.0
    for label in STAGE_NAMES:
        length = circumference * (durations[label] / total)
        gap = circumference - length
        parts.append(
            '<circle cx="110" cy="110" r="80" fill="none" stroke="%s" '
            'stroke-width="24" stroke-dasharray="%.2f %.2f" '
            'stroke-dashoffset="%.2f" transform="rotate(-90 110 110)"/>'
            % (STAGE_COLORS[label], length, gap, -offset)
        )
        offset += length
    parts.append(
        '<text x="110" y="106" text-anchor="middle" font-size="15" fill="#1f2937">'
        "细胞周期</text>"
    )
    parts.append(
        '<text x="110" y="128" text-anchor="middle" font-size="13" fill="#4b5563">'
        "四期循环</text>"
    )
    parts.append("</svg>")
    return "".join(parts)


def render_demo() -> str:
    """渲染细胞周期图解与概念卡片页。"""
    durations = stage_durations(1200.0, 600.0, 300.0, 240.0)
    percentages = stage_percentages(durations)
    legend: List[str] = []
    for label in STAGE_NAMES:
        legend.append(
            '<li><span class="swatch" style="background:%s"></span>%s：%s 分钟（%s%%）</li>'
            % (
                STAGE_COLORS[label],
                STAGE_LABELS[label],
                _fmt1(durations[label]),
                _fmt1(percentages[label]),
            )
        )
    rows: List[str] = []
    for name, chrom, chromatid, dna in mitosis_table(46):
        rows.append(
            "<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>"
            % (html.escape(name), chrom, chromatid, dna)
        )
    body = (
        "<header>\n"
        "<h1>细胞周期与有丝分裂</h1>\n"
        '<p class="meta">一个细胞周期依次经过 G1 期、S 期、G2 期和 M 期，'
        "其中 G1、S、G2 合称间期。</p>\n"
        "</header>\n"
        '<h2>细胞周期图解</h2>\n'
        '<div class="figure">%s</div>\n'
        '<ul class="legend">%s</ul>\n'
        '<h2>核心概念</h2>\n'
        '<div class="cards">\n'
        '<div class="card"><h3>细胞周期</h3><p>连续分裂的细胞，从一次分裂完成时开始，'
        "到下一次分裂完成时为止。</p></div>\n"
        '<div class="card"><h3>间期</h3><p>完成 DNA 复制和有关蛋白质的合成，'
        "细胞有适度生长，染色体数目不变。</p></div>\n"
        '<div class="card"><h3>分裂期</h3><p>前期核膜核仁消失、出现染色体；中期着丝点排列在'
        "赤道板上；后期着丝点分裂、染色体移向两极；末期形成两个子细胞。</p></div>\n"
        '<div class="card"><h3>数目关系</h3><p>染色体数 = 着丝点数；有染色单体时，'
        "染色单体数 = DNA 分子数 = 2 × 染色体数。</p></div>\n"
        "</div>\n"
        '<h2>人体细胞（2n = 46）各时期数目</h2>\n'
        "<table>\n"
        "<thead><tr><th>时期</th><th>染色体数</th><th>染色单体数</th>"
        "<th>DNA 分子数</th></tr></thead>\n"
        "<tbody>\n%s\n</tbody>\n"
        "</table>\n"
        '<p class="hint">表中数值均为每个细胞的数目；末期按每个子细胞计。</p>\n'
        '<h2>计算示例</h2>\n'
        '<div class="cards">\n'
        '<div class="card"><h3>细胞数</h3><p>1 个细胞分裂 5 次：1 × 2^5 = 32 个。</p></div>\n'
        '<div class="card"><h3>周期时间</h3><p>周期 20 小时、分裂 4 次：'
        "20 × 4 = 80 小时。</p></div>\n"
        '<div class="card"><h3>M 期时长</h3><p>总时长 1200 分钟，G1 600、S 300、'
        "G2 240：M = 1200 - 600 - 300 - 240 = 60 分钟。</p></div>\n"
        "</div>\n"
    ) % (_cycle_svg(durations), "\n".join(legend), "\n".join(rows))
    return _page("细胞周期图解", body)

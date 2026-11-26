"""cellcycle 命令行入口。"""

import argparse
import sys
from typing import List, Optional, Sequence

from . import __version__
from .core import (
    cell_count,
    mitosis_table,
    parse_float_text,
    parse_int_text,
    stage_durations,
    stage_percentages,
    total_time,
)
from .sheet import make_questions, render_demo, render_sheet


def _ensure_utf8_console() -> None:
    """尽量把标准输出改为 UTF-8，失败时忽略。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            continue


def build_parser() -> argparse.ArgumentParser:
    """构造命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="cellcycle",
        description="初中生物细胞分裂教学工具：细胞数、周期时间、各期时长与染色体数目表。",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    subparsers = parser.add_subparsers(dest="command", metavar="命令")
    subparsers.required = True

    count_parser = subparsers.add_parser("count", help="计算分裂后的细胞数")
    count_parser.add_argument("--start", default="1", help="起始细胞数，1..1000，默认 1")
    count_parser.add_argument(
        "--divisions", default="5", help="分裂次数，0..30，默认 5"
    )

    time_parser = subparsers.add_parser("time", help="计算完成分裂所需时间")
    time_parser.add_argument(
        "--cycle", default="20", help="每个细胞周期的小时数，需大于 0，默认 20"
    )
    time_parser.add_argument(
        "--divisions", default="4", help="分裂次数，0..30，默认 4"
    )

    stages_parser = subparsers.add_parser("stages", help="计算各期时长与占比")
    stages_parser.add_argument(
        "--cycle", default="1200", help="细胞周期总时长（分钟），需大于 0，默认 1200"
    )
    stages_parser.add_argument("--g1", default="600", help="G1 期时长（分钟），默认 600")
    stages_parser.add_argument("--s", default="300", help="S 期时长（分钟），默认 300")
    stages_parser.add_argument("--g2", default="240", help="G2 期时长（分钟），默认 240")

    chromosomes_parser = subparsers.add_parser(
        "chromosomes", help="输出各时期染色体、染色单体与 DNA 数目表"
    )
    chromosomes_parser.add_argument(
        "--diploid", default="46", help="二倍体染色体数，2..200 的偶数，默认 46"
    )

    sheet_parser = subparsers.add_parser("sheet", help="生成 A4 练习纸")
    sheet_parser.add_argument(
        "--count", default="8", help="题目数量，1..50，默认 8"
    )
    sheet_parser.add_argument("--seed", default="1", help="随机种子，默认 1")
    sheet_parser.add_argument(
        "-o", "--output", required=True, help="输出 HTML 文件路径"
    )
    sheet_parser.add_argument(
        "--answers", action="store_true", help="附加参考答案页"
    )

    demo_parser = subparsers.add_parser("demo", help="生成细胞周期图解页")
    demo_parser.add_argument(
        "-o", "--output", required=True, help="输出 HTML 文件路径"
    )
    return parser


def _write_text(path: str, content: str) -> None:
    """以 UTF-8 写入文本，失败时抛出中文 ValueError。"""
    if not isinstance(path, str) or not path.strip():
        raise ValueError("输出路径不能为空")
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except OSError as exc:
        raise ValueError("写入文件失败：%s" % exc) from exc


def _run_count(args: argparse.Namespace) -> int:
    start = parse_int_text(str(args.start), "起始细胞数")
    divisions = parse_int_text(str(args.divisions), "分裂次数")
    total = cell_count(start, divisions)
    print("起始细胞数：%d" % start)
    print("有丝分裂次数：%d" % divisions)
    print("细胞总数：%d" % total)
    return 0


def _run_time(args: argparse.Namespace) -> int:
    cycle = parse_float_text(str(args.cycle), "细胞周期")
    divisions = parse_int_text(str(args.divisions), "分裂次数")
    hours = total_time(cycle, divisions)
    print("细胞周期：%s 小时" % ("%.1f" % cycle))
    print("有丝分裂次数：%d" % divisions)
    print("所需总时间：%s 小时" % ("%.1f" % hours))
    return 0


def _run_stages(args: argparse.Namespace) -> int:
    cycle = parse_float_text(str(args.cycle), "细胞周期总时长")
    g1 = parse_float_text(str(args.g1), "G1 期时长")
    s_value = parse_float_text(str(args.s), "S 期时长")
    g2 = parse_float_text(str(args.g2), "G2 期时长")
    durations = stage_durations(cycle, g1, s_value, g2)
    percentages = stage_percentages(durations)
    print("细胞周期总时长：%s 分钟" % ("%.1f" % cycle))
    for label in ("G1", "S", "G2", "M"):
        print(
            "%s 期：%s 分钟（%s%%）"
            % (label, "%.1f" % durations[label], "%.1f" % percentages[label])
        )
    return 0


def _run_chromosomes(args: argparse.Namespace) -> int:
    diploid = parse_int_text(str(args.diploid), "二倍体染色体数")
    rows = mitosis_table(diploid)
    print("二倍体染色体数：%d（2n）" % diploid)
    lines: List[str] = [
        "| 时期 | 染色体数 | 染色单体数 | DNA 分子数 |",
        "| --- | --- | --- | --- |",
    ]
    for name, chrom, chromatid, dna in rows:
        lines.append("| %s | %d | %d | %d |" % (name, chrom, chromatid, dna))
    print("\n".join(lines))
    print("说明：表中为每个细胞的数目，末期按每个子细胞计，间期取 DNA 复制完成后。")
    return 0


def _run_sheet(args: argparse.Namespace) -> int:
    count = parse_int_text(str(args.count), "题目数量")
    seed = parse_int_text(str(args.seed), "随机种子")
    questions = make_questions(count, seed)
    content = render_sheet(questions, bool(args.answers))
    _write_text(str(args.output), content)
    print("已生成练习纸：%s（共 %d 题）" % (args.output, len(questions)))
    return 0


def _run_demo(args: argparse.Namespace) -> int:
    content = render_demo()
    _write_text(str(args.output), content)
    print("已生成细胞周期图解：%s" % args.output)
    return 0


def _run(args: argparse.Namespace) -> int:
    """按子命令执行，返回退出码。"""
    handlers = {
        "count": _run_count,
        "time": _run_time,
        "stages": _run_stages,
        "chromosomes": _run_chromosomes,
        "sheet": _run_sheet,
        "demo": _run_demo,
    }
    handler = handlers.get(getattr(args, "command", ""))
    if handler is None:
        raise ValueError("未知命令：%s" % getattr(args, "command", ""))
    return handler(args)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主入口：成功返回 0，输入非法或写文件失败返回 2。"""
    _ensure_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2

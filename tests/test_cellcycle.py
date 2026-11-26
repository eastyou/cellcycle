"""cellcycle 单元测试。"""

import contextlib
import io
import tempfile
import unittest
from html.parser import HTMLParser
from typing import List, Optional, Tuple

from cellcycle import (
    Question,
    __version__,
    cell_count,
    make_questions,
    mitosis_table,
    parse_float_text,
    parse_int_text,
    render_demo,
    render_sheet,
    stage_durations,
    stage_percentages,
    total_time,
)
from cellcycle.cli import main
from cellcycle.sheet import QUESTION_KINDS


def run_cli(argv: List[str]) -> Tuple[int, str, str]:
    """执行 main 并捕获标准输出与标准错误。"""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class _TagCollector(HTMLParser):
    """收集 HTML 标签与文本，用于校验页面可被解析。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: List[str] = []
        self.texts: List[str] = []

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        self.tags.append(tag)

    def handle_data(self, data: str) -> None:
        self.texts.append(data)


def parse_html(text: str) -> _TagCollector:
    """解析 HTML 文本，返回收集器。"""
    collector = _TagCollector()
    collector.feed(text)
    collector.close()
    return collector


class TestCellCount(unittest.TestCase):
    def test_one_division(self) -> None:
        self.assertEqual(cell_count(1, 1), 2)

    def test_zero_divisions_keeps_start(self) -> None:
        self.assertEqual(cell_count(7, 0), 7)

    def test_five_divisions(self) -> None:
        self.assertEqual(cell_count(1, 5), 32)

    def test_start_with_multiple_cells(self) -> None:
        self.assertEqual(cell_count(3, 4), 48)

    def test_max_start_and_max_divisions_allowed(self) -> None:
        self.assertEqual(cell_count(1000, 0), 1000)
        self.assertEqual(cell_count(1000, 29), 536870912000)

    def test_result_limit_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(1000, 30)

    def test_start_lower_bound_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(0, 3)

    def test_start_negative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(-5, 3)

    def test_start_upper_bound_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(1001, 3)

    def test_divisions_negative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(1, -1)

    def test_divisions_upper_bound_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(1, 31)

    def test_bool_start_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(True, 2)

    def test_float_start_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count(2.0, 2)

    def test_text_start_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cell_count("2", 2)  # type: ignore[arg-type]


class TestTotalTime(unittest.TestCase):
    def test_basic(self) -> None:
        self.assertEqual(total_time(20.0, 4), 80.0)

    def test_zero_divisions(self) -> None:
        self.assertEqual(total_time(12.5, 0), 0.0)

    def test_int_cycle_accepted(self) -> None:
        self.assertEqual(total_time(10, 3), 30.0)

    def test_zero_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            total_time(0.0, 3)

    def test_negative_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            total_time(-2.0, 3)

    def test_nan_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            total_time(float("nan"), 3)

    def test_inf_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            total_time(float("inf"), 3)

    def test_bool_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            total_time(True, 3)

    def test_divisions_upper_bound_rejected(self) -> None:
        with self.assertRaises(ValueError):
            total_time(20.0, 31)

    def test_result_limit_rejected(self) -> None:
        with self.assertRaises(ValueError):
            total_time(1e11, 30)


class TestStageDurations(unittest.TestCase):
    def setUp(self) -> None:
        self.result = stage_durations(1200.0, 600.0, 300.0, 240.0)

    def test_four_stages(self) -> None:
        self.assertEqual(sorted(self.result.keys()), ["G1", "G2", "M", "S"])

    def test_m_phase_value(self) -> None:
        self.assertAlmostEqual(self.result["M"], 60.0)

    def test_given_values_kept(self) -> None:
        self.assertAlmostEqual(self.result["G1"], 600.0)
        self.assertAlmostEqual(self.result["S"], 300.0)
        self.assertAlmostEqual(self.result["G2"], 240.0)

    def test_sum_equals_total(self) -> None:
        self.assertAlmostEqual(sum(self.result.values()), 1200.0)

    def test_equal_split(self) -> None:
        result = stage_durations(100.0, 10.0, 10.0, 10.0)
        self.assertAlmostEqual(result["M"], 70.0)

    def test_cycle_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(0.0, 10.0, 10.0, 10.0)

    def test_cycle_negative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(-100.0, 10.0, 10.0, 10.0)

    def test_g1_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, 0.0, 10.0, 10.0)

    def test_s_negative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, 10.0, -1.0, 10.0)

    def test_g2_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, 10.0, 10.0, 0.0)

    def test_sum_equal_to_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(90.0, 30.0, 30.0, 30.0)

    def test_sum_greater_than_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, 50.0, 40.0, 30.0)

    def test_stage_larger_than_cycle_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, 150.0, 10.0, 10.0)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, float("nan"), 10.0, 10.0)

    def test_inf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, 10.0, float("inf"), 10.0)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations(100.0, True, 10.0, 10.0)

    def test_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_durations("100", 10.0, 10.0, 10.0)  # type: ignore[arg-type]


class TestStagePercentages(unittest.TestCase):
    def test_basic_percentages(self) -> None:
        durations = stage_durations(1200.0, 600.0, 300.0, 240.0)
        percentages = stage_percentages(durations)
        self.assertAlmostEqual(percentages["G1"], 50.0)
        self.assertAlmostEqual(percentages["S"], 25.0)
        self.assertAlmostEqual(percentages["G2"], 20.0)
        self.assertAlmostEqual(percentages["M"], 5.0)

    def test_percentages_sum_to_hundred(self) -> None:
        percentages = stage_percentages(stage_durations(600.0, 300.0, 150.0, 90.0))
        self.assertAlmostEqual(sum(percentages.values()), 100.0)

    def test_missing_stage_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_percentages({"G1": 10.0, "S": 10.0, "G2": 10.0})

    def test_zero_total_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_percentages({"G1": 0.0, "S": 0.0, "G2": 0.0, "M": 0.0})

    def test_non_dict_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stage_percentages([1, 2, 3, 4])  # type: ignore[arg-type]


class TestMitosisTable(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = mitosis_table(46)

    def test_five_rows(self) -> None:
        self.assertEqual(len(self.rows), 5)

    def test_stage_names(self) -> None:
        self.assertEqual(
            [row[0] for row in self.rows],
            ["间期", "前期", "中期", "后期", "末期"],
        )

    def test_interphase_values(self) -> None:
        self.assertEqual(self.rows[0], ("间期", 46, 92, 92))

    def test_prophase_values(self) -> None:
        self.assertEqual(self.rows[1], ("前期", 46, 92, 92))

    def test_metaphase_values(self) -> None:
        self.assertEqual(self.rows[2], ("中期", 46, 92, 92))

    def test_anaphase_doubles_chromosomes(self) -> None:
        self.assertEqual(self.rows[3], ("后期", 92, 0, 92))

    def test_telophase_values(self) -> None:
        self.assertEqual(self.rows[4], ("末期", 46, 0, 46))

    def test_smallest_diploid(self) -> None:
        rows = mitosis_table(2)
        self.assertEqual(rows[0], ("间期", 2, 4, 4))
        self.assertEqual(rows[3], ("后期", 4, 0, 4))

    def test_odd_diploid_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mitosis_table(47)

    def test_too_small_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mitosis_table(0)

    def test_too_large_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mitosis_table(202)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mitosis_table(True)

    def test_float_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mitosis_table(46.0)  # type: ignore[arg-type]


class TestParseHelpers(unittest.TestCase):
    def test_parse_int_plain(self) -> None:
        self.assertEqual(parse_int_text("12", "次数"), 12)

    def test_parse_int_with_spaces(self) -> None:
        self.assertEqual(parse_int_text("  8  ", "次数"), 8)

    def test_parse_int_negative(self) -> None:
        self.assertEqual(parse_int_text("-3", "次数"), -3)

    def test_parse_int_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_int_text("12.0", "次数")

    def test_parse_int_empty_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_int_text("   ", "次数")

    def test_parse_float_plain(self) -> None:
        self.assertAlmostEqual(parse_float_text("2.5", "周期"), 2.5)

    def test_parse_float_scientific(self) -> None:
        self.assertAlmostEqual(parse_float_text("1e3", "周期"), 1000.0)

    def test_parse_float_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_float_text("nan", "周期")

    def test_parse_float_inf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_float_text("inf", "周期")

    def test_parse_float_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_float_text("abc", "周期")

    def test_parse_float_empty_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_float_text("", "周期")


class TestQuestions(unittest.TestCase):
    def test_count_eight(self) -> None:
        self.assertEqual(len(make_questions(8, 1)), 8)

    def test_count_one(self) -> None:
        self.assertEqual(len(make_questions(1, 0)), 1)

    def test_count_fifty(self) -> None:
        self.assertEqual(len(make_questions(50, 7)), 50)

    def test_count_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(0, 1)

    def test_count_too_large_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(51, 1)

    def test_seed_reproducible(self) -> None:
        self.assertEqual(make_questions(8, 42), make_questions(8, 42))

    def test_different_seed_differs(self) -> None:
        first = [q.prompt for q in make_questions(8, 1)]
        second = [q.prompt for q in make_questions(8, 2)]
        self.assertNotEqual(first, second)

    def test_all_kinds_covered(self) -> None:
        kinds = set(q.kind for q in make_questions(8, 3))
        self.assertEqual(kinds, set(QUESTION_KINDS))

    def test_fields_not_empty(self) -> None:
        for question in make_questions(12, 5):
            self.assertTrue(question.prompt)
            self.assertTrue(question.answer)
            self.assertTrue(question.steps)

    def test_seed_negative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(8, -1)

    def test_seed_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(8, True)

    def test_count_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions("8", 1)  # type: ignore[arg-type]

    def test_question_is_named_tuple(self) -> None:
        question = make_questions(4, 9)[0]
        self.assertIsInstance(question, Question)
        self.assertIsInstance(tuple(question), tuple)


class TestRenderSheet(unittest.TestCase):
    def setUp(self) -> None:
        self.questions = make_questions(8, 1)
        self.html = render_sheet(self.questions, False)

    def test_has_doctype(self) -> None:
        self.assertTrue(self.html.startswith("<!DOCTYPE html>"))

    def test_parses_with_html_parser(self) -> None:
        collector = parse_html(self.html)
        for tag in ("html", "head", "body", "main", "ol", "li"):
            self.assertIn(tag, collector.tags)

    def test_question_count_in_text(self) -> None:
        self.assertIn("共 8 题", self.html)

    def test_no_answers_by_default(self) -> None:
        self.assertNotIn("参考答案", self.html)

    def test_answers_page_included(self) -> None:
        html_text = render_sheet(self.questions, True)
        self.assertIn("参考答案", html_text)
        self.assertIn('class="answer-page"', html_text)

    def test_answers_page_parses(self) -> None:
        collector = parse_html(render_sheet(self.questions, True))
        self.assertIn("section", collector.tags)

    def test_prompts_escaped(self) -> None:
        tricky = Question("测试", "<script>x</script>", "1", "2")
        html_text = render_sheet([tricky], False)
        self.assertIn("&lt;script&gt;", html_text)
        self.assertNotIn("<script>x", html_text)

    def test_empty_list_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet([], False)

    def test_invalid_question_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet([("细胞数", "问题", "答案", "步骤")], False)  # type: ignore[list-item]

    def test_answers_flag_type_checked(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(self.questions, "yes")  # type: ignore[arg-type]

    def test_non_sequence_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet("题目", False)  # type: ignore[arg-type]

    def test_tuple_accepted(self) -> None:
        self.assertIn("共 2 题", render_sheet(tuple(self.questions[:2]), False))

    def test_utf8_chinese_present(self) -> None:
        self.assertIn("细胞分裂练习纸", self.html)

    def test_print_style_present(self) -> None:
        self.assertIn("@page", self.html)


class TestRenderDemo(unittest.TestCase):
    def setUp(self) -> None:
        self.html = render_demo()

    def test_contains_svg(self) -> None:
        self.assertIn("<svg", self.html)
        self.assertIn("</svg>", self.html)

    def test_parses_with_html_parser(self) -> None:
        collector = parse_html(self.html)
        for tag in ("html", "body", "svg", "table", "circle"):
            self.assertIn(tag, collector.tags)

    def test_contains_stage_labels(self) -> None:
        for label in ("G1", "S 期", "G2", "M 期"):
            self.assertIn(label, self.html)

    def test_contains_table_rows(self) -> None:
        self.assertIn("<td>后期</td>", self.html)
        self.assertIn("<td>92</td>", self.html)

    def test_contains_percentages(self) -> None:
        self.assertIn("50.0%", self.html)


class TestCliCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name: str) -> str:
        return "%s/%s" % (self.tmp.name, name)

    def test_count_default(self) -> None:
        code, out, err = run_cli(["count"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("细胞总数：32", out)

    def test_count_custom(self) -> None:
        code, out, _ = run_cli(["count", "--start", "2", "--divisions", "3"])
        self.assertEqual(code, 0)
        self.assertIn("细胞总数：16", out)

    def test_count_zero_divisions(self) -> None:
        code, out, _ = run_cli(["count", "--start", "9", "--divisions", "0"])
        self.assertEqual(code, 0)
        self.assertIn("细胞总数：9", out)

    def test_time_default(self) -> None:
        code, out, _ = run_cli(["time"])
        self.assertEqual(code, 0)
        self.assertIn("所需总时间：80.0 小时", out)

    def test_time_float_cycle(self) -> None:
        code, out, _ = run_cli(["time", "--cycle", "20.5", "--divisions", "2"])
        self.assertEqual(code, 0)
        self.assertIn("所需总时间：41.0 小时", out)

    def test_stages_default(self) -> None:
        code, out, _ = run_cli(["stages"])
        self.assertEqual(code, 0)
        self.assertIn("M 期：60.0 分钟（5.0%）", out)

    def test_stages_custom(self) -> None:
        code, out, _ = run_cli(
            ["stages", "--cycle", "600", "--g1", "300", "--s", "150", "--g2", "90"]
        )
        self.assertEqual(code, 0)
        self.assertIn("M 期：60.0 分钟（10.0%）", out)

    def test_chromosomes_default(self) -> None:
        code, out, _ = run_cli(["chromosomes"])
        self.assertEqual(code, 0)
        self.assertIn("| 后期 | 92 | 0 | 92 |", out)
        self.assertIn("| 间期 | 46 | 92 | 92 |", out)

    def test_chromosomes_custom(self) -> None:
        code, out, _ = run_cli(["chromosomes", "--diploid", "8"])
        self.assertEqual(code, 0)
        self.assertIn("| 间期 | 8 | 16 | 16 |", out)

    def test_sheet_writes_file(self) -> None:
        target = self.path("sheet.html")
        code, out, _ = run_cli(["sheet", "--count", "6", "-o", target])
        self.assertEqual(code, 0)
        self.assertIn("已生成练习纸", out)
        with open(target, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("共 6 题", content)
        self.assertNotIn("参考答案", content)

    def test_sheet_with_answers(self) -> None:
        target = self.path("answers.html")
        code, _, _ = run_cli(["sheet", "--count", "4", "--answers", "-o", target])
        self.assertEqual(code, 0)
        with open(target, "r", encoding="utf-8") as handle:
            self.assertIn("参考答案", handle.read())

    def test_sheet_seed_reproducible(self) -> None:
        first = self.path("a.html")
        second = self.path("b.html")
        run_cli(["sheet", "--count", "5", "--seed", "3", "-o", first])
        run_cli(["sheet", "--count", "5", "--seed", "3", "-o", second])
        with open(first, "r", encoding="utf-8") as handle:
            content_a = handle.read()
        with open(second, "r", encoding="utf-8") as handle:
            content_b = handle.read()
        self.assertEqual(content_a, content_b)

    def test_sheet_different_seed(self) -> None:
        first = self.path("c.html")
        second = self.path("d.html")
        run_cli(["sheet", "--count", "5", "--seed", "1", "-o", first])
        run_cli(["sheet", "--count", "5", "--seed", "2", "-o", second])
        with open(first, "r", encoding="utf-8") as handle:
            content_a = handle.read()
        with open(second, "r", encoding="utf-8") as handle:
            content_b = handle.read()
        self.assertNotEqual(content_a, content_b)

    def test_demo_writes_file(self) -> None:
        target = self.path("demo.html")
        code, out, _ = run_cli(["demo", "-o", target])
        self.assertEqual(code, 0)
        self.assertIn("已生成细胞周期图解", out)
        with open(target, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("<svg", content)
        self.assertIn("细胞周期", content)

    def test_help_exits_zero(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("cellcycle", out.getvalue())

    def test_version_exits_zero(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn(__version__, out.getvalue())

    def test_no_command_exits_two(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main([])
        self.assertEqual(ctx.exception.code, 2)

    def test_unknown_command_exits_two(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(["unknown"])
        self.assertEqual(ctx.exception.code, 2)


class TestCliErrors(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def assert_failure(self, argv: List[str]) -> str:
        code, out, err = run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)
        return err

    def test_start_zero(self) -> None:
        self.assert_failure(["count", "--start", "0"])

    def test_start_too_large(self) -> None:
        self.assert_failure(["count", "--start", "1001"])

    def test_divisions_negative(self) -> None:
        self.assert_failure(["count", "--divisions", "-1"])

    def test_divisions_too_large(self) -> None:
        self.assert_failure(["count", "--divisions", "31"])

    def test_start_not_a_number(self) -> None:
        self.assert_failure(["count", "--start", "abc"])

    def test_start_empty(self) -> None:
        self.assert_failure(["count", "--start", ""])

    def test_result_too_large(self) -> None:
        self.assert_failure(["count", "--start", "1000", "--divisions", "30"])

    def test_cycle_zero(self) -> None:
        self.assert_failure(["time", "--cycle", "0"])

    def test_cycle_nan(self) -> None:
        self.assert_failure(["time", "--cycle", "nan"])

    def test_cycle_inf(self) -> None:
        self.assert_failure(["time", "--cycle", "inf"])

    def test_cycle_not_a_number(self) -> None:
        self.assert_failure(["time", "--cycle", "abc"])

    def test_stages_sum_equals_cycle(self) -> None:
        self.assert_failure(
            ["stages", "--cycle", "90", "--g1", "30", "--s", "30", "--g2", "30"]
        )

    def test_stages_sum_greater_than_cycle(self) -> None:
        self.assert_failure(
            ["stages", "--cycle", "100", "--g1", "50", "--s", "40", "--g2", "30"]
        )

    def test_diploid_odd(self) -> None:
        self.assert_failure(["chromosomes", "--diploid", "47"])

    def test_diploid_too_small(self) -> None:
        self.assert_failure(["chromosomes", "--diploid", "1"])

    def test_diploid_too_large(self) -> None:
        self.assert_failure(["chromosomes", "--diploid", "202"])

    def test_sheet_count_zero(self) -> None:
        target = "%s/x.html" % self.tmp.name
        self.assert_failure(["sheet", "--count", "0", "-o", target])

    def test_sheet_count_too_large(self) -> None:
        target = "%s/x.html" % self.tmp.name
        self.assert_failure(["sheet", "--count", "51", "-o", target])

    def test_sheet_seed_negative(self) -> None:
        target = "%s/x.html" % self.tmp.name
        self.assert_failure(["sheet", "--seed", "-1", "-o", target])

    def test_sheet_output_empty(self) -> None:
        self.assert_failure(["sheet", "--count", "2", "-o", ""])

    def test_sheet_output_bad_directory(self) -> None:
        err = self.assert_failure(
            ["sheet", "--count", "2", "-o", "/nonexistent_dir_xyz/sheet.html"]
        )
        self.assertIn("写入文件失败", err)

    def test_demo_output_bad_directory(self) -> None:
        err = self.assert_failure(
            ["demo", "-o", "/nonexistent_dir_xyz/demo.html"]
        )
        self.assertIn("写入文件失败", err)

    def test_missing_required_output(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(["demo"])
        self.assertEqual(ctx.exception.code, 2)

    def test_no_error_output_on_success(self) -> None:
        code, _, err = run_cli(["count", "--start", "1", "--divisions", "1"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()

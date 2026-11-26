"""细胞分裂核心计算：细胞数、周期时间、各期时长与染色体数目表。"""

import math
from typing import Dict, List, Tuple

# 结果上限：任何输出都必须小于该值
MAX_RESULT = 1e12

MIN_START = 1
MAX_START = 1000
MIN_DIVISIONS = 0
MAX_DIVISIONS = 30
MIN_DIPLOID = 2
MAX_DIPLOID = 200
MIN_QUESTIONS = 1
MAX_QUESTIONS = 50
MAX_SEED = 2147483647

STAGE_NAMES = ("G1", "S", "G2", "M")


def _as_int(value: object, name: str) -> int:
    """校验并返回整数，bool 不算数值。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s 必须是整数" % name)
    return int(value)


def _as_float(value: object, name: str) -> float:
    """校验并返回有限浮点数，bool 不算数值。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s 必须是数值" % name)
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("%s 必须是有限数值" % name)
    return number


def _checked(value: float, name: str) -> float:
    """检查结果有限且未超出上限。"""
    if not math.isfinite(value):
        raise ValueError("%s 结果不是有限数值" % name)
    if abs(value) >= MAX_RESULT:
        raise ValueError("%s 结果超出允许范围（需小于 1e12）" % name)
    return value


def parse_int_text(text: str, name: str) -> int:
    """把命令行文本解析为整数，失败时抛出中文 ValueError。"""
    if not isinstance(text, str):
        raise ValueError("%s 必须是文本" % name)
    stripped = text.strip()
    if not stripped:
        raise ValueError("%s 不能为空" % name)
    try:
        return int(stripped)
    except ValueError as exc:
        raise ValueError("%s 必须是整数：%s" % (name, stripped)) from exc


def parse_float_text(text: str, name: str) -> float:
    """把命令行文本解析为有限浮点数，失败时抛出中文 ValueError。"""
    if not isinstance(text, str):
        raise ValueError("%s 必须是文本" % name)
    stripped = text.strip()
    if not stripped:
        raise ValueError("%s 不能为空" % name)
    try:
        number = float(stripped)
    except ValueError as exc:
        raise ValueError("%s 必须是数值：%s" % (name, stripped)) from exc
    if not math.isfinite(number):
        raise ValueError("%s 必须是有限数值：%s" % (name, stripped))
    return number


def cell_count(start: int, divisions: int) -> int:
    """起始 start 个细胞连续有丝分裂 divisions 次后的细胞总数。"""
    start_value = _as_int(start, "起始细胞数")
    division_value = _as_int(divisions, "分裂次数")
    if start_value < MIN_START or start_value > MAX_START:
        raise ValueError(
            "起始细胞数必须在 %d..%d 之间" % (MIN_START, MAX_START)
        )
    if division_value < MIN_DIVISIONS or division_value > MAX_DIVISIONS:
        raise ValueError(
            "分裂次数必须在 %d..%d 之间" % (MIN_DIVISIONS, MAX_DIVISIONS)
        )
    result = start_value * (2 ** division_value)
    _checked(float(result), "细胞总数")
    return result


def total_time(cycle_hours: float, divisions: int) -> float:
    """每个细胞周期 cycle_hours 小时时，完成 divisions 次分裂所需小时数。"""
    cycle_value = _as_float(cycle_hours, "细胞周期")
    division_value = _as_int(divisions, "分裂次数")
    if cycle_value <= 0:
        raise ValueError("细胞周期必须大于 0 小时")
    if division_value < MIN_DIVISIONS or division_value > MAX_DIVISIONS:
        raise ValueError(
            "分裂次数必须在 %d..%d 之间" % (MIN_DIVISIONS, MAX_DIVISIONS)
        )
    return _checked(cycle_value * division_value, "所需总时间")


def stage_durations(
    cycle_minutes: float, g1: float, s: float, g2: float
) -> Dict[str, float]:
    """由总时长与 G1/S/G2 求各期时长（分钟），M 期 = 总时长 - G1 - S - G2。"""
    cycle_value = _as_float(cycle_minutes, "细胞周期总时长")
    g1_value = _as_float(g1, "G1 期时长")
    s_value = _as_float(s, "S 期时长")
    g2_value = _as_float(g2, "G2 期时长")
    if cycle_value <= 0:
        raise ValueError("细胞周期总时长必须大于 0 分钟")
    for label, value in (("G1", g1_value), ("S", s_value), ("G2", g2_value)):
        if value <= 0:
            raise ValueError("%s 期时长必须大于 0 分钟" % label)
        if value >= cycle_value:
            raise ValueError("%s 期时长必须小于细胞周期总时长" % label)
    known = g1_value + s_value + g2_value
    if known >= cycle_value:
        raise ValueError("G1、S、G2 三期时长之和必须小于细胞周期总时长")
    m_value = cycle_value - known
    durations = {
        "G1": g1_value,
        "S": s_value,
        "G2": g2_value,
        "M": _checked(m_value, "M 期时长"),
    }
    for label in STAGE_NAMES:
        _checked(durations[label], "%s 期时长" % label)
    return durations


def stage_percentages(durations: Dict[str, float]) -> Dict[str, float]:
    """按各期时长计算占比（百分比，0..100）。"""
    if not isinstance(durations, dict):
        raise ValueError("各期时长必须是字典")
    total = 0.0
    for label in STAGE_NAMES:
        if label not in durations:
            raise ValueError("缺少 %s 期时长" % label)
        total += _as_float(durations[label], "%s 期时长" % label)
    if total <= 0:
        raise ValueError("各期时长之和必须大于 0")
    percentages: Dict[str, float] = {}
    for label in STAGE_NAMES:
        percentages[label] = _checked(
            _as_float(durations[label], "%s 期时长" % label) / total * 100.0,
            "%s 期占比" % label,
        )
    return percentages


def mitosis_table(diploid: int) -> List[Tuple[str, int, int, int]]:
    """返回有丝分裂各时期每个细胞的（时期, 染色体数, 染色单体数, DNA 分子数）。

    间期取 DNA 复制完成后的数据；末期取每个子细胞的数据。
    """
    value = _as_int(diploid, "二倍体染色体数")
    if value < MIN_DIPLOID or value > MAX_DIPLOID:
        raise ValueError(
            "二倍体染色体数必须在 %d..%d 之间" % (MIN_DIPLOID, MAX_DIPLOID)
        )
    if value % 2 != 0:
        raise ValueError("二倍体染色体数必须是偶数")
    doubled = value * 2
    return [
        ("间期", value, doubled, doubled),
        ("前期", value, doubled, doubled),
        ("中期", value, doubled, doubled),
        ("后期", doubled, 0, doubled),
        ("末期", value, 0, value),
    ]


def check_question_count(count: int) -> int:
    """校验题目数量。"""
    value = _as_int(count, "题目数量")
    if value < MIN_QUESTIONS or value > MAX_QUESTIONS:
        raise ValueError(
            "题目数量必须在 %d..%d 之间" % (MIN_QUESTIONS, MAX_QUESTIONS)
        )
    return value


def check_seed(seed: int) -> int:
    """校验随机种子。"""
    value = _as_int(seed, "随机种子")
    if value < 0 or value > MAX_SEED:
        raise ValueError("随机种子必须在 0..%d 之间" % MAX_SEED)
    return value

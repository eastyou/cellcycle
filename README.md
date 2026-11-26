# cellcycle

[![CI](https://github.com/eastyou/cellcycle/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/cellcycle/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

初中生物「细胞分裂」教学工具：计算细胞增殖数量、细胞周期时间、G1/S/G2/M 各期时长与占比，输出有丝分裂各时期的染色体、染色单体与 DNA 分子数目表，并可生成 A4 练习纸与细胞周期图解页。

## 特性

- 细胞数计算：按 `起始细胞数 × 2^分裂次数` 计算有丝分裂后的细胞总数。
- 周期时间计算：已知单个细胞周期时长与分裂次数，给出所需总时间。
- 各期拆解：由细胞周期总时长与 G1、S、G2 期时长反推 M 期时长，并给出四期占比。
- 染色体数目表：按二倍体染色体数生成间期、前期、中期、后期、末期四类数目表。
- 练习纸生成：四种题型（细胞数、周期时间、各期计算、染色体数）混合出题，支持同种子复现与答案页。
- 图解页生成：以手写 SVG 环形图展示细胞周期四期占比，并附概念卡片与人体细胞数目表。
- 零第三方依赖，仅使用 Python 标准库，兼容 Python 3.9 及以上版本。
- 全部外部输入做类型与范围校验，非法输入以中文错误信息返回退出码 2。

## 安装

```bash
pip install .
```

也可不安装，直接在仓库根目录用 `python3 -m cellcycle` 运行。

## 使用

```bash
$ cellcycle count --start 1 --divisions 5
起始细胞数：1
有丝分裂次数：5
细胞总数：32
```

```bash
$ cellcycle time --cycle 20 --divisions 4
细胞周期：20.0 小时
有丝分裂次数：4
所需总时间：80.0 小时
```

```bash
$ cellcycle stages --cycle 1200 --g1 600 --s 300 --g2 240
细胞周期总时长：1200.0 分钟
G1 期：600.0 分钟（50.0%）
S 期：300.0 分钟（25.0%）
G2 期：240.0 分钟（20.0%）
M 期：60.0 分钟（5.0%）
```

```bash
$ cellcycle chromosomes --diploid 46
二倍体染色体数：46（2n）
| 时期 | 染色体数 | 染色单体数 | DNA 分子数 |
| --- | --- | --- | --- |
| 间期 | 46 | 92 | 92 |
| 前期 | 46 | 92 | 92 |
| 中期 | 46 | 92 | 92 |
| 后期 | 92 | 0 | 92 |
| 末期 | 46 | 0 | 46 |
说明：表中为每个细胞的数目，末期按每个子细胞计，间期取 DNA 复制完成后。
```

```bash
$ cellcycle sheet --count 8 --seed 1 -o sheet.html
已生成练习纸：sheet.html（共 8 题）
```

```bash
$ cellcycle demo -o demo.html
已生成细胞周期图解：demo.html
```

错误示例（退出码为 2）：

```bash
$ cellcycle count --start 0
错误：起始细胞数必须在 1..1000 之间
```

### 参数

| 子命令 | 参数 | 说明 | 取值范围 / 默认值 |
| --- | --- | --- | --- |
| `count` | `--start` | 起始细胞数 | 1..1000，默认 1 |
| `count` | `--divisions` | 连续有丝分裂次数 | 0..30，默认 5 |
| `time` | `--cycle` | 每个细胞周期的小时数 | 大于 0，默认 20 |
| `time` | `--divisions` | 分裂次数 | 0..30，默认 4 |
| `stages` | `--cycle` | 细胞周期总时长（分钟） | 大于 0，默认 1200 |
| `stages` | `--g1` | G1 期时长（分钟） | 大于 0，默认 600 |
| `stages` | `--s` | S 期时长（分钟） | 大于 0，默认 300 |
| `stages` | `--g2` | G2 期时长（分钟） | 大于 0，默认 240 |
| `chromosomes` | `--diploid` | 二倍体染色体数 | 2..200 的偶数，默认 46 |
| `sheet` | `--count` | 题目数量 | 1..50，默认 8 |
| `sheet` | `--seed` | 随机种子 | 0..2147483647，默认 1 |
| `sheet` | `-o` / `--output` | 输出 HTML 路径 | 必填 |
| `sheet` | `--answers` | 附加参考答案页 | 开关，默认关闭 |
| `demo` | `-o` / `--output` | 输出 HTML 路径 | 必填 |

补充约束：`stages` 要求 G1、S、G2 三期之和严格小于总时长（M 期必须大于 0）；任何结果都必须有限且小于 `1e12`。

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 执行成功 |
| 2 | 输入非法（类型、范围、空值）、写文件失败，或命令行参数缺失 |

## 作为库使用

```python
from cellcycle import (
    cell_count,
    make_questions,
    mitosis_table,
    render_sheet,
    stage_durations,
    total_time,
)

print(cell_count(1, 5))                                # 32
print(total_time(20.0, 4))                             # 80.0
print(stage_durations(1200.0, 600.0, 300.0, 240.0))    # {'G1': 600.0, 'S': 300.0, 'G2': 240.0, 'M': 60.0}
print(mitosis_table(46)[3])                            # ('后期', 92, 0, 92)

questions = make_questions(8, 1)
html_text = render_sheet(questions, True)
```

`make_questions` 使用 `random.Random(seed)`，相同 `count` 与 `seed` 必定生成相同题目；`render_sheet` 只做字符串拼接与 `html.escape` 转义，不依赖任何第三方模板库。

## 开发与测试

```bash
python3 -m unittest discover -s tests -v
```

共 144 个测试用例，覆盖正常值、边界（分裂次数为 0、超范围、各期之和超过或等于总时长、奇数二倍体、空输入）、非法输入（`main` 返回 2 且 stderr 含「错误：」）、同种子可复现、HTML 可被 `html.parser` 解析以及全部子命令。已在 Python 3.9.6 与 3.15.2 上验证，用例数一致且全部通过。测试产生的临时文件写入 `tempfile`，不会残留在仓库中。

## License

[MIT](LICENSE) © 2026 eastyou

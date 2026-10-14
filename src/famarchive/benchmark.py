"""模块 5：合成档案测试样例与内置基准 —— M4 实装。

纪律（data/README.md 第三节）：人物姓名只取假名白名单；证件号 999999 占位段、
电话 19900000000 假号段；真值与植入字段由生成器单一来源输出，manifest 不手写
第二份口径；覆盖度口径按异常类型列最低覆盖项（plan/04 §2），不写硬数字。
"""

from __future__ import annotations


def run_benchmark() -> dict:  # noqa: ANN001 - M4 实装
    raise NotImplementedError("基准生成器与断言随 M4 里程碑实装（plan/05）")

"""模块 2：规则化校验器 —— M3 实装。

只读 profile / 词表数据文件，规则不硬编码（一处定义多处引用）。
校验结果 {rule_id, field, severity, message, source} 逐条可回溯出处。
三个规则类型：required（必填）/ vocabulary（词表）/ format（W3CDTF）。
"""

from __future__ import annotations


def validate(fields: dict, profile: dict) -> list[dict]:  # noqa: ANN001 - M3 实装
    raise NotImplementedError("校验器随 M3 里程碑实装（plan/05）")

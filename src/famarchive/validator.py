"""模块 2：规则化校验器 —— M3 实装。

只读 profile / 词表数据文件，规则不硬编码（一处定义多处引用，plan/02 §4）。
校验结果 {rule_id, field, severity, message, source} 逐条可回溯出处。
三个规则类型：required（必填缺失）/ vocabulary（词表越界）/ format（W3CDTF）。
"""

from __future__ import annotations

import re
from pathlib import Path

from famarchive.resources import vocabularies_dir

# W3CDTF 日期子集：YYYY / YYYY-MM / YYYY-MM-DD / 带时区 datetime
# （DCMI dcterms:date 的 W3CDTF 语法编码方案；扩展形式如年份段 YYYY-MM-DDThh:mm:ss 不放开）
_W3CDTF_PATTERNS = (
    re.compile(r"^\d{4}$"),
    re.compile(r"^\d{4}-\d{2}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d+)?"
        r"(Z|[+-]\d{2}:\d{2})$"
    ),
)

_result_columns = ("rule_id", "field", "severity", "message", "source")


def _result(rule: dict, message: str) -> dict:
    return {
        "rule_id": rule["id"],
        "field": rule["field"],
        "severity": rule["severity"],
        "message": message,
        "source": rule["source"],
    }


def _load_vocabulary_ids(vocab_name: str) -> set[str]:
    path = vocabularies_dir() / f"{vocab_name}.yaml"
    import yaml

    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return {v["id"] for v in doc["values"]}


def is_valid_w3cdtf(value: str) -> bool:
    """W3CDTF：YYYY / YYYY-MM / YYYY-MM-DD / 带时区 datetime，其余拒绝。

    YYYY-MM / YYYY-MM-DD 还须通过日历语义检查（月份 01–12、日期在该月存在）。
    """
    if not isinstance(value, str):
        return False
    date_part = value.split("T", 1)[0]
    if not any(p.match(date_part) for p in _W3CDTF_PATTERNS):
        return False
    parts = date_part.split("-")
    try:
        if len(parts) >= 2:
            month = int(parts[1])
            if not 1 <= month <= 12:
                return False
        if len(parts) == 3:
            import datetime as _dt

            _dt.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return False
    return True


def validate(fields: dict, profile: dict) -> list[dict]:
    """按 profile 规则校验著录字段，返回违规结果列表（合法时为空）。

    fields: {字段名: 取值}（值应为字符串；非字符串按类型规则处理）。
    profile: load_profile() 返回的结构；规则缺 source 由加载器拦截，
    本函数不做二次出处检查——出处随结果逐条透出。
    """
    results: list[dict] = []
    vocab_cache: dict[str, set[str]] = {}

    for rule in profile["rules"]:
        rtype = rule["type"]
        field = rule["field"]
        value = fields.get(field)

        if rtype == "required":
            if value is None or (isinstance(value, str) and not value.strip()):
                results.append(_result(rule, f"必填字段 {field!r} 缺失或为空"))

        elif rtype == "vocabulary":
            if value is not None and str(value).strip():
                vocab_name = rule.get("vocab_source")
                if not vocab_name:
                    results.append(_result(rule, f"规则 {rule['id']} 未指定 vocab_source，无法校验"))
                    continue
                if vocab_name not in vocab_cache:
                    vocab_cache[vocab_name] = _load_vocabulary_ids(vocab_name)
                allowed = vocab_cache[vocab_name]
                if str(value) not in allowed:
                    results.append(
                        _result(rule, f"字段 {field!r} 取值 {value!r} 不在词表 {vocab_name} 内（允许 {sorted(allowed)}）")
                    )

        elif rtype == "format":
            fmt = rule.get("format", "W3CDTF")
            if value is not None and str(value).strip():
                if fmt == "W3CDTF" and not is_valid_w3cdtf(str(value)):
                    results.append(
                        _result(rule, f"字段 {field!r} 取值 {value!r} 不符合 W3CDTF（YYYY / YYYY-MM / YYYY-MM-DD / 带时区 datetime）")
                    )

    return results


def validate_item_file(
    item_id: str, fields: dict, profile_path: str | Path | None = None
) -> list[dict]:
    """便捷入口：加载 profile 数据文件后校验（CLI/GUI 共用）。"""
    from famarchive.profile import load_profile

    return validate(fields, load_profile(profile_path))

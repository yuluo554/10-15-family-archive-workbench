"""profile 加载器（骨架版）。

加载 DCMI 著录 profile 数据文件并做最小完整性检查：
- 必备键存在（profile_id / version / based_on / rules）；
- 每条规则必须带 source 出处（确定性纪律：无出处不落库）。
M3 扩展：规则类型展开、版本史与 archived/ 对比。
"""

from __future__ import annotations

from pathlib import Path

import yaml

from famarchive.resources import profiles_dir

_REQUIRED_PROFILE_KEYS = ("profile_id", "version", "based_on", "rules")
_REQUIRED_RULE_KEYS = ("id", "field", "type", "severity", "source")
_RULE_TYPES = ("required", "vocabulary", "format")


def load_profile(path: str | Path | None = None) -> dict:
    """加载 profile YAML；规则无出处或缺必备键时抛 ValueError。"""
    profile_path = Path(path) if path else profiles_dir() / "dcmi-family-profile.yaml"
    with open(profile_path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    missing = [k for k in _REQUIRED_PROFILE_KEYS if k not in profile]
    if missing:
        raise ValueError(f"profile 缺必备键: {missing}（{profile_path}）")

    for rule in profile["rules"]:
        missing_rule = [k for k in _REQUIRED_RULE_KEYS if k not in rule]
        if missing_rule:
            raise ValueError(f"规则 {rule.get('id', '?')} 缺键 {missing_rule}（无出处不得落库）")
        if rule["type"] not in _RULE_TYPES:
            raise ValueError(f"规则 {rule['id']} 类型非法: {rule['type']}")
    return profile

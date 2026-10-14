"""打包资源定位：profile / 词表 / 白名单数据文件随包内嵌。

开发态从仓库 data/ 读取；exe 打包后从 sys._MEIPASS 读取。
数据文件是规则唯一来源，代码不硬编码规则。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 开发态仓库根（src/famarchive/resources.py → 上溯两级）
_REPO_DATA = Path(__file__).resolve().parents[2] / "data"


def data_dir() -> Path:
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "famarchive_data"
    if bundled.is_dir():
        return bundled
    return _REPO_DATA


def profiles_dir() -> Path:
    return data_dir() / "profiles"


def vocabularies_dir() -> Path:
    return data_dir() / "vocabularies"


def export_whitelist_path() -> Path:
    return data_dir() / "export-whitelist.yaml"

"""打包资源定位：profile / 词表 / 白名单数据文件随包内嵌。

源码态从包内 src/famarchive/data/ 读取（随 wheel/sdist 一起安装，package-data 收录）；
exe 打包后从 sys._MEIPASS 读取。数据文件是规则唯一来源，代码不硬编码规则。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 包内规则数据目录（与 resources.py 同级的 data/，随 wheel/sdist 分发）
_PACKAGE_DATA = Path(__file__).parent / "data"


def data_dir() -> Path:
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "famarchive_data"
    if bundled.is_dir():
        return bundled
    return _PACKAGE_DATA


def profiles_dir() -> Path:
    return data_dir() / "profiles"


def vocabularies_dir() -> Path:
    return data_dir() / "vocabularies"


def export_whitelist_path() -> Path:
    return data_dir() / "export-whitelist.yaml"

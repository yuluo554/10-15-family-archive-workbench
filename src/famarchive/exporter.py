"""模块 4：白名单导出 —— M5 实装。

纪律：白名单以数据文件定义（data/export-whitelist.yaml，可审）；
默认抹除 GPS、证件号类敏感字段——抹除 = 导出文件中字段不出现，而非置空；
导出包内附 manifest（来源 profile 版本、白名单版本、导出时间）。
"""

from __future__ import annotations


def export(out_path, whitelist) -> dict:  # noqa: ANN001 - M5 实装
    raise NotImplementedError("白名单导出随 M5 里程碑实装（plan/05）")

"""模块 1：档案项导入（混合媒体类型）—— M2 实装。

确定性纪律（plan/01 题目文档）：
- 照片扫描件（JPEG/TIFF/PNG）、家书/文献/证件扫描页同一录入路径；
- EXIF 仅作预填建议（pillow 可选解析），永不自动写入著录字段；
- 文件指纹（SHA-256）保证同件不重复入库。
"""

from __future__ import annotations


def import_path(path) -> list[dict]:  # noqa: ANN001 - M2 实装
    raise NotImplementedError("模块 1 导入随 M2 里程碑实装（plan/05）")

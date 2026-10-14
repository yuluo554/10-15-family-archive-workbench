"""SQLite 档案库访问层（纯本地单文件）—— M2 实装。

schema 见 plan/02 §3：archive_items / metadata_fields / persons /
person_item_links / person_relations / profile_history / export_manifests。
SHA-256 指纹唯一约束保证同件不重复入库；无任何网络访问。
"""

from __future__ import annotations


class Store:
    def __init__(self, db_path) -> None:  # noqa: ANN001 - M2 实装
        raise NotImplementedError("档案库访问层随 M2 里程碑实装（plan/05）")

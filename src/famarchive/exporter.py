"""模块 4：白名单导出 —— M5 实装（plan/02 §5，plan/03 §5）。

纪律：
- 白名单以数据文件定义（data/export-whitelist.yaml，可审、可版本化）；
- 白名单外的著录字段在导出文件中**不出现**（键不出现，非置空）——K13 口径，
  与 benchmark sensitive_export_plan（exported=False）一致；
- 导出包内附 manifest：profile 版本、白名单版本、导出时间、逐条目字段摘要；
- 导出留痕写 export_manifests 表。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from famarchive.resources import export_whitelist_path


def load_whitelist(path: str | Path | None = None) -> dict:
    """读导出白名单（export_fields / sensitive_fields / version）。"""
    import yaml

    p = Path(path) if path else export_whitelist_path()
    with open(p, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    for key in ("version", "export_fields", "sensitive_fields"):
        if key not in doc:
            raise ValueError(f"导出白名单缺少必备键 {key}（{p}）")
    return doc


def export_package(
    store,
    out_path: str | Path,
    profile: dict,
    whitelist_path: str | Path | None = None,
    *, item_ids: list[str] | None = None,
) -> dict:
    """按白名单导出档案包（JSON 文件）并登记 manifest。

    返回 manifest dict（含 export_id / versions / exported_at / items）。
    导出条目结构：每个条目只序列化白名单 export_fields 内的字段；
    白名单外与 sensitive_fields 内的键**不写入**（非置空，K13）。
    """
    whitelist = load_whitelist(whitelist_path)
    export_fields = list(whitelist["export_fields"])
    sensitive = set(whitelist["sensitive_fields"])

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    items = store.list_items()
    if item_ids is not None:
        wanted = set(item_ids)
        items = [it for it in items if it["item_id"] in wanted]

    exported_items: list[dict] = []
    for item in items:
        fields = store.get_metadata_fields(item["item_id"])
        clean: dict = {}
        for name in export_fields:  # 白名单驱动：不在名单上的键根本不进循环
            if name in sensitive:
                continue  # 防御：白名单若误纳敏感键，仍按 K13 排除
            if name in fields:
                clean[name] = fields[name]
        exported_items.append({
            "item_id": item["item_id"],
            "media_type": item["media_type"],
            "file_name": item["file_name"],
            "fields": clean,
        })

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "manifest_version": "0.1.0",
        "export_id": f"export-{uuid.uuid4().hex[:8]}",
        "profile_id": profile["profile_id"],
        "profile_version": profile["version"],
        "whitelist_version": whitelist["version"],
        "exported_at": now,
        "erased_fields": sorted(sensitive),  # 抹除口径：导出文件中键不出现
        "item_count": len(exported_items),
        "items": exported_items,
    }

    payload = {"manifest": manifest, "records": exported_items}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with store._conn:
        store._conn.execute(
            """INSERT OR REPLACE INTO export_manifests
               (export_id, profile_version, whitelist_version, exported_at)
               VALUES (?, ?, ?, ?)""",
            (manifest["export_id"], manifest["profile_version"],
             manifest["whitelist_version"], now),
        )
    return manifest

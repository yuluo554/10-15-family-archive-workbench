"""模块 3：人物/代际关系标注与家庭年表 —— M3 实装。

纪律（plan/01 题目文档 + plan/03 §4）：
- 关系边类型取受控词表 relation-type（越界即拒绝，不静默）；
- 同名人物**不自动合并**：find_same_name_pairs 只报告，合并须人工确认后
  走 Store.confirm_same_name_merge 显式路径；
- 家庭年表只收"编目完成"的档案项（必填字段齐且校验零 error）。
"""

from __future__ import annotations

from pathlib import Path

from famarchive.resources import vocabularies_dir
from famarchive.store import Store


def load_relation_type_ids() -> set[str]:
    import yaml

    path = vocabularies_dir() / "relation-type.yaml"
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return {v["id"] for v in doc["values"]}


def add_relation_checked(
    store: Store, from_person: str, to_person: str, relation_type: str
) -> None:
    """带词表校验的关系边写入：relation_type 不在 relation-type 词表内即抛 ValueError。"""
    allowed = load_relation_type_ids()
    if relation_type not in allowed:
        raise ValueError(
            f"relation_type {relation_type!r} 不在 relation-type 词表内（允许 {sorted(allowed)}）"
        )
    store.add_relation(from_person, to_person, relation_type)


def find_same_name_persons(store: Store) -> list[list[dict]]:
    """报告同名人物组（≥2 人同名），供人工确认合并；本函数不做任何合并。"""
    groups: list[list[dict]] = []
    for person in store.list_persons():
        if any(person["name"] in g_names for g_names in ({p["name"] for p in g} for g in groups)):
            continue
        same = store.find_persons_by_name(person["name"])
        if len(same) >= 2:
            groups.append(same)
    return groups


def build_timeline(store: Store, profile: dict, *, profile_path: str | Path | None = None) -> list[dict]:
    """家庭年表：按著录 date 升序排列"编目完成"的档案项。

    编目完成的判定：必填字段齐 + 校验结果中无 severity=error 的条目
    （warning 不拦截）。未编目完成的档案项不进入年表（plan/03 §4）。
    """
    from famarchive.validator import validate

    timeline: list[dict] = []
    linked: dict[str, list[str]] = {}
    for link in store._conn.execute(
        "SELECT pil.item_id, p.name FROM person_item_links pil JOIN persons p ON p.person_id = pil.person_id"
    ):
        linked.setdefault(link["item_id"], []).append(link["name"])
    for item in store.list_items():
        fields = store.get_metadata_fields(item["item_id"])
        results = validate(fields, profile)
        errors = [r for r in results if r["severity"] == "error"]
        date_value = fields.get("date")
        if errors or not date_value:
            continue  # 未编目完成：不进年表
        timeline.append(
            {
                "item_id": item["item_id"],
                "file_name": item["file_name"],
                "media_type": item["media_type"],
                "date": date_value,
                "title": fields.get("title", ""),
                "persons": linked.get(item["item_id"], []),
            }
        )
    timeline.sort(key=lambda e: e["date"])
    return timeline

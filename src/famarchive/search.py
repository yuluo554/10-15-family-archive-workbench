"""模块 4：检索 —— M5 实装（plan/03 §1/§4）。

字段/人物/时间范围/媒体类型的组合查询，走核心库供 CLI 与 GUI 共用。
查询条件全部可选，多个条件之间是 AND 语义；未给任何条件返回全部条目
（等价 list_items，但附著录字段与人物）。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Query:
    """组合查询条件（全部可选；None/空串表示不限制）。"""

    text: str | None = None            # 标题/描述/地点/关键词 模糊匹配
    field_name: str | None = None      # 指定著录字段名（与 field_value 配对）
    field_value: str | None = None     # 指定著录字段取值（模糊包含）
    person: str | None = None          # 人物姓名或 person_id（链接过的条目）
    date_from: str | None = None       # W3CDTF 下界（含），按字符串比较
    date_to: str | None = None         # W3CDTF 上界（含）
    media_type: str | None = None      # 媒体类型（media-type 词表 id）
    ids: set[str] = field(default_factory=set)  # 限定条目集（内部用）

    def is_empty(self) -> bool:
        plain = (self.text, self.field_name, self.field_value,
                 self.person, self.date_from, self.date_to, self.media_type)
        return not any(plain) and not self.ids


def _matches_date(date_value: str | None, q: Query) -> bool:
    if q.date_from is None and q.date_to is None:
        return True
    if not date_value:
        return False
    # W3CDTF 形态（YYYY / YYYY-MM / YYYY-MM-DD）按字典序即时间序，前缀截齐比较。
    lo = q.date_from or ""
    hi = q.date_to or "9999-99-99"
    if date_value < lo[: len(date_value)] and lo:
        return False
    if date_value > hi[: len(date_value)]:
        return False
    return True


def search(store, query: Query) -> list[dict]:
    """组合查询：返回条目列表，每条附著录字段与关联人物名。

    只走 store 读取层，不写库；结果按 imported_at, item_id 稳定排序。
    """
    items = store.list_items()
    if query.ids:
        items = [it for it in items if it["item_id"] in query.ids]

    # 人物条件 → 命中的条目集（按姓名或 person_id，同名全部并入）
    person_items: set[str] | None = None
    if query.person:
        person_items = set()
        for p in store.list_persons():
            if query.person in (p["name"], p["person_id"]):
                person_items.update(
                    it["item_id"] for it in store.list_items_for_person(p["person_id"])
                )

    results: list[dict] = []
    for item in items:
        if query.media_type and item["media_type"] != query.media_type:
            continue
        if person_items is not None and item["item_id"] not in person_items:
            continue
        fields = store.get_metadata_fields(item["item_id"])
        if query.field_name:
            if query.field_value is None:
                if query.field_name not in fields:
                    continue
            else:
                if query.field_value not in str(fields.get(query.field_name, "")):
                    continue
        elif query.field_value:
            # 未指定字段名时按全字段模糊匹配
            if not any(query.field_value in str(v) for v in fields.values()):
                continue
        if query.text:
            haystack = " ".join(str(v) for v in fields.values())
            if query.text not in haystack:
                continue
        if not _matches_date(fields.get("date"), query):
            continue

        persons = [
            row["name"]
            for row in store._conn.execute(
                """SELECT p.name FROM person_item_links pil
                   JOIN persons p ON p.person_id = pil.person_id
                   WHERE pil.item_id = ? ORDER BY p.name""",
                (item["item_id"],),
            )
        ]
        results.append({
            "item_id": item["item_id"],
            "file_name": item["file_name"],
            "media_type": item["media_type"],
            "fields": fields,
            "persons": persons,
        })
    return results

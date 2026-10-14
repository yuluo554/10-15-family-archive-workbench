"""SQLite 档案库访问层（纯本地单文件）—— M2 实装。

schema 见 plan/02 §3：archive_items / metadata_fields / persons /
person_item_links / person_relations / profile_history / export_manifests。
SHA-256 指纹唯一约束保证同件不重复入库；无任何网络访问。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS archive_items (
    item_id        TEXT PRIMARY KEY,
    media_type     TEXT NOT NULL,
    sha256         TEXT NOT NULL UNIQUE,
    file_name      TEXT NOT NULL,
    original_path  TEXT,
    thumbnail_path TEXT,
    exif_snapshot  TEXT,
    exif_suggestions TEXT,
    imported_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metadata_fields (
    item_id    TEXT NOT NULL REFERENCES archive_items(item_id),
    field_name TEXT NOT NULL,
    value      TEXT,
    profile_version TEXT,
    PRIMARY KEY (item_id, field_name)
);

CREATE TABLE IF NOT EXISTS persons (
    person_id TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    relation  TEXT
);

CREATE TABLE IF NOT EXISTS person_item_links (
    person_id TEXT NOT NULL REFERENCES persons(person_id),
    item_id   TEXT NOT NULL REFERENCES archive_items(item_id),
    link_role TEXT,
    PRIMARY KEY (person_id, item_id)
);

CREATE TABLE IF NOT EXISTS person_relations (
    from_person TEXT NOT NULL REFERENCES persons(person_id),
    to_person   TEXT NOT NULL REFERENCES persons(person_id),
    relation_type TEXT NOT NULL,
    PRIMARY KEY (from_person, to_person)
);

CREATE TABLE IF NOT EXISTS profile_history (
    version     TEXT PRIMARY KEY,
    based_on    TEXT,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_manifests (
    export_id        TEXT PRIMARY KEY,
    profile_version  TEXT,
    whitelist_version TEXT,
    exported_at      TEXT NOT NULL
);
"""


class DuplicateItemError(Exception):
    """同 SHA-256 指纹的文件已入库。"""

    def __init__(self, item_id: str, sha256: str) -> None:
        super().__init__(f"指纹 {sha256[:12]}… 已入库（item_id={item_id}），拒绝重复导入")
        self.item_id = item_id
        self.sha256 = sha256


class Store:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---- archive_items -------------------------------------------------

    def find_by_sha256(self, sha256: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM archive_items WHERE sha256 = ?", (sha256,)
        ).fetchone()
        return dict(row) if row else None

    def add_item(
        self,
        *,
        item_id: str,
        media_type: str,
        sha256: str,
        file_name: str,
        original_path: str | None = None,
        thumbnail_path: str | None = None,
        exif_snapshot: dict | None = None,
        exif_suggestions: list | None = None,
        imported_at: str,
    ) -> dict:
        """登记档案项；同指纹已存在时抛 DuplicateItemError（不入库）。"""
        existing = self.find_by_sha256(sha256)
        if existing is not None:
            raise DuplicateItemError(existing["item_id"], sha256)
        import json

        self._conn.execute(
            """INSERT INTO archive_items
               (item_id, media_type, sha256, file_name, original_path,
                thumbnail_path, exif_snapshot, exif_suggestions, imported_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item_id,
                media_type,
                sha256,
                file_name,
                original_path,
                thumbnail_path,
                json.dumps(exif_snapshot, ensure_ascii=False) if exif_snapshot else None,
                json.dumps(exif_suggestions, ensure_ascii=False) if exif_suggestions else None,
                imported_at,
            ),
        )
        self._conn.commit()
        return self.get_item(item_id)  # type: ignore[return-value]

    def get_item(self, item_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM archive_items WHERE item_id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_items(self) -> list[dict]:
        return [
            dict(r)
            for r in self._conn.execute(
                "SELECT * FROM archive_items ORDER BY imported_at, item_id"
            )
        ]

    # ---- metadata_fields -----------------------------------------------

    def set_metadata_fields(
        self, item_id: str, fields: dict[str, str], profile_version: str
    ) -> None:
        """写入/覆盖著录字段。调用方必须保证：此处只进人工确认值，EXIF 预填建议不进。"""
        import json

        with self._conn:
            for name, value in fields.items():
                self._conn.execute(
                    """INSERT INTO metadata_fields (item_id, field_name, value, profile_version)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(item_id, field_name)
                       DO UPDATE SET value = excluded.value,
                                     profile_version = excluded.profile_version""",
                    (item_id, name, json.dumps(value, ensure_ascii=False), profile_version),
                )

    def get_metadata_fields(self, item_id: str) -> dict[str, str]:
        import json

        rows = self._conn.execute(
            "SELECT field_name, value FROM metadata_fields WHERE item_id = ?", (item_id,)
        ).fetchall()
        return {r["field_name"]: json.loads(r["value"]) for r in rows}

    def count(self, table: str) -> int:
        if table not in {
            "archive_items", "metadata_fields", "persons", "person_item_links",
            "person_relations", "profile_history", "export_manifests",
        }:
            raise ValueError(f"未知表名: {table}")
        return self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    # ---- persons / person_item_links / person_relations（M3） -------------

    def add_person(self, *, person_id: str, name: str, relation: str | None = None) -> dict:
        """登记人物。同名人物**不自动合并**：允许并存，合并须走显式 confirm_same_name。"""
        with self._conn:
            self._conn.execute(
                "INSERT INTO persons (person_id, name, relation) VALUES (?, ?, ?)",
                (person_id, name, relation),
            )
        return self.get_person(person_id)  # type: ignore[return-value]

    def get_person(self, person_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM persons WHERE person_id = ?", (person_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_persons(self) -> list[dict]:
        return [
            dict(r)
            for r in self._conn.execute("SELECT * FROM persons ORDER BY person_id")
        ]

    def find_persons_by_name(self, name: str) -> list[dict]:
        """同名人物查询（可能有多个——同名合并必须人工确认，不自动）。"""
        return [
            dict(r)
            for r in self._conn.execute(
                "SELECT * FROM persons WHERE name = ? ORDER BY person_id", (name,)
            )
        ]

    def update_person_name(self, person_id: str, name: str) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE persons SET name = ? WHERE person_id = ?", (name, person_id)
            )

    def confirm_same_name_merge(self, keep_id: str, drop_id: str) -> None:
        """同名人工确认后的合并：把 drop 的人物与其链接/关系并进 keep 后删除 drop。

        只能由人工确认路径调用（GUI/CLI 显式动作），任何自动流程不得调用。
        """
        with self._conn:
            self._conn.execute(
                "UPDATE OR IGNORE person_item_links SET person_id = ? WHERE person_id = ?",
                (keep_id, drop_id),
            )
            self._conn.execute(
                "DELETE FROM person_item_links WHERE person_id = ?", (drop_id,)
            )
            self._conn.execute(
                "UPDATE OR IGNORE person_relations SET from_person = ? WHERE from_person = ?",
                (keep_id, drop_id),
            )
            self._conn.execute(
                "UPDATE OR IGNORE person_relations SET to_person = ? WHERE to_person = ?",
                (keep_id, drop_id),
            )
            self._conn.execute(
                "DELETE FROM person_relations WHERE from_person = ? AND to_person = ?",
                (keep_id, keep_id),
            )
            self._conn.execute(
                "DELETE FROM person_relations WHERE from_person = ? OR to_person = ?",
                (drop_id, drop_id),
            )
            self._conn.execute("DELETE FROM persons WHERE person_id = ?", (drop_id,))

    def link_person_item(
        self, person_id: str, item_id: str, link_role: str | None = None
    ) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO person_item_links (person_id, item_id, link_role)
                   VALUES (?, ?, ?)
                   ON CONFLICT(person_id, item_id)
                   DO UPDATE SET link_role = excluded.link_role""",
                (person_id, item_id, link_role),
            )

    def unlink_person_item(self, person_id: str, item_id: str) -> None:
        with self._conn:
            self._conn.execute(
                "DELETE FROM person_item_links WHERE person_id = ? AND item_id = ?",
                (person_id, item_id),
            )

    def list_items_for_person(self, person_id: str) -> list[dict]:
        return [
            dict(r)
            for r in self._conn.execute(
                """SELECT ai.*, pil.link_role FROM person_item_links pil
                   JOIN archive_items ai ON ai.item_id = pil.item_id
                   WHERE pil.person_id = ?
                   ORDER BY ai.imported_at, ai.item_id""",
                (person_id,),
            )
        ]

    def add_relation(
        self, from_person: str, to_person: str, relation_type: str
    ) -> None:
        """关系边：relation_type 取值限 relation-type 词表（调用方校验）。"""
        with self._conn:
            self._conn.execute(
                """INSERT INTO person_relations (from_person, to_person, relation_type)
                   VALUES (?, ?, ?)
                   ON CONFLICT(from_person, to_person)
                   DO UPDATE SET relation_type = excluded.relation_type""",
                (from_person, to_person, relation_type),
            )

    def remove_relation(self, from_person: str, to_person: str) -> None:
        with self._conn:
            self._conn.execute(
                "DELETE FROM person_relations WHERE from_person = ? AND to_person = ?",
                (from_person, to_person),
            )

    def list_relations(self) -> list[dict]:
        return [
            dict(r)
            for r in self._conn.execute(
                "SELECT * FROM person_relations ORDER BY from_person, to_person"
            )
        ]

    # ---- profile_history（M3 版本化登记） ----------------------------------

    def record_profile_version(self, *, version: str, based_on: str | None, recorded_at: str) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO profile_history (version, based_on, recorded_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(version) DO NOTHING""",
                (version, based_on, recorded_at),
            )

    def list_profile_history(self) -> list[dict]:
        return [
            dict(r)
            for r in self._conn.execute(
                "SELECT * FROM profile_history ORDER BY recorded_at, version"
            )
        ]

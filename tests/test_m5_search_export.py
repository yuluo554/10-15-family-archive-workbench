"""M5 测试：检索与白名单导出（plan/05 M5 DoD 锁定）。

- search.py：字段/人物/时间/媒体类型组合查询（AND 语义、条件全可选）；
- exporter.py：白名单导出包 + manifest（记 profile/白名单版本、导出时间），
  敏感字段抹除 = **键不出现**（K13，非置空），衔接 benchmark sensitive_export_plan；
- 导出留痕写 export_manifests 表。
"""

from __future__ import annotations

import json

import pytest

from famarchive.benchmark import generate_samples
from famarchive.exporter import export_package, load_whitelist
from famarchive.profile import load_profile
from famarchive.search import Query, search
from famarchive.store import Store


@pytest.fixture()
def store(tmp_path):
    """植入基准样例的内存化库（baseline/sensitive-carry 已编目）。"""
    s = Store(tmp_path / "m5.sqlite3")
    profile = load_profile()
    manifest = generate_samples()
    base = next(x for x in manifest["samples"] if x["sample_id"] == "baseline-full")
    sens = next(x for x in manifest["samples"] if x["sample_id"] == "sensitive-carry")
    unc = next(x for x in manifest["samples"] if x["sample_id"] == "uncatalogued")
    s.add_item(item_id="it-base", media_type=base["media_type"], sha256="c" * 64,
               file_name="baseline.jpg", imported_at="2026-10-14T00:00:00+00:00")
    s.set_metadata_fields("it-base", base["planted_fields"], profile["version"])
    s.add_item(item_id="it-sens", media_type=sens["media_type"], sha256="d" * 64,
               file_name="sensitive.jpg", imported_at="2026-10-14T00:00:00+00:00")
    s.set_metadata_fields("it-sens", sens["planted_fields"], profile["version"])
    # 敏感携带值按 benchmark 口径落 exif_snapshot（库层 JSON 字符串），验证导出不带出
    s.add_item(item_id="it-uncat", media_type=unc["media_type"], sha256="e" * 64,
               file_name="uncat.jpg", imported_at="2026-10-14T00:00:00+00:00")
    p1 = s.add_person(person_id="mp1", name=manifest["fake_name_whitelist"][0])
    s.link_person_item(p1["person_id"], "it-base", "人物")
    yield s, manifest, profile
    s.close()


# ---- search ------------------------------------------------------------------


def test_search_by_media_type(store):
    s, _, _ = store
    results = search(s, Query(media_type="id-card"))
    assert [r["item_id"] for r in results] == ["it-sens"]


def test_search_by_person(store):
    s, manifest, _ = store
    name = manifest["fake_name_whitelist"][0]
    results = search(s, Query(person=name))
    assert [r["item_id"] for r in results] == ["it-base"]
    assert name in results[0]["persons"]


def test_search_by_time_range(store):
    s, _, _ = store
    results = search(s, Query(date_from="1963-01", date_to="1963-12"))
    assert {r["item_id"] for r in results} == {"it-base", "it-sens"}
    assert search(s, Query(date_from="1990")) == []


def test_search_by_field_value(store):
    s, manifest, _ = store
    placeholders = manifest["placeholders"]
    # 敏感值不在著录字段里（K12/K13 口径），按字段值查不到
    assert search(s, Query(field_name="subject", field_value="张三丰")) != []
    assert search(s, Query(field_name="subject",
                           field_value=placeholders["id_number"])) == []


def test_search_combined_and_semantics(store):
    s, _, _ = store
    results = search(s, Query(media_type="photo-scan", date_from="1963"))
    assert {r["item_id"] for r in results} == {"it-base"}
    results = search(s, Query(media_type="photo-scan", person="不存在的人"))
    assert results == []


def test_search_empty_query_returns_all(store):
    s, _, _ = store
    assert len(search(s, Query())) == 3


# ---- exporter ----------------------------------------------------------------


def test_whitelist_loads_with_version_and_sensitive_fields():
    wl = load_whitelist()
    assert wl["version"]
    assert {"gps", "id-number", "phone", "biometric"} <= set(wl["sensitive_fields"])
    assert "title" in wl["export_fields"]


def test_export_sensitive_keys_absent(store, tmp_path):
    """K13：导出文件中敏感键不出现（非置空），白名单外字段同样不出现。"""
    s, manifest, profile = store
    out = tmp_path / "pkg.json"
    export_package(s, out, profile)
    payload = json.loads(out.read_text(encoding="utf-8"))
    forbidden = set(manifest["sensitive_export_plan"]) | {"exif_snapshot", "sha256"}
    for rec in payload["records"]:
        keys = set(rec["fields"])
        assert not (keys & forbidden), f"导出文件出现禁止键：{keys & forbidden}"
        assert None not in rec["fields"].values()
    base = next(r for r in payload["records"] if r["item_id"] == "it-base")
    assert base["fields"]["title"].startswith("祖母")  # 白名单内字段正常导出
    assert "type" in base["fields"] and "coverage" in base["fields"]


def test_export_manifest_records_versions(store, tmp_path):
    s, _, profile = store
    out = tmp_path / "pkg.json"
    manifest = export_package(s, out, profile)
    wl = load_whitelist()
    assert manifest["profile_version"] == profile["version"]
    assert manifest["whitelist_version"] == wl["version"]
    assert manifest["exported_at"]  # 导出时间留痕
    assert manifest["item_count"] == 3
    # 导出留痕写 export_manifests 表
    count = s._conn.execute("SELECT COUNT(*) FROM export_manifests").fetchone()[0]
    assert count == 1


def test_export_subset_and_whitespace_vs_absence(store, tmp_path):
    """导出只含白名单内键：键不出现 ≠ 置空（导出字段集中无 None 占位键）。"""
    s, _, profile = store
    out = tmp_path / "pkg.json"
    manifest = export_package(s, out, profile, item_ids=["it-base"])
    assert manifest["item_count"] == 1
    rec = manifest["items"][0]
    assert set(rec["fields"]) <= set(load_whitelist()["export_fields"])

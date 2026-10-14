"""M3 测试：著录规则校验器 + 人物/关系/年表 + profile 版本化（plan/05 M3 DoD 锁定）。

- validator：三类规则（required / vocabulary / format-W3CDTF）全部可触发，
  结果逐条含 {rule_id, field, severity, message, source}（K1 出处透出）；
- persons：关系边限 relation-type 词表；同名不自动合并；年表只收编目完成项；
- profile v0.2.0 与 v0.1.0 必填集实质可区分（K6），旧版留档 archived/。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from famarchive.persons import add_relation_checked, build_timeline
from famarchive.profile import load_profile
from famarchive.store import Store
from famarchive.validator import is_valid_w3cdtf, validate

REPO_DATA = Path(__file__).resolve().parents[1] / "data"
ARCHIVED_V010 = REPO_DATA / "profiles" / "archived" / "dcmi-family-profile-v0.1.0-draft.yaml"


@pytest.fixture()
def store(tmp_path):
    s = Store(tmp_path / "archive.sqlite3")
    yield s
    s.close()


@pytest.fixture()
def profile():
    return load_profile()


# ---- validator：三类规则 + 出处 -------------------------------------------


def _rule(profile, rule_id):
    return next(r for r in profile["rules"] if r["id"] == rule_id)


def test_valid_fields_produce_no_results(profile):
    fields = {
        "title": "祖母的结婚照",
        "date": "1963-05-01",
        "description": "黑白照片",
        "type": "photo-scan",
        "coverage": "北京",
    }
    assert validate(fields, profile) == []


def test_required_rule_triggers_with_source(profile):
    results = validate({}, profile)
    for rid in ("REQ-TITLE", "REQ-DATE", "REQ-TYPE", "REQ-DESCRIPTION", "REQ-COVERAGE"):
        rule = _rule(profile, rid)
        hit = [r for r in results if r["rule_id"] == rid]
        assert hit, f"{rid} 未触发"
        r = hit[0]
        assert set(r) == {"rule_id", "field", "severity", "message", "source"}
        assert r["field"] == rule["field"]
        assert r["severity"] == "error"
        assert r["source"] == rule["source"]


def test_vocabulary_rule_triggers(profile):
    results = validate(
        {
            "title": "t",
            "date": "2020-01-01",
            "description": "d",
            "coverage": "c",
            "type": "not-a-type",
        },
        profile,
    )
    hit = [r for r in results if r["rule_id"] == "VOC-TYPE"]
    assert hit and hit[0]["severity"] == "error"
    assert "not-a-type" in hit[0]["message"]
    assert "media-type" in hit[0]["source"]


def test_format_w3cdtf_triggers(profile):
    results = validate(
        {
            "title": "t",
            "date": "1963年5月1日",
            "description": "d",
            "coverage": "c",
            "type": "photo-scan",
        },
        profile,
    )
    hit = [r for r in results if r["rule_id"] == "FMT-DATE"]
    assert hit and "W3CDTF" in hit[0]["message"]


def test_w3cdtf_accepted_and_rejected_forms():
    valid = ["1963", "1963-05", "1963-05-01", "1963-05-01T10:30:00+08:00",
             "1963-05-01T10:30Z", "1963-05-01T10:30:00.123+00:00"]
    invalid = ["", "1963-5-1", "63-05-01", "1963/05/01", "1963年5月",
               "1963-05-01 10:30", "1963-13", "1963-00", "01-05-1963"]
    for v in valid:
        assert is_valid_w3cdtf(v), f"{v} 应合法"
    for v in invalid:
        assert not is_valid_w3cdtf(v), f"{v} 应拒绝"


def test_empty_and_whitespace_fields_count_as_missing(profile):
    results = validate({"title": "   "}, profile)
    assert any(r["rule_id"] == "REQ-TITLE" for r in results)


def test_validator_reads_profile_data_file_not_hardcoded(tmp_path):
    """规则不硬编码：自造 profile（新必填字段）也能驱动校验。"""
    custom = tmp_path / "custom.yaml"
    custom.write_text(
        "profile_id: c\nversion: t\nbased_on: t\n"
        "rules:\n"
        "- {id: REQ-NOTE, field: note, type: required, severity: error, source: 测试出处}\n",
        encoding="utf-8",
    )
    results = validate({}, load_profile(custom))
    assert [r["rule_id"] for r in results] == ["REQ-NOTE"]
    assert results[0]["source"] == "测试出处"


# ---- persons：关系词表 / 同名 / 年表 ----------------------------------------


def test_relation_type_outside_vocabulary_rejected(store):
    p1 = store.add_person(person_id="p1", name="张三丰")
    p2 = store.add_person(person_id="p2", name="李四")
    with pytest.raises(ValueError, match="词表"):
        add_relation_checked(store, p1["person_id"], p2["person_id"], "父子")  # 词表外
    add_relation_checked(store, p1["person_id"], p2["person_id"], "parent-child")  # 词表内
    assert store.list_relations()[0]["relation_type"] == "parent-child"


def test_same_name_not_auto_merged(store):
    """同名人物并存不自动合并；合并只走显式 confirm_same_name_merge。"""
    store.add_person(person_id="p1", name="李四", relation="父亲")
    store.add_person(person_id="p2", name="李四", relation="儿子")
    from famarchive.persons import find_same_name_persons

    groups = find_same_name_persons(store)
    assert len(groups) == 1 and {p["person_id"] for p in groups[0]} == {"p1", "p2"}
    # 未合并：仍是两个人
    assert store.count("persons") == 2
    store.confirm_same_name_merge("p1", "p2")  # 人工确认后
    assert store.count("persons") == 1
    assert store.get_person("p2") is None


def test_timeline_only_covers_categorized_items(tmp_path, store, profile):
    """年表只收编目完成项（必填齐+零 error）；未完成不进入。"""
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    done = store.add_item(
        item_id="item-done", media_type="photo-scan", sha256="11" * 32,
        file_name="done.jpg", imported_at=ts,
    )
    undone = store.add_item(
        item_id="item-undone", media_type="photo-scan", sha256="22" * 32,
        file_name="undone.jpg", imported_at=ts,
    )
    # done：必填齐全 → 进年表
    store.set_metadata_fields(
        "item-done",
        {"title": "老照片", "date": "1963-05-01", "type": "photo-scan",
         "description": "d", "coverage": "北京"},
        profile_version=profile["version"],
    )
    # undone：缺 description/coverage → 不进年表
    store.set_metadata_fields(
        "item-undone", {"title": "半成品", "date": "1963-05-02", "type": "photo-scan"},
        profile_version=profile["version"],
    )
    store.add_person(person_id="p1", name="张三丰")
    store.link_person_item("p1", "item-done", "人物")

    timeline = build_timeline(store, profile)
    ids = [e["item_id"] for e in timeline]
    assert ids == ["item-done"], f"年表应只含编目完成项，实际 {ids}"
    assert timeline[0]["persons"] == ["张三丰"]
    assert timeline[0]["date"] == "1963-05-01"


# ---- profile v0.2.0 版本化（K6） -------------------------------------------


def test_profile_version_bumped_with_substantive_change():
    profile = load_profile()
    assert profile["version"] == "0.2.0"
    v2_required = {r["field"] for r in profile["rules"] if r["type"] == "required"}
    assert {"description", "coverage"} <= v2_required, "v0.2.0 必填集须与 v0.1.0 实质可区分"


def test_archived_v010_exists_and_is_distinguishable():
    assert ARCHIVED_V010.exists(), "v0.1.0 未留档 data/profiles/archived/"
    old = load_profile(ARCHIVED_V010)
    assert old["version"] == "0.1.0-draft"
    new = load_profile()
    old_required = {r["field"] for r in old["rules"] if r["type"] == "required"}
    new_required = {r["field"] for r in new["rules"] if r["type"] == "required"}
    assert new_required != old_required, "两版本必填集必须实质可区分（K6）"
    assert new_required - old_required == {"description", "coverage"}


def test_profile_history_recorded(tmp_path, store):
    from datetime import datetime, timezone

    profile = load_profile()
    store.record_profile_version(
        version=profile["version"],
        based_on=profile["based_on"],
        recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    history = store.list_profile_history()
    assert len(history) == 1
    assert history[0]["version"] == "0.2.0"
    assert "DCMI" in history[0]["based_on"]

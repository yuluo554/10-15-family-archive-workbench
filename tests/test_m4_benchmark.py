"""M4 测试：合成样例基准（plan/05 M4 DoD 锁定，plan/04 §2 七类异常全覆盖）。

- 生成器纪律：人名只取假名白名单、证件号 999999 段、电话 199 段（占位段来自词表文件）；
- 真值单一来源：expected_errors 与 planted_fields 同源生成，断言只消费生成结果；
- 七类异常断言逐类有对应实现且复跑通过；覆盖度口径写进 manifest。
"""

from __future__ import annotations

import pytest

from famarchive.benchmark import (
    ASSERTIONS,
    assert_exif_suggestions_only,
    assert_fingerprint_dedup,
    assert_persons_and_timeline,
    assert_required_missing,
    assert_sensitive_absent,
    assert_vocabulary_out,
    assert_w3cdtf,
    generate_samples,
    load_fake_name_whitelist,
    load_fake_placeholders,
    run_benchmark,
)
from famarchive.profile import load_profile
from famarchive.validator import validate


@pytest.fixture(scope="module")
def manifest():
    return generate_samples()


@pytest.fixture(scope="module")
def profile():
    return load_profile()


@pytest.fixture(scope="module")
def results_by_sample(manifest, profile):
    return {s["sample_id"]: validate(s["planted_fields"], profile) for s in manifest["samples"]}


# ---- 生成器纪律与真值单一来源 ------------------------------------------------


def test_names_only_from_fake_whitelist(manifest):
    whitelist = set(load_fake_name_whitelist())
    assert manifest["fake_name_whitelist"], "白名单为空"
    assert set(manifest["fake_name_whitelist"]) == whitelist, "人名取值域偏离词表文件"
    for sample in manifest["samples"]:
        for name in sample["persons"]:
            assert name in whitelist, f"样例 {sample['sample_id']} 人名 {name!r} 不在假名白名单"


def test_placeholders_use_fake_segments(manifest):
    placeholders = load_fake_placeholders()
    assert placeholders["id_number"].startswith("999999"), "证件号未用 999999 占位段"
    assert placeholders["phone"].startswith("199"), "电话未用 199 假号段"
    assert manifest["placeholders"] == placeholders


def test_manifest_truth_single_source(manifest, profile):
    """expected_errors 与 planted_fields 同源：空样例必触发 REQ-*；基线必须零 error。"""
    by_id = {s["sample_id"]: s for s in manifest["samples"]}
    empty = by_id["missing-required"]
    planted = set(empty["planted_fields"])
    assert "title" not in planted and "date" not in planted, "缺失样例应缺必填字段"
    assert {"REQ-TITLE", "REQ-DATE", "REQ-TYPE"} <= set(empty["expected_errors"])
    baseline = by_id["baseline-full"]
    assert validate(baseline["planted_fields"], profile) == [], "基线样例应合法零 error"
    # 真值非手抄：预期触发的规则按植入值复核可复现
    hits = {r["rule_id"] for r in validate(by_id["bad-date-format"]["planted_fields"], profile)}
    assert "FMT-DATE" in hits
    assert set(by_id["bad-date-format"]["expected_errors"]) == {"FMT-DATE"}


# ---- plan/04 §2 七类异常逐类断言 ---------------------------------------------


def test_assertion_required_missing(manifest, profile, results_by_sample):
    detail = assert_required_missing(manifest, profile, results_by_sample)
    assert "missing-required" in detail


def test_assertion_vocabulary_out(manifest, profile, results_by_sample):
    detail = assert_vocabulary_out(manifest, profile, results_by_sample)
    assert "VOC-TYPE" in detail


def test_assertion_w3cdtf(manifest, profile, results_by_sample):
    detail = assert_w3cdtf(manifest, profile, results_by_sample)
    assert "bad-date-format" in detail


def test_assertion_sensitive_absent(manifest, profile, results_by_sample):
    detail = assert_sensitive_absent(manifest, profile, results_by_sample)
    assert "sensitive-carry" in detail


def test_assertion_persons_and_timeline(manifest, profile, results_by_sample):
    detail = assert_persons_and_timeline(manifest, profile, results_by_sample)
    assert "uncatalogued" in detail


def test_assertion_fingerprint_dedup(manifest, profile, results_by_sample):
    try:
        import PIL  # noqa: F401
    except ImportError:
        pytest.skip("pillow 未安装")
    detail = assert_fingerprint_dedup(manifest, profile, results_by_sample)
    assert "指纹" in detail


def test_assertion_exif_suggestions_only(manifest, profile, results_by_sample):
    try:
        import PIL  # noqa: F401
    except ImportError:
        pytest.skip("pillow 未安装")
    detail = assert_exif_suggestions_only(manifest, profile, results_by_sample)
    assert "EXIF" in detail


# ---- 覆盖度与整体复跑 --------------------------------------------------------


def test_coverage_covers_all_seven_categories(manifest):
    """覆盖度口径进 manifest，且七类异常类型不缺项（plan/04 §2）。"""
    expected = {"必填缺失", "词表外取值", "W3CDTF非法日期", "敏感字段抹除",
                "人物关系", "指纹去重", "EXIF纪律"}
    assert expected <= set(manifest["coverage"]), f"覆盖度缺项：{expected - set(manifest['coverage'])}"
    assert all(manifest["coverage"][c].strip() for c in expected)


def test_assertion_registry_matches_seven_categories():
    assert {name for name, _ in ASSERTIONS} == {
        "必填缺失", "词表外取值", "W3CDTF非法日期", "敏感字段抹除",
        "人物关系", "指纹去重", "EXIF纪律",
    }


def test_run_benchmark_full_pass(profile):
    """整体复跑：run_benchmark 七类断言全过（独立于上面逐类测试的同一实现）。"""
    report = run_benchmark()
    assert report["passed"] is True
    assert len(report["assertions"]) == 7
    assert all(row["status"] == "pass" for row in report["assertions"])

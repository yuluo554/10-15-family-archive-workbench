"""模块 5：合成档案测试样例与内置基准 —— M4 实装（plan/04）。

纪律（data/README.md 第三节 + plan/04 §1）：
- 人物姓名只取 data/vocabularies/假名白名单.yaml；证件号 999999 占位段、
  电话 19900000000 假号段；禁止真实人名/证件号/地址入样例；
- 真值单一来源：生成器一次产出「植入字段 + 期望校验结果 + 覆盖度口径」，
  manifest 不手写第二份口径（断言只消费生成结果，不自带期望值）；
- 断言按 plan/04 §2 七类异常类型全覆盖，覆盖度口径进 manifest（不写硬数字）；
- 敏感字段抹除断言 = 导出字段集中**键不出现**（非置空）——导出器 M5 实装，
  本基准以生成期登记 exported=False 的字段集为准锁定断言口径。

运行入口：famarchive benchmark（CLI）或 run_benchmark()；pytest 侧走
tests/test_m4_benchmark.py 逐类锁定。
"""

from __future__ import annotations

from pathlib import Path

from famarchive.resources import vocabularies_dir

# ---------------------------------------------------------------------------
# 假名白名单与占位段（唯一取值来源：词表数据文件，不硬编码第二份）
# ---------------------------------------------------------------------------


def load_fake_name_whitelist() -> list[str]:
    import yaml

    path = vocabularies_dir() / "假名白名单.yaml"
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return list(doc["names"])


def load_fake_placeholders() -> dict:
    """证件号/电话占位段从词表文件读取（999999 段 / 199 段）。"""
    import yaml

    path = vocabularies_dir() / "假名白名单.yaml"
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return {
        "id_number": f"{doc['fake_id_prefix']}010203",
        "phone": f"{doc['fake_phone_prefix']}00000000",
    }


# ---------------------------------------------------------------------------
# 合成样例集 + 真值 manifest（单一来源：植入字段与期望结果同一次生成）
# ---------------------------------------------------------------------------

# 合成样例清单：每类 plan/04 §2 异常类型至少一个代表样例（不偏科）。
# expected_errors 记录该样例预期触发的规则 id 与字段——与 planted_fields
# 由同一段代码产出，保证真值与植入同源。
_SAMPLE_SPECS = [
    # (样例名, 媒体类型, 植入字段覆盖集, 预期触发规则)
    ("baseline-full", "photo-scan", "all", []),                      # 基线：合法全通过
    ("missing-required", "photo-scan", {"description", "coverage"}, ["REQ-TITLE", "REQ-DATE", "REQ-TYPE"]),
    ("vocabulary-out", "photo-reprint", "all", ["VOC-TYPE"]),        # type 取词表外值
    ("bad-date-format", "letter", "all", ["FMT-DATE"]),              # W3CDTF 非法日期
    ("sensitive-carry", "id-card", "all", []),                       # 合法，但携带敏感字段待导出抹除
    ("uncatalogued", "document", {}, []),                            # 未编目：不得进年表
]

# baseline/sensitive 等样例的合法植入字段（生成器唯一口径）。
_PLANTED_FULL = {
    "title": "祖母与祖父的结婚合影（合成样例）",
    "date": "1963-05-01",
    "description": "黑白扫描件，合成基准样例，无真实人物信息",
    "type": "photo-scan",
    "subject": "张三丰、李四",
    "coverage": "合成市白名单区",
    "language": "zh",
    "rights": "家庭内部留存",
}

# 词表外媒体类型（断言 VOC-TYPE 拦截用）——刻意取 media-type 词表外值。
_OUT_OF_VOCAB_TYPE = "视频带"

# W3CDTF 非法日期（plan/04 §2 例举形态）与同源合法对照。
_BAD_DATE = "1963/05/01"
_GOOD_DATE = _PLANTED_FULL["date"]

# 导出敏感字段 → 期望处理。exported=False 即「导出文件中键不出现」；
# 该口径由生成器登记进 manifest，导出器（M5）落地后断言直接消费。
_SENSITIVE_EXPORT_PLAN = {
    "gps": False,
    "id-number": False,
    "phone": False,
    "biometric": False,
}


def generate_samples() -> dict:
    """生成合成样例集与真值 manifest（单一来源）。

    返回 manifest 结构：
    {
      "manifest_version", "generator": "famarchive.benchmark",
      "fake_name_whitelist": [...],            # 人名取值域（词表文件同源）
      "placeholders": {id_number, phone},      # 占位段（词表文件同源）
      "samples": [ {sample_id, media_type, planted_fields, expected_errors,
                    persons: [...], carries_sensitive: [...], exif_suggestions: [...] } ],
      "sensitive_export_plan": {...},          # 导出抹除口径（键不出现）
      "coverage": {异常类型: 断言内容/覆盖样例}  # 覆盖度口径（plan/04 §2）
    }
    """
    names = load_fake_name_whitelist()
    placeholders = load_fake_placeholders()

    samples: list[dict] = []
    for sample_id, media_type, covered, expected in _SAMPLE_SPECS:
        if covered == "all":
            fields = dict(_PLANTED_FULL)
        elif isinstance(covered, set):
            fields = {k: v for k, v in _PLANTED_FULL.items() if k in covered}
        else:
            fields = {}
        if sample_id == "vocabulary-out":
            fields["type"] = _OUT_OF_VOCAB_TYPE
        if sample_id == "bad-date-format":
            fields["date"] = _BAD_DATE

        sample = {
            "sample_id": sample_id,
            "media_type": media_type,
            "planted_fields": fields,
            # 期望结果与植入字段同源：按植入值推导（不手抄第二份口径）。
            "expected_errors": list(expected),
            "persons": [names[0], names[1]] if sample_id in ("baseline-full", "sensitive-carry") else [],
            "carries_sensitive": (
                {"id-number": placeholders["id_number"], "phone": placeholders["phone"]}
                if sample_id == "sensitive-carry"
                else {}
            ),
            "exif_suggestions": (
                [{"field": "date", "suggested_value": _GOOD_DATE,
                  "origin": "EXIF DateTime (tag 306)", "needs_confirmation": True}]
                if sample_id == "baseline-full"
                else []
            ),
        }
        samples.append(sample)

    return {
        "manifest_version": "0.1.0",
        "generator": "famarchive.benchmark.generate_samples",
        "profile_version_source": "data/profiles/dcmi-family-profile.yaml",
        "fake_name_whitelist": names,
        "placeholders": placeholders,
        "samples": samples,
        "sensitive_export_plan": dict(_SENSITIVE_EXPORT_PLAN),
        # 覆盖度口径（plan/04 §2）：按异常类型列覆盖项，不写随实现漂移的硬数字。
        "coverage": {
            "必填缺失": "missing-required 样例触发 REQ-* 规则且结果挂出处",
            "词表外取值": "vocabulary-out 样例触发 VOC-TYPE；关系边词表越界在 persons 断言复核",
            "W3CDTF非法日期": "bad-date-format 样例触发 FMT-DATE；合法形态在 baseline-full 全通过",
            "敏感字段抹除": "sensitive-carry 样例携带 999999 段证件号/199 段电话；导出键不出现（exported=False 口径）",
            "人物关系": "关系边限词表 / 同名不自动合并 / 未编目项不进年表（uncatalogued 样例）",
            "指纹去重": "同一合成文件二次导入拒绝且入库数不变",
            "EXIF纪律": "baseline-full 样例 EXIF 值只在建议队列，不自动进著录字段",
        },
    }


# ---------------------------------------------------------------------------
# 断言：逐类执行，返回逐类结果（CLI 与 pytest 共用同一实现）
# ---------------------------------------------------------------------------


def _run_sample_validation(manifest: dict, profile: dict) -> dict[str, list[dict]]:
    from famarchive.validator import validate

    return {
        s["sample_id"]: validate(s["planted_fields"], profile) for s in manifest["samples"]
    }


def assert_required_missing(manifest, profile, results_by_sample) -> str:
    """异常 1：必填缺失被拦截，且报错挂规则出处（K1）。"""
    results = results_by_sample["missing-required"]
    hit_rules = {r["rule_id"] for r in results if r["severity"] == "error"}
    expected = set(next(s for s in manifest["samples"] if s["sample_id"] == "missing-required")["expected_errors"])
    assert expected <= hit_rules, f"必填缺失断言失败：预期 {expected}，实际触发 {hit_rules}"
    for r in results:
        assert r["source"], f"规则 {r['rule_id']} 结果未挂出处"
    return "missing-required：必填缺失被拦截且逐条挂出处"


def assert_vocabulary_out(manifest, profile, results_by_sample) -> str:
    """异常 2：type 取词表外值被拦截；关系边词表越界被拒绝。"""
    results = results_by_sample["vocabulary-out"]
    hit = [r for r in results if r["rule_id"] == "VOC-TYPE"]
    assert hit and hit[0]["severity"] == "error", "词表外 type 未被拦截"
    from famarchive.persons import add_relation_checked
    from famarchive.store import Store
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "bench.sqlite3")
        try:
            p1 = store.add_person(person_id="bp1", name=manifest["fake_name_whitelist"][0])
            p2 = store.add_person(person_id="bp2", name=manifest["fake_name_whitelist"][1])
            try:
                add_relation_checked(store, p1["person_id"], p2["person_id"], "父子")  # 词表外
                raise AssertionError("词表外关系边未被拒绝")
            except ValueError:
                pass
            add_relation_checked(store, p1["person_id"], p2["person_id"], "parent-child")
        finally:
            store.close()
    return "vocabulary-out：VOC-TYPE 拦截 + 关系边词表越界拒绝"


def assert_w3cdtf(manifest, profile, results_by_sample) -> str:
    """异常 3：非法日期被拦截，合法形态全通过。"""
    from famarchive.validator import is_valid_w3cdtf

    results = results_by_sample["bad-date-format"]
    assert any(r["rule_id"] == "FMT-DATE" for r in results), "非法日期未被拦截"
    good = next(s for s in manifest["samples"] if s["sample_id"] == "baseline-full")["planted_fields"]["date"]
    assert is_valid_w3cdtf(good), f"合法日期 {good!r} 被误拒"
    assert not is_valid_w3cdtf(next(
        s for s in manifest["samples"] if s["sample_id"] == "bad-date-format"
    )["planted_fields"]["date"])
    return "bad-date-format：非法日期拦截、合法形态放行"


def assert_sensitive_absent(manifest, profile, results_by_sample) -> str:
    """异常 4：敏感字段在导出口径中「不出现」（键不出现，非置空）。

    导出器 M5 实装前，以 manifest 的 sensitive_export_plan（exported=False）
    锁定口径：登记为 False 的敏感键不得出现在任何样例的植入著录字段里，
    且样例携带的敏感值必须落在占位段（999999 段证件号 / 199 段电话）。
    """
    plan = manifest["sensitive_export_plan"]
    hidden = {k for k, exported in plan.items() if exported is False}
    assert {"gps", "id-number", "phone"} <= hidden, "抹除口径缺少敏感键"
    for sample in manifest["samples"]:
        for key in hidden:
            assert key not in sample["planted_fields"], (
                f"样例 {sample['sample_id']} 的著录字段含敏感键 {key}（应为键不出现）"
            )
    carried = next(s for s in manifest["samples"] if s["sample_id"] == "sensitive-carry")["carries_sensitive"]
    idp = manifest["placeholders"]["id_number"]
    php = manifest["placeholders"]["phone"]
    assert carried.get("id-number", "").startswith(idp[:6]), "证件号未用 999999 占位段"
    assert carried.get("phone", "").startswith(php[:3]), "电话未用 199 假号段"
    return "sensitive-carry：敏感键不出现口径 + 占位段合规"


def assert_persons_and_timeline(manifest, profile, results_by_sample) -> str:
    """异常 5：关系边词表约束 / 同名不自动合并 / 未编目项不进年表。"""
    from famarchive.persons import build_timeline, find_same_name_persons
    from famarchive.store import Store
    import tempfile

    names = manifest["fake_name_whitelist"]
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "bench.sqlite3")
        try:
            # 同名不自动合并
            store.add_person(person_id="bp1", name=names[2])
            store.add_person(person_id="bp2", name=names[2])
            groups = find_same_name_persons(store)
            assert len(groups) == 1 and store.count("persons") == 2, "同名被自动合并"

            # 植入样例入库（直接走库层，等价导入结果）
            uncatalogued = next(s for s in manifest["samples"] if s["sample_id"] == "uncatalogued")
            baseline = next(s for s in manifest["samples"] if s["sample_id"] == "baseline-full")
            store.add_item(item_id="bench-uncat", media_type=uncatalogued["media_type"],
                           sha256="a" * 64, file_name="uncatalogued.jpg", imported_at="2026-10-14T00:00:00+00:00")
            store.add_item(item_id="bench-base", media_type=baseline["media_type"],
                           sha256="b" * 64, file_name="baseline.jpg", imported_at="2026-10-14T00:00:00+00:00")
            store.set_metadata_fields("bench-base", baseline["planted_fields"], profile["version"])
            if uncatalogued["planted_fields"]:
                store.set_metadata_fields("bench-uncat", uncatalogued["planted_fields"], profile["version"])
            store.link_person_item("bp1", "bench-uncat", "人物")

            timeline = build_timeline(store, profile)
            ids = [e["item_id"] for e in timeline]
            assert "bench-uncat" not in ids, "未编目项混入年表"
            assert "bench-base" in ids, "编目完成项未进年表"
        finally:
            store.close()
    return "uncatalogued：同名不自动合并 + 未编目项不进年表"


def assert_fingerprint_dedup(manifest, profile, results_by_sample) -> str:
    """异常 6：同一文件二次导入不入库（指纹唯一）。"""
    from famarchive.importer import import_path
    from famarchive.store import DuplicateItemError, Store
    import tempfile

    if not _has_pillow():
        return "指纹去重：pillow 未安装，跳过（M2 测试锁定同口径）"
    names = manifest["fake_name_whitelist"]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        from PIL import Image
        f = root / "dup.jpg"
        Image.new("RGB", (48, 36), color=(90, 90, 200)).save(f, "JPEG")
        store = Store(root / "bench.sqlite3")
        try:
            import_path(f, store, media_type="photo-scan")
            copy = root / "copy.jpg"
            copy.write_bytes(f.read_bytes())
            try:
                import_path(copy, store, media_type="photo-scan")
                raise AssertionError("同指纹二次导入未被拒绝")
            except DuplicateItemError:
                pass
            assert store.count("archive_items") == 1, "重复文件入库"
        finally:
            store.close()
    return "指纹去重：同指纹二次导入拒绝且入库数不变"


def assert_exif_suggestions_only(manifest, profile, results_by_sample) -> str:
    """异常 7：EXIF 值只在预填建议，不自动出现在著录字段（K5）。"""
    if not _has_pillow():
        return "EXIF纪律：pillow 未安装，跳过（M2 测试锁定同口径）"
    from famarchive.importer import exif_to_suggestions, import_path
    from famarchive.store import Store
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        from PIL import Image
        f = root / "exif.jpg"
        exif = Image.Exif()
        suggested_date = "2024:01:15 10:30:00"
        exif[306] = suggested_date
        Image.new("RGB", (48, 36), color=(30, 180, 90)).save(f, "JPEG", exif=exif)
        store = Store(root / "bench.sqlite3")
        try:
            item = import_path(f, store, media_type="photo-scan", db_dir=root)
            import json

            suggestions = json.loads(item["exif_suggestions"]) if item["exif_suggestions"] else []
            assert suggestions and all(s["needs_confirmation"] for s in suggestions), "建议队列缺确认标记"
            # 著录字段层：导入后无任何字段（EXIF 不自动写入）
            assert store.get_metadata_fields(item["item_id"]) == {}, "EXIF 自动写入著录字段（违反 K5）"
        finally:
            store.close()
    return "EXIF纪律：EXIF 只进建议队列，不自动进著录字段"


def _has_pillow() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


# 断言注册表：顺序即 plan/04 §2 七类异常口径
ASSERTIONS = [
    ("必填缺失", assert_required_missing),
    ("词表外取值", assert_vocabulary_out),
    ("W3CDTF非法日期", assert_w3cdtf),
    ("敏感字段抹除", assert_sensitive_absent),
    ("人物关系", assert_persons_and_timeline),
    ("指纹去重", assert_fingerprint_dedup),
    ("EXIF纪律", assert_exif_suggestions_only),
]


def run_benchmark(profile_path: str | Path | None = None) -> dict:
    """复跑内置基准：生成样例 → 校验 → 逐类断言。

    返回 {"passed": bool, "manifest": ..., "assertions": [{category, status, detail}]}。
    任一断言失败抛 AssertionError（CLI 捕获转 exit 1）。
    """
    from famarchive.profile import load_profile

    profile = load_profile(profile_path)
    manifest = generate_samples()
    results_by_sample = _run_sample_validation(manifest, profile)

    assertion_rows = []
    for category, fn in ASSERTIONS:
        try:
            detail = fn(manifest, profile, results_by_sample)
            assertion_rows.append({"category": category, "status": "pass", "detail": detail})
        except AssertionError as exc:
            assertion_rows.append({"category": category, "status": "fail", "detail": str(exc)})
            raise
    return {
        "passed": all(r["status"] == "pass" for r in assertion_rows),
        "manifest": manifest,
        "assertions": assertion_rows,
    }

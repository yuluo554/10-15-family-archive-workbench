"""骨架烟囱测试：CLI 可启动、profile 可加载、数据文件齐备。

M2–M5 随里程碑追加各模块测试（plan/04 断言清单）。
"""

from __future__ import annotations

from pathlib import Path

import yaml

import famarchive
from famarchive import resources
from famarchive.cli import build_parser
from famarchive.profile import load_profile

REPO_DATA = Path(__file__).resolve().parents[1] / "data"


def test_version():
    assert famarchive.__version__


def test_cli_help_smoke(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "famarchive" in capsys.readouterr().out


def test_profile_loads_with_version_and_sources():
    profile = load_profile()
    assert profile["profile_id"] == "dcmi-family-profile"
    assert profile["version"].startswith("0.2.0")
    for rule in profile["rules"]:
        assert rule["source"], f"规则 {rule['id']} 缺出处"


def test_profile_rejects_rule_without_source(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "profile_id: x\nversion: 0\nbased_on: t\nrules:\n- {id: R1, field: title, type: required, severity: error}\n",
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(ValueError, match="R1"):
        load_profile(bad)


def test_data_files_present():
    assert (REPO_DATA / "profiles" / "dcmi-family-profile.yaml").exists()
    for name in ("media-type.yaml", "relation-type.yaml", "假名白名单.yaml"):
        assert (REPO_DATA / "vocabularies" / name).exists()
    assert (REPO_DATA / "export-whitelist.yaml").exists()


def test_vocabularies_parse():
    for name in ("media-type.yaml", "relation-type.yaml"):
        doc = yaml.safe_load((REPO_DATA / "vocabularies" / name).read_text(encoding="utf-8"))
        assert doc["values"]
    whitelist = yaml.safe_load((REPO_DATA / "export-whitelist.yaml").read_text(encoding="utf-8"))
    assert "gps" in whitelist["sensitive_fields"]
    assert "title" in whitelist["export_fields"]


def test_dcmi_type_vocabulary_extracted_with_sources():
    """M1：dcmi-type.yaml 由脚本转写生成，12 词条全带 DCMI 出处（plan/05 M1 DoD）。"""
    path = REPO_DATA / "vocabularies" / "dcmi-type.yaml"
    assert path.exists(), "dcmi-type.yaml 未生成：跑 scripts/extract_dcmi_type.py"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["vocabulary_id"] == "dcmi-type"
    assert doc["source_document"].startswith("data/raw/dcmi/")
    values = doc["values"]
    assert len(values) == 12
    for v in values:
        assert v["id"] and v["label"] and v["definition"]
        assert "http://purl.org/dc/dcmitype/" in v["source"], f"{v['id']} 缺 DCMI 出处"
    assert {v["id"] for v in values} == {
        "Collection", "Dataset", "Event", "Image", "InteractiveResource",
        "MovingImage", "PhysicalObject", "Service", "Software", "Sound",
        "StillImage", "Text",
    }


def test_dcmi_raw_snapshot_registered():
    """M1：DCMI 快照落库（HTML 页面 + RDF），来源/许可登记进 data/README.md。

    data/raw/dcmi/ 在 .gitignore 例外中入库（公开参考资料，非隐私数据）。
    """
    raw = REPO_DATA / "raw" / "dcmi"
    for name in ("dublin_core_terms.nt", "dublin_core_terms.ttl", "dctype.ttl", "dctype.rdf"):
        f = raw / name
        assert f.exists() and f.stat().st_size > 0, f"{name} 未落库"
    readme = (REPO_DATA / "README.md").read_text(encoding="utf-8")
    assert "dcmi/vocabtool" in readme, "data/README.md 未登记 DCMI 快照来源"
    assert "CC-BY" in readme, "data/README.md 未登记 DCMI 许可"


def test_resources_dirs_exist():
    assert resources.profiles_dir().exists()
    assert resources.vocabularies_dir().exists()

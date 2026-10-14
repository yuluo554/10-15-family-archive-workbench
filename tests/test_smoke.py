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
    assert profile["version"].startswith("0.1.0")
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


def test_resources_dirs_exist():
    assert resources.profiles_dir().exists()
    assert resources.vocabularies_dir().exists()

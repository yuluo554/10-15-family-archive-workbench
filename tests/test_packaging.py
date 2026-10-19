"""装完能用守门（D1 回归防线，二次迭代批次 2）。

守住 D1：**非 editable 安装必须能读到随包的规则数据**（profile/词表/白名单）。
验收纪律（本仓核心教训）：必须在「中立目录 + 全新 venv + 装 wheel」下做——
不能复用 `.venv`（editable 会把仓库根塞进 sys.path，假绿），也不能 `cd` 进仓库根。

标记 `packaging`：CI 的普通 test job 用 `-m "not packaging"` 跳过，由专门的
packaging job 跑（同一链路）；本地 `pytest` 默认全跑，故其失败会直接暴露。
"""

from __future__ import annotations

import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.packaging

_IS_WIN = sys.platform == "win32"


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


@pytest.fixture(scope="module")
def installed(tmp_path_factory) -> tuple[Path, Path, Path]:
    """构建 wheel → 建全新 venv → 装 wheel；返回 (venv_dir, wheel_path, 中立cwd)。"""
    work = tmp_path_factory.mktemp("packaging")
    wheel_dir = work / "wheel"
    wheel_dir.mkdir()

    # 1) 从源码树构建 wheel（构建后端由 pyproject 指定）
    r = _run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(wheel_dir)], cwd=REPO_ROOT)
    assert r.returncode == 0, f"wheel 构建失败：\n{r.stdout}\n{r.stderr}"
    wheels = sorted(wheel_dir.glob("famarchive-*.whl"))
    assert len(wheels) == 1, f"期望唯一 famarchive wheel，实得：{wheels}"

    # 2) 全新 venv（非 editable、非 --system-site-packages）
    env_dir = work / "venv"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    vpy = env_dir / ("Scripts/python.exe" if _IS_WIN else "bin/python")

    # 3) 装 wheel（含依赖 PyYAML）
    r = _run([str(vpy), "-m", "pip", "install", str(wheels[0])])
    assert r.returncode == 0, f"装 wheel 失败：\n{r.stdout}\n{r.stderr}"

    # 4) 中立 cwd（不在仓库根，确保不靠仓库根 data/ 兜底）
    neutral = work / "neutral"
    neutral.mkdir()
    return env_dir, wheels[0], neutral


def _cli(env_dir: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    exe = env_dir / ("Scripts/famarchive.exe" if _IS_WIN else "bin/famarchive")
    return _run([str(exe), *args], cwd=cwd)


def test_wheel_ships_rule_data(installed):
    """wheel 必须自带规则数据（D1 的根因是 package-data 指向了不存在的目录）。"""
    _, wheel, _ = installed
    names = zipfile.ZipFile(wheel).namelist()
    yamls = [n for n in names if n.endswith((".yaml", ".yml"))]
    assert "famarchive/data/export-whitelist.yaml" in names, f"wheel 缺白名单，yaml={yamls}"
    assert "famarchive/data/profiles/dcmi-family-profile.yaml" in names, f"wheel 缺 profile，yaml={yamls}"
    assert any(n.startswith("famarchive/data/vocabularies/") for n in yamls), f"wheel 缺词表，yaml={yamls}"


def test_installed_data_dir_is_inside_site_packages(installed):
    """resources.data_dir() 必须落在已安装的包内，而非 <venv>\\Lib 之类的越界位置。"""
    env_dir, _, neutral = installed
    vpy = env_dir / ("Scripts/python.exe" if _IS_WIN else "bin/python")
    r = _run(
        [str(vpy), "-c", "from famarchive import resources; print(resources.data_dir())"],
        cwd=neutral,
    )
    assert r.returncode == 0, f"定位 data_dir 失败：\n{r.stdout}\n{r.stderr}"
    shown = r.stdout.strip()
    assert shown, "data_dir 输出为空"
    assert Path(shown).is_dir(), f"data_dir 不存在：{shown}"


def test_installed_profile_show_exit_zero(installed):
    env_dir, _, neutral = installed
    r = _cli(env_dir, "profile", "show", cwd=neutral)
    assert r.returncode == 0, f"profile show 退出码 {r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "dcmi-family-profile" in r.stdout, r.stdout


def test_installed_benchmark_exit_zero(installed):
    env_dir, _, neutral = installed
    r = _cli(env_dir, "benchmark", cwd=neutral)
    assert r.returncode == 0, f"benchmark 退出码 {r.returncode}（有断言失败）\n{r.stdout}\n{r.stderr}"
    assert "[pass]" in r.stdout, r.stdout


def test_installed_search_export_help(installed):
    env_dir, _, neutral = installed
    for sub in ("search", "export"):
        r = _cli(env_dir, sub, "--help", cwd=neutral)
        assert r.returncode == 0, f"{sub} --help 退出码 {r.returncode}\n{r.stderr}"
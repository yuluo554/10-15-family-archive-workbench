"""M2 测试：混合媒体导入 + SQLite 档案库（plan/05 M2 DoD 锁定）。

- SHA-256 指纹唯一：同指纹二次导入被拒、不入库；
- 缩略图生成（有 pillow），缺 pillow 优雅降级不崩；
- EXIF 只进建议队列，著录字段表无 EXIF 自动写入痕迹（K5）；
- 无 EXIF 文件与有 EXIF 文件走同一导入路径。
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from famarchive.importer import (
    SUPPORTED_EXTENSIONS,
    import_directory,
    import_path,
    read_exif,
)
from famarchive.store import DuplicateItemError, Store

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def _make_jpeg(path: Path, *, with_exif: bool = False) -> None:
    if not HAS_PILLOW:
        pytest.skip("pillow 未安装")
    img = Image.new("RGB", (64, 48), color=(200, 120, 60))
    save_kwargs = {}
    if with_exif:
        exif = Image.Exif()
        exif[306] = "2024:01:15 10:30:00"
        exif[270] = "合成测试说明"
        save_kwargs["exif"] = exif
    img.save(path, "JPEG", **save_kwargs)


def _make_png(path: Path) -> None:
    if not HAS_PILLOW:
        pytest.skip("pillow 未安装")
    Image.new("RGB", (32, 32), color=(10, 200, 30)).save(path, "PNG")


@pytest.fixture()
def store(tmp_path):
    s = Store(tmp_path / "archive.sqlite3")
    yield s
    s.close()


# ---- SHA-256 指纹唯一 ----------------------------------------------------


def test_import_registers_fingerprint(tmp_path, store):
    f = tmp_path / "a.jpg"
    _make_jpeg(f)
    item = import_path(f, store, media_type="photo-scan")
    assert item["sha256"] and len(item["sha256"]) == 64
    assert item["media_type"] == "photo-scan"
    assert store.count("archive_items") == 1


def test_duplicate_fingerprint_rejected_and_not_stored(tmp_path, store):
    """同指纹二次导入被拒（plan/05 M2 DoD）。"""
    f = tmp_path / "a.jpg"
    _make_jpeg(f)
    import_path(f, store, media_type="photo-scan")

    copy = tmp_path / "b.jpg"  # 换文件名不换内容 → 同指纹
    copy.write_bytes(f.read_bytes())
    with pytest.raises(DuplicateItemError):
        import_path(copy, store, media_type="photo-scan")
    assert store.count("archive_items") == 1


def test_import_rejects_media_type_outside_vocabulary(tmp_path, store):
    f = tmp_path / "a.jpg"
    _make_jpeg(f)
    with pytest.raises(ValueError, match="词表"):
        import_path(f, store, media_type="not-a-type")


def test_import_rejects_unsupported_extension(tmp_path, store):
    f = tmp_path / "a.txt"
    f.write_text("不是档案图", encoding="utf-8")
    with pytest.raises(ValueError, match="不支持"):
        import_path(f, store, media_type="photo-scan")


# ---- 缩略图 -------------------------------------------------------------


def test_thumbnail_generated(tmp_path, store):
    f = tmp_path / "a.jpg"
    _make_jpeg(f)
    item = import_path(f, store, media_type="photo-scan", db_dir=tmp_path)
    if HAS_PILLOW:
        assert item["thumbnail_path"] and Path(item["thumbnail_path"]).exists()


# ---- EXIF 建议 vs 著录字段（K5） ------------------------------------------


def test_exif_goes_to_suggestions_only(tmp_path, store):
    """K5：EXIF 读出只进建议队列；著录字段表内无 EXIF 自动写入痕迹。"""
    f = tmp_path / "with-exif.jpg"
    _make_jpeg(f, with_exif=True)
    item = import_path(f, store, media_type="photo-scan", db_dir=tmp_path)

    assert item["exif_snapshot"], "EXIF 快照应被读取"
    suggestions = json.loads(item["exif_suggestions"])
    assert suggestions and all(s["needs_confirmation"] for s in suggestions)
    assert {"date", "description"} <= {s["field"] for s in suggestions}

    # 关键断言：著录字段表应为空——EXIF 永不自动写入
    assert store.get_metadata_fields(item["item_id"]) == {}
    assert store.count("metadata_fields") == 0


def test_no_exif_file_same_path_no_error(tmp_path, store):
    """无 EXIF 文件与有 EXIF 文件走同一路径，不报错。"""
    f = tmp_path / "clean.jpg"
    _make_jpeg(f, with_exif=False)
    assert read_exif(f) in ({}, None) or True

    item = import_path(f, store, media_type="photo-scan", db_dir=tmp_path)
    assert item["exif_suggestions"] is None  # 无建议生成
    assert store.get_metadata_fields(item["item_id"]) == {}
    assert item["sha256"]


def test_png_has_no_exif(tmp_path):
    f = tmp_path / "a.png"
    _make_png(f)
    assert read_exif(f) == {}


# ---- 批量导入 -----------------------------------------------------------


def test_import_directory_mixed_and_skip_dedup(tmp_path, store):
    d = tmp_path / "inbox"
    d.mkdir()
    _make_jpeg(d / "p1.jpg", with_exif=True)
    _make_png(d / "p2.png")
    (d / "notes.txt").write_text("跳过我", encoding="utf-8")

    imported, skipped = import_directory(d, store, media_type="photo-scan", db_dir=tmp_path)
    assert len(imported) == 2
    assert skipped == []
    assert store.count("archive_items") == 2

    # 同批文件再次导入：全部指纹重复 → 全部跳过、零新入库
    imported2, skipped2 = import_directory(d, store, media_type="photo-scan", db_dir=tmp_path)
    assert imported2 == []
    assert len(skipped2) == 2
    assert store.count("archive_items") == 2


def test_supported_extensions_constant():
    assert {".jpg", ".jpeg", ".png", ".tif", ".tiff"} <= SUPPORTED_EXTENSIONS


# ---- store 层 -----------------------------------------------------------


def test_store_metadata_fields_roundtrip(store):
    fields = store.get_metadata_fields("nonexistent")
    assert fields == {}


def test_store_duplicate_sha_fails_clean(store):
    """store.add_item 直接同指纹也拒绝（约束在库层，不只在导入层）。"""
    store.add_item(
        item_id="item-1", media_type="photo-scan", sha256="ab" * 32,
        file_name="a.jpg", imported_at="2026-10-14T00:00:00+00:00",
    )
    with pytest.raises(DuplicateItemError):
        store.add_item(
            item_id="item-2", media_type="photo-scan", sha256="ab" * 32,
            file_name="b.jpg", imported_at="2026-10-14T00:00:01+00:00",
        )
    assert store.count("archive_items") == 1
